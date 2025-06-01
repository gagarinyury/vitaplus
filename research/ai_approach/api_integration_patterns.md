# Паттерны интеграции с внешними API

## 1. Gateway Pattern - Единая точка входа

```typescript
interface InteractionAPI {
  pubmed: PubMedService;
  fda: FDAService;
  cache: CacheService;
  ai: AIAnalysisService;
}

class InteractionGateway {
  async checkInteraction(sub1: string, sub2: string): Promise<InteractionResult> {
    // 1. Проверяем кэш
    const cached = await this.cache.get(`${sub1}:${sub2}`);
    if (cached && !this.isExpired(cached)) return cached;
    
    // 2. Параллельные запросы к источникам
    const [pubmedData, fdaData] = await Promise.allSettled([
      this.pubmed.search(sub1, sub2),
      this.fda.searchAdverseEvents(sub1, sub2)
    ]);
    
    // 3. AI анализ собранных данных
    const analysis = await this.ai.analyze({
      pubmed: pubmedData.status === 'fulfilled' ? pubmedData.value : null,
      fda: fdaData.status === 'fulfilled' ? fdaData.value : null
    });
    
    // 4. Сохраняем в кэш
    await this.cache.set(`${sub1}:${sub2}`, analysis, TTL_24_HOURS);
    
    return analysis;
  }
}
```

## 2. Circuit Breaker Pattern - Защита от недоступности API

```typescript
class APICircuitBreaker {
  private failures = new Map<string, number>();
  private lastFailure = new Map<string, number>();
  
  async callWithBreaker<T>(
    apiName: string, 
    apiCall: () => Promise<T>, 
    fallback: () => Promise<T>
  ): Promise<T> {
    
    if (this.isCircuitOpen(apiName)) {
      console.log(`Circuit breaker OPEN for ${apiName}, using fallback`);
      return await fallback();
    }
    
    try {
      const result = await apiCall();
      this.onSuccess(apiName);
      return result;
    } catch (error) {
      this.onFailure(apiName);
      
      if (this.shouldOpenCircuit(apiName)) {
        console.log(`Opening circuit breaker for ${apiName}`);
      }
      
      return await fallback();
    }
  }
  
  private isCircuitOpen(apiName: string): boolean {
    const failures = this.failures.get(apiName) || 0;
    const lastFail = this.lastFailure.get(apiName) || 0;
    
    return failures >= 5 && (Date.now() - lastFail) < 60000; // 1 минута
  }
}
```

## 3. Retry Pattern с Exponential Backoff

```typescript
class APIRetryService {
  async retryWithBackoff<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        if (attempt === maxRetries) throw error;
        
        const delay = baseDelay * Math.pow(2, attempt - 1) + Math.random() * 1000;
        await this.sleep(delay);
        
        console.log(`Retry ${attempt}/${maxRetries} after ${delay}ms`);
      }
    }
    
    throw new Error('Max retries exceeded');
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## 4. Rate Limiting Pattern

```typescript
class RateLimiter {
  private requests = new Map<string, number[]>();
  
  async throttle(apiName: string, limit: number, windowMs: number): Promise<void> {
    const now = Date.now();
    const requests = this.requests.get(apiName) || [];
    
    // Очищаем старые запросы
    const validRequests = requests.filter(time => now - time < windowMs);
    
    if (validRequests.length >= limit) {
      const oldestRequest = Math.min(...validRequests);
      const waitTime = windowMs - (now - oldestRequest);
      
      console.log(`Rate limit hit for ${apiName}, waiting ${waitTime}ms`);
      await this.sleep(waitTime);
    }
    
    validRequests.push(now);
    this.requests.set(apiName, validRequests);
  }
}
```

## 5. PubMed API Integration Service

```typescript
class PubMedService {
  private baseUrl = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
  private rateLimiter = new RateLimiter();
  
  async searchInteractions(substance1: string, substance2: string): Promise<PubMedResult> {
    await this.rateLimiter.throttle('pubmed', 3, 1000); // 3 req/sec
    
    // Этап 1: Поиск статей
    const searchQuery = this.buildSearchQuery(substance1, substance2);
    const searchUrl = `${this.baseUrl}esearch.fcgi?db=pubmed&term=${encodeURIComponent(searchQuery)}&retmode=json&retmax=20`;
    
    const searchResponse = await fetch(searchUrl);
    const searchData = await searchResponse.json();
    
    if (!searchData.esearchresult?.idlist?.length) {
      return { found: false, articles: [] };
    }
    
    // Этап 2: Получение деталей статей
    await this.rateLimiter.throttle('pubmed', 3, 1000);
    
    const pmids = searchData.esearchresult.idlist.join(',');
    const fetchUrl = `${this.baseUrl}efetch.fcgi?db=pubmed&id=${pmids}&retmode=xml&rettype=abstract`;
    
    const fetchResponse = await fetch(fetchUrl);
    const articlesXml = await fetchResponse.text();
    
    return {
      found: true,
      articles: this.parseArticlesXML(articlesXml),
      searchQuery,
      totalFound: searchData.esearchresult.count
    };
  }
  
  private buildSearchQuery(sub1: string, sub2: string): string {
    const interactions = ['interaction', 'contraindication', 'adverse effect'];
    const timeLimit = '2019:2024[pdat]'; // Последние 5 лет
    
    return `(${sub1}[mesh] OR "${sub1}"[tiab]) AND (${sub2}[mesh] OR "${sub2}"[tiab]) AND (${interactions.join(' OR ')}) AND ${timeLimit}`;
  }
}
```

## 6. FDA API Integration Service

```typescript
class FDAService {
  private baseUrl = 'https://api.fda.gov/';
  
  async searchAdverseEvents(substance1: string, substance2: string): Promise<FDAResult> {
    const searchTerms = [
      `product.substance_name:"${substance1}"`,
      `product.substance_name:"${substance2}"`
    ].join(' AND ');
    
    const url = `${this.baseUrl}food/event.json?search=${encodeURIComponent(searchTerms)}&limit=50`;
    
    try {
      const response = await fetch(url);
      const data = await response.json();
      
      return {
        found: data.results?.length > 0,
        events: data.results || [],
        totalCount: data.meta?.results?.total || 0
      };
    } catch (error) {
      console.error('FDA API error:', error);
      return { found: false, events: [], totalCount: 0 };
    }
  }
}
```

## 7. AI Analysis Service Integration

```typescript
class AIAnalysisService {
  private anthropicClient: Anthropic;
  
  async analyzeInteraction(data: {
    pubmed?: PubMedResult;
    fda?: FDAResult;
    substances: [string, string];
  }): Promise<StructuredInteractionResult> {
    
    const prompt = this.buildAnalysisPrompt(data);
    
    const response = await this.anthropicClient.messages.create({
      model: 'claude-3-sonnet-20240229',
      max_tokens: 1024,
      system: INTERACTION_EXPERT_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: prompt }],
      tools: [
        {
          name: 'structure_interaction_result',
          description: 'Structure the interaction analysis result',
          input_schema: {
            type: 'object',
            properties: {
              interaction_found: { type: 'boolean' },
              severity: { 
                type: 'string', 
                enum: ['none', 'mild', 'moderate', 'severe', 'critical'] 
              },
              mechanism: { type: 'string' },
              evidence_level: { 
                type: 'string', 
                enum: ['low', 'moderate', 'high'] 
              },
              recommendations: { type: 'string' },
              sources: { 
                type: 'array', 
                items: { type: 'string' } 
              }
            },
            required: ['interaction_found', 'severity', 'evidence_level']
          }
        }
      ]
    });
    
    return this.parseAIResponse(response);
  }
}
```

## 8. Caching Strategy Implementation

```typescript
class InteractionCacheService {
  private memoryCache = new Map<string, CachedResult>();
  private persistentCache: LRUCache<string, CachedResult>;
  
  constructor() {
    this.persistentCache = new LRUCache({
      max: 10000, // Максимум 10k записей
      ttl: 24 * 60 * 60 * 1000 // 24 часа
    });
  }
  
  async get(key: string): Promise<CachedResult | null> {
    // Сначала проверяем память
    if (this.memoryCache.has(key)) {
      const result = this.memoryCache.get(key)!;
      if (!this.isExpired(result)) return result;
      this.memoryCache.delete(key);
    }
    
    // Затем persistent cache
    const persistent = this.persistentCache.get(key);
    if (persistent && !this.isExpired(persistent)) {
      // Кэшируем в памяти для быстрого доступа
      this.memoryCache.set(key, persistent);
      return persistent;
    }
    
    return null;
  }
  
  async set(key: string, result: any, ttl: number): Promise<void> {
    const cached: CachedResult = {
      data: result,
      timestamp: Date.now(),
      ttl
    };
    
    this.memoryCache.set(key, cached);
    this.persistentCache.set(key, cached);
  }
  
  generateKey(substance1: string, substance2: string): string {
    // Нормализуем порядок для консистентности
    const [a, b] = [substance1, substance2].sort();
    return `interaction:${a}:${b}`;
  }
}
```

## 9. Error Handling и Logging

```typescript
class InteractionServiceError extends Error {
  constructor(
    message: string,
    public code: string,
    public apiSource?: string,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'InteractionServiceError';
  }
}

class ErrorHandler {
  static handle(error: any, context: string): InteractionServiceError {
    if (error instanceof InteractionServiceError) {
      return error;
    }
    
    // API specific errors
    if (error.response?.status === 429) {
      return new InteractionServiceError(
        'Rate limit exceeded',
        'RATE_LIMIT_EXCEEDED',
        context,
        error
      );
    }
    
    if (error.response?.status >= 500) {
      return new InteractionServiceError(
        'External API unavailable',
        'API_UNAVAILABLE',
        context,
        error
      );
    }
    
    return new InteractionServiceError(
      'Unknown error occurred',
      'UNKNOWN_ERROR',
      context,
      error
    );
  }
}
```

## 10. Monitoring и Metrics

```typescript
class APIMetrics {
  private metrics = {
    requests: new Map<string, number>(),
    errors: new Map<string, number>(),
    latency: new Map<string, number[]>(),
    cacheHits: 0,
    cacheMisses: 0
  };
  
  recordRequest(apiName: string, latency: number, success: boolean): void {
    // Счётчик запросов
    const current = this.metrics.requests.get(apiName) || 0;
    this.metrics.requests.set(apiName, current + 1);
    
    // Ошибки
    if (!success) {
      const errors = this.metrics.errors.get(apiName) || 0;
      this.metrics.errors.set(apiName, errors + 1);
    }
    
    // Латентность
    const latencies = this.metrics.latency.get(apiName) || [];
    latencies.push(latency);
    if (latencies.length > 100) latencies.shift(); // Keep last 100
    this.metrics.latency.set(apiName, latencies);
  }
  
  getMetrics(): object {
    return {
      apis: Object.fromEntries(this.metrics.requests),
      errors: Object.fromEntries(this.metrics.errors),
      avgLatency: this.calculateAverageLatencies(),
      cacheHitRate: this.calculateCacheHitRate()
    };
  }
}