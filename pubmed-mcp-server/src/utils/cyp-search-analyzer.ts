import { PubMedClient } from './pubmed-client.js';
import { ProcessedArticle } from '../types/pubmed.js';
import { CachedCypData, SupplementCacheManager } from './supplement-cache.js';

export interface CypSearchResult {
  articles: ProcessedArticle[];
  supplement: string;
  searchQueries: string[];
  totalFound: number;
}

export interface ParsedCypEffects {
  cypProfile: CachedCypData;
  confidence: number;
  evidenceLevel: 'high' | 'moderate' | 'low' | 'minimal';
}

export class CypSearchAnalyzer {
  private pubmedClient: PubMedClient;
  private cacheManager: SupplementCacheManager;

  constructor(pubmedClient: PubMedClient, cacheManager?: SupplementCacheManager) {
    this.pubmedClient = pubmedClient;
    this.cacheManager = cacheManager || new SupplementCacheManager();
  }

  async searchCypMechanisms(supplement: string): Promise<CypSearchResult> {
    // Стратегия многоэтапного поиска
    const searchQueries = [
      `"${supplement}" AND (CYP450 OR "cytochrome P450") AND (inhibition OR induction)`,
      `"${supplement}" AND "P-glycoprotein" AND "drug interaction"`,
      `"${supplement}" AND pharmacokinetics AND "drug interaction" AND human`,
      `"${supplement}" AND metabolism AND "enzyme" AND (CYP OR cytochrome)`,
      `"${supplement}" AND "herb-drug interaction" AND "clinical significance"`
    ];

    let allArticles: ProcessedArticle[] = [];
    let totalFound = 0;

    for (const query of searchQueries) {
      try {
        const result = await this.pubmedClient.searchPubMed({
          query,
          maxResults: 5,
          dateFrom: '2015', // Фокус на более свежих данных
          studyTypes: ['systematic review', 'meta analysis', 'clinical trial']
        });

        if (result.articles && result.articles.length > 0) {
          allArticles.push(...result.articles);
          totalFound += result.totalFound;
        }

        // Небольшая задержка между запросами
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (error) {
        console.error(`Search failed for query: ${query}`, error);
        continue;
      }
    }

    // Удаляем дубликаты по PMID
    const uniqueArticles = allArticles.filter((article, index, array) =>
      array.findIndex(a => a.pmid === article.pmid) === index
    );

    return {
      articles: uniqueArticles,
      supplement,
      searchQueries,
      totalFound
    };
  }

  parseCypEffects(searchResults: CypSearchResult): ParsedCypEffects {
    const cypProfile: CachedCypData = {
      CYP3A4: { action: 'unknown' },
      CYP2C9: { action: 'unknown' },
      CYP2C19: { action: 'unknown' },
      CYP2D6: { action: 'unknown' },
      CYP1A2: { action: 'unknown' },
      CYP2B6: { action: 'unknown' },
      'P-gp': { action: 'unknown' },
      references: [],
      updated: new Date().toISOString(),
      source: 'pubmed'
    };

    // Ключевые слова для анализа
    const inhibitionKeywords = [
      'inhibit', 'inhibition', 'inhibitory', 'IC50', 'Ki', 'decrease activity',
      'competitive inhibition', 'non-competitive inhibition', 'mechanism-based inhibition'
    ];

    const inductionKeywords = [
      'induc', 'induction', 'upregulat', 'increase expression', 'increase activity',
      'mRNA expression', 'protein expression', 'enzymatic activity'
    ];

    const strengthKeywords = {
      strong: ['strong', 'potent', 'significant', 'marked', 'substantial'],
      moderate: ['moderate', 'modest', 'partial'],
      weak: ['weak', 'slight', 'minor', 'mild']
    };

    let totalEvidence = 0;
    let cypMentions = 0;

    for (const article of searchResults.articles) {
      const abstract = article.abstract.toLowerCase();
      const title = article.title.toLowerCase();
      const content = `${title} ${abstract}`;

      // Добавляем PMID в ссылки
      if (article.pmid && !cypProfile.references.includes(article.pmid)) {
        cypProfile.references.push(article.pmid);
      }

      // Анализируем каждый CYP фермент
      const cypEnzymes = ['CYP3A4', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP1A2', 'CYP2B6'];
      
      for (const cyp of cypEnzymes) {
        const cypVariations = [
          cyp.toLowerCase(),
          cyp.replace('CYP', 'cyp'),
          cyp.replace('CYP', 'CYP '),
          cyp.replace('CYP', 'cytochrome P450 ')
        ];

        const cypMentioned = cypVariations.some(variation => content.includes(variation));
        
        if (cypMentioned) {
          cypMentions++;
          totalEvidence++;

          // Определяем тип воздействия
          const hasInhibition = inhibitionKeywords.some(kw => content.includes(kw));
          const hasInduction = inductionKeywords.some(kw => content.includes(kw));

          if (hasInhibition && !hasInduction) {
            cypProfile[cyp].action = 'inhibitor';
          } else if (hasInduction && !hasInhibition) {
            cypProfile[cyp].action = 'inducer';
          } else if (hasInhibition && hasInduction) {
            // Смешанные эффекты - определяем по контексту
            cypProfile[cyp].action = 'mixed';
          }

          // Определяем силу воздействия
          if (cypProfile[cyp].action !== 'unknown') {
            for (const [strength, keywords] of Object.entries(strengthKeywords)) {
              if (keywords.some(kw => content.includes(kw))) {
                cypProfile[cyp].strength = strength;
                break;
              }
            }
          }

          // Простая оценка уверенности на основе качества источника
          let confidence = 0.5;
          if (article.publicationTypes.includes('Meta-Analysis')) {
            confidence = 0.9;
          } else if (article.publicationTypes.includes('Systematic Review')) {
            confidence = 0.8;
          } else if (article.publicationTypes.includes('Randomized Controlled Trial')) {
            confidence = 0.7;
          } else if (article.publicationTypes.includes('Clinical Trial')) {
            confidence = 0.6;
          }

          cypProfile[cyp].confidence = Math.max(cypProfile[cyp].confidence || 0, confidence);
        }
      }

      // Анализ P-гликопротеина
      const pgpKeywords = ['p-glycoprotein', 'p-gp', 'pgp', 'mdr1', 'abcb1'];
      const pgpMentioned = pgpKeywords.some(kw => content.includes(kw));
      
      if (pgpMentioned) {
        cypMentions++;
        totalEvidence++;

        const hasInhibition = inhibitionKeywords.some(kw => content.includes(kw));
        const hasInduction = inductionKeywords.some(kw => content.includes(kw));

        if (hasInhibition && !hasInduction) {
          cypProfile['P-gp']!.action = 'inhibitor';
        } else if (hasInduction && !hasInhibition) {
          cypProfile['P-gp']!.action = 'inducer';
        }
      }
    }

    // Определяем общий уровень доказательств
    let evidenceLevel: 'high' | 'moderate' | 'low' | 'minimal';
    const averageConfidence = cypMentions > 0 ? totalEvidence / cypMentions : 0;
    
    if (searchResults.articles.length >= 5 && cypMentions >= 3 && averageConfidence > 0.7) {
      evidenceLevel = 'high';
    } else if (searchResults.articles.length >= 3 && cypMentions >= 2 && averageConfidence > 0.5) {
      evidenceLevel = 'moderate';
    } else if (searchResults.articles.length >= 1 && cypMentions >= 1) {
      evidenceLevel = 'low';
    } else {
      evidenceLevel = 'minimal';
    }

    return {
      cypProfile,
      confidence: averageConfidence,
      evidenceLevel
    };
  }

  async getOrSearchCypData(supplement: string): Promise<ParsedCypEffects> {
    // Сначала проверяем кэш
    const cachedData = await this.cacheManager.getCachedData(supplement);
    
    if (cachedData) {
      return {
        cypProfile: cachedData,
        confidence: this.calculateCacheConfidence(cachedData),
        evidenceLevel: this.determineEvidenceLevel(cachedData)
      };
    }

    // Если нет в кэше, выполняем поиск
    const searchResults = await this.searchCypMechanisms(supplement);
    const parsedEffects = this.parseCypEffects(searchResults);

    // Сохраняем в кэш
    await this.cacheManager.saveToCache(supplement, parsedEffects.cypProfile);

    return parsedEffects;
  }

  private calculateCacheConfidence(data: CachedCypData): number {
    const confidences = Object.values(data)
      .filter(item => typeof item === 'object' && item !== null && 'confidence' in item)
      .map(item => (item as any).confidence)
      .filter(conf => typeof conf === 'number');

    if (confidences.length === 0) return 0.5;
    return confidences.reduce((sum, conf) => sum + conf, 0) / confidences.length;
  }

  private determineEvidenceLevel(data: CachedCypData): 'high' | 'moderate' | 'low' | 'minimal' {
    const referencesCount = data.references.length;
    const knownActions = Object.values(data)
      .filter(item => typeof item === 'object' && item !== null && 'action' in item)
      .filter(item => (item as any).action !== 'unknown').length;

    if (referencesCount >= 5 && knownActions >= 3) return 'high';
    if (referencesCount >= 3 && knownActions >= 2) return 'moderate';
    if (referencesCount >= 1 && knownActions >= 1) return 'low';
    return 'minimal';
  }
}