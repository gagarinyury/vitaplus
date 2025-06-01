import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { PubMedClient } from '../utils/pubmed-client.js';
import { SearchPubMedParams, SearchPubMedParamsSchema, PubMedAPIError } from '../types/pubmed.js';

export class SearchPubMedTool {
  private pubmedClient: PubMedClient;

  constructor(pubmedClient: PubMedClient) {
    this.pubmedClient = pubmedClient;
  }

  getToolDefinition(): Tool {
    return {
      name: 'search_pubmed',
      description: 'Search PubMed for medical and scientific articles. Use this tool to find research papers, clinical studies, and scientific literature on any medical topic, drug, supplement, or health condition.',
      inputSchema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'Search query for PubMed. Can include medical terms, drug names, conditions, etc. Use scientific terminology for best results.',
            minLength: 1,
          },
          maxResults: {
            type: 'number',
            description: 'Maximum number of articles to return (1-100)',
            minimum: 1,
            maximum: 100,
            default: 20,
          },
          dateFrom: {
            type: 'string',
            description: 'Start date for search results in YYYY or YYYY/MM or YYYY/MM/DD format',
            pattern: '^\\d{4}(\\/\\d{2}(\\/\\d{2})?)?$',
          },
          dateTo: {
            type: 'string',
            description: 'End date for search results in YYYY or YYYY/MM or YYYY/MM/DD format',
            pattern: '^\\d{4}(\\/\\d{2}(\\/\\d{2})?)?$',
          },
          studyTypes: {
            type: 'array',
            description: 'Filter by study types',
            items: {
              type: 'string',
              enum: [
                'clinical trial',
                'randomized controlled trial',
                'systematic review',
                'meta analysis',
                'case report',
                'cohort study',
                'cross-sectional study',
                'review'
              ],
            },
          },
        },
        required: ['query'],
        additionalProperties: false,
      },
    };
  }

  async execute(params: unknown): Promise<{
    totalFound: number;
    articles: Array<{
      pmid: string;
      title: string;
      authors: string[];
      journal: string;
      publicationDate: string;
      abstract: string;
      meshTerms: string[];
      publicationTypes: string[];
      relevanceScore?: number;
    }>;
    searchQuery: string;
    searchSummary: string;
  }> {
    try {
      // Validate parameters
      const validatedParams = SearchPubMedParamsSchema.parse(params);


      // Execute search
      const result = await this.pubmedClient.searchPubMed(validatedParams);

      // Calculate relevance scores based on query terms
      const articlesWithScores = result.articles.map(article => ({
        ...article,
        relevanceScore: this.calculateRelevanceScore(article, validatedParams.query),
      }));

      // Sort by relevance score
      articlesWithScores.sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0));

      const searchSummary = this.generateSearchSummary(result, validatedParams);


      return {
        totalFound: result.totalFound,
        articles: articlesWithScores,
        searchQuery: result.searchQuery,
        searchSummary,
      };
    } catch (error) {

      if (error instanceof PubMedAPIError) {
        throw new Error(`PubMed API error: ${error.message}`);
      }

      throw new Error(`Search failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Calculate relevance score for an article based on query terms
   */
  private calculateRelevanceScore(article: any, query: string): number {
    const queryTerms = query.toLowerCase()
      .split(/[\\s,;]+/)
      .filter(term => term.length > 2)
      .map(term => term.replace(/[^a-z0-9]/g, ''));

    if (queryTerms.length === 0) return 0;

    const title = article.title.toLowerCase();
    const abstract = article.abstract.toLowerCase();
    const meshTerms = article.meshTerms.map((term: string) => term.toLowerCase()).join(' ');

    let score = 0;

    queryTerms.forEach(term => {
      // Title matches are worth more
      if (title.includes(term)) {
        score += 10;
      }

      // Abstract matches
      const abstractMatches = (abstract.match(new RegExp(term, 'g')) || []).length;
      score += abstractMatches * 2;

      // MeSH term matches are valuable
      if (meshTerms.includes(term)) {
        score += 5;
      }
    });

    // Boost score for recent articles
    const currentYear = new Date().getFullYear();
    const publicationYear = parseInt(article.publicationDate.substring(0, 4)) || 0;
    const yearDiff = currentYear - publicationYear;
    
    if (yearDiff <= 2) {
      score *= 1.2; // Recent articles get 20% boost
    } else if (yearDiff <= 5) {
      score *= 1.1; // Somewhat recent articles get 10% boost
    }

    // Boost score for systematic reviews and meta-analyses
    const highQualityStudies = ['systematic review', 'meta analysis', 'randomized controlled trial'];
    if (article.publicationTypes.some((type: string) => 
      highQualityStudies.some(hqs => type.toLowerCase().includes(hqs))
    )) {
      score *= 1.3;
    }

    return Math.round(score * 100) / 100; // Round to 2 decimal places
  }

  /**
   * Generate a summary of the search results
   */
  private generateSearchSummary(result: any, params: SearchPubMedParams): string {
    const { totalFound, articles } = result;
    
    if (totalFound === 0) {
      return `No articles found for query: "${params.query}". Try broadening your search terms or checking spelling.`;
    }

    const studyTypes = this.analyzeStudyTypes(articles);
    const yearRange = this.analyzeYearRange(articles);
    const topJournals = this.analyzeTopJournals(articles);

    let summary = `Found ${totalFound} articles for "${params.query}". `;
    summary += `Returning top ${articles.length} most relevant results. `;

    if (studyTypes.length > 0) {
      summary += `Study types include: ${studyTypes.slice(0, 3).join(', ')}. `;
    }

    if (yearRange.min && yearRange.max) {
      summary += `Publications span from ${yearRange.min} to ${yearRange.max}. `;
    }

    if (topJournals.length > 0) {
      summary += `Top journals: ${topJournals.slice(0, 2).join(', ')}.`;
    }

    return summary;
  }

  private analyzeStudyTypes(articles: any[]): string[] {
    const typeCount = new Map<string, number>();
    
    articles.forEach(article => {
      article.publicationTypes.forEach((type: string) => {
        const normalizedType = type.toLowerCase();
        typeCount.set(normalizedType, (typeCount.get(normalizedType) || 0) + 1);
      });
    });

    return Array.from(typeCount.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([type]) => type);
  }

  private analyzeYearRange(articles: any[]): { min?: string; max?: string } {
    const years = articles
      .map(article => article.publicationDate.substring(0, 4))
      .filter(year => year && year.match(/^\\d{4}$/))
      .map(year => parseInt(year))
      .filter(year => year > 1900 && year <= new Date().getFullYear());

    if (years.length === 0) return {};

    return {
      min: Math.min(...years).toString(),
      max: Math.max(...years).toString(),
    };
  }

  private analyzeTopJournals(articles: any[]): string[] {
    const journalCount = new Map<string, number>();
    
    articles.forEach(article => {
      if (article.journal) {
        journalCount.set(article.journal, (journalCount.get(article.journal) || 0) + 1);
      }
    });

    return Array.from(journalCount.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([journal]) => journal);
  }
}