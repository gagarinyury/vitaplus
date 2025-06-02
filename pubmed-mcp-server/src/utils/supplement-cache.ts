import { readFile, writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

export interface CachedCypData {
  CYP3A4: { action: string; strength?: string; confidence?: number };
  CYP2C9: { action: string; strength?: string; confidence?: number };
  CYP2C19: { action: string; strength?: string; confidence?: number };
  CYP2D6: { action: string; strength?: string; confidence?: number };
  CYP1A2: { action: string; strength?: string; confidence?: number };
  CYP2B6: { action: string; strength?: string; confidence?: number };
  'P-gp'?: { action: string; strength?: string; confidence?: number };
  references: string[];
  updated: string;
  source: 'pubmed' | 'database' | 'prediction';
}

export interface SupplementCache {
  [supplementName: string]: CachedCypData;
}

export class SupplementCacheManager {
  private cacheDir: string;
  private cacheFile: string;

  constructor(cacheDir?: string) {
    this.cacheDir = cacheDir || join(process.cwd(), 'data', 'cache');
    this.cacheFile = join(this.cacheDir, 'supplement_cyp_cache.json');
  }

  private async ensureCacheDir(): Promise<void> {
    if (!existsSync(this.cacheDir)) {
      await mkdir(this.cacheDir, { recursive: true });
    }
  }

  async loadCache(): Promise<SupplementCache> {
    try {
      await this.ensureCacheDir();
      
      if (!existsSync(this.cacheFile)) {
        return {};
      }

      const data = await readFile(this.cacheFile, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.error('Failed to load supplement cache:', error);
      return {};
    }
  }

  async saveToCache(supplement: string, data: CachedCypData): Promise<void> {
    try {
      await this.ensureCacheDir();
      
      const cache = await this.loadCache();
      cache[supplement.toLowerCase()] = {
        ...data,
        updated: new Date().toISOString()
      };

      await writeFile(this.cacheFile, JSON.stringify(cache, null, 2));
    } catch (error) {
      console.error(`Failed to save ${supplement} to cache:`, error);
    }
  }

  async getCachedData(supplement: string): Promise<CachedCypData | null> {
    const cache = await this.loadCache();
    const data = cache[supplement.toLowerCase()];
    
    if (!data) return null;

    // Проверяем, не устарели ли данные (30 дней)
    const updated = new Date(data.updated);
    const now = new Date();
    const daysDiff = (now.getTime() - updated.getTime()) / (1000 * 60 * 60 * 24);
    
    if (daysDiff > 30) {
      return null; // Данные устарели
    }

    return data;
  }

  async isCached(supplement: string): Promise<boolean> {
    const data = await this.getCachedData(supplement);
    return data !== null;
  }

  async clearCache(): Promise<void> {
    try {
      if (existsSync(this.cacheFile)) {
        await writeFile(this.cacheFile, '{}');
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  async getCacheStats(): Promise<{
    totalEntries: number;
    oldEntries: number;
    newestUpdate: string;
    oldestUpdate: string;
  }> {
    const cache = await this.loadCache();
    const entries = Object.values(cache);
    
    if (entries.length === 0) {
      return {
        totalEntries: 0,
        oldEntries: 0,
        newestUpdate: '',
        oldestUpdate: ''
      };
    }

    const now = new Date();
    let oldEntries = 0;
    let newest = new Date(0);
    let oldest = new Date();

    for (const entry of entries) {
      const updated = new Date(entry.updated);
      const daysDiff = (now.getTime() - updated.getTime()) / (1000 * 60 * 60 * 24);
      
      if (daysDiff > 30) oldEntries++;
      if (updated > newest) newest = updated;
      if (updated < oldest) oldest = updated;
    }

    return {
      totalEntries: entries.length,
      oldEntries,
      newestUpdate: newest.toISOString(),
      oldestUpdate: oldest.toISOString()
    };
  }
}