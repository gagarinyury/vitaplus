import { RateLimiterMemory } from 'rate-limiter-flexible';
import { RateLimitError } from '../types/pubmed.js';

export class PubMedRateLimiter {
  private rateLimiter: RateLimiterMemory;
  private readonly maxRetries = 3;
  private readonly baseDelay = 1000; // 1 second

  constructor(requestsPerMinute: number = 180) {
    // PubMed allows 3 requests per second = 180 per minute
    this.rateLimiter = new RateLimiterMemory({
      keyPrefix: 'pubmed_api',
      points: requestsPerMinute,
      duration: 60, // Per 60 seconds
      blockDuration: 60, // Block for 60 seconds if limit exceeded
    });
  }

  async throttle(key: string = 'default'): Promise<void> {
    try {
      await this.rateLimiter.consume(key);
    } catch (rateLimiterRes) {
      if (rateLimiterRes instanceof Error) {
        throw new RateLimitError(`Rate limiting error: ${rateLimiterRes.message}`);
      }
      
      // If rate limited, throw error with retry info
      const secs = Math.round(rateLimiterRes.msBeforeNext / 1000) || 1;
      throw new RateLimitError(
        `Rate limit exceeded. Try again in ${secs} seconds.`,
        secs * 1000
      );
    }
  }

  async executeWithRetry<T>(
    operation: () => Promise<T>,
    key: string = 'default'
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        await this.throttle(key);
        return await operation();
      } catch (error) {
        lastError = error as Error;

        if (error instanceof RateLimitError) {
          if (attempt === this.maxRetries) {
            throw error;
          }

          // Wait before retry with exponential backoff
          const delay = this.baseDelay * Math.pow(2, attempt - 1) + Math.random() * 1000;
          await this.sleep(delay);
          continue;
        }

        // For non-rate-limit errors, throw immediately
        throw error;
      }
    }

    throw lastError!;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Get current rate limit status
  async getStatus(key: string = 'default'): Promise<{
    totalHits: number;
    totalHitsPerDuration: number;
    remainingPoints: number;
    msBeforeNext: number;
  }> {
    const status = await this.rateLimiter.get(key);
    
    return {
      totalHits: (status as any)?.totalHits || 0,
      totalHitsPerDuration: this.rateLimiter.points,
      remainingPoints: status?.remainingPoints || this.rateLimiter.points,
      msBeforeNext: status?.msBeforeNext || 0,
    };
  }
}