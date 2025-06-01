import fetch from 'node-fetch';
import { PubMedRateLimiter } from './rate-limiter.js';
import { PubMedXMLParser } from './xml-parser.js';
import { PubMedQueryBuilder } from './query-builder.js';
import { 
  ProcessedArticle, 
  PubMedAPIError, 
  PubMedSearchResult,
  InteractionSearchResult,
  SearchPubMedParams,
  GetArticleDetailsParams,
  SearchInteractionsParams,
  SearchSafetyParams,
  PubMedSearchResultSchema
} from '../types/pubmed.js';

export class PubMedClient {
  private baseUrl: string;
  private apiKey?: string;
  private rateLimiter: PubMedRateLimiter;
  private xmlParser: PubMedXMLParser;
  private timeout: number;

  constructor(
    baseUrl: string = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/',
    apiKey?: string,
    requestsPerMinute: number = 180,
    timeout: number = 30000
  ) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
    this.apiKey = apiKey;
    this.rateLimiter = new PubMedRateLimiter(requestsPerMinute);
    this.xmlParser = new PubMedXMLParser();
    this.timeout = timeout;
  }

  /**
   * Search PubMed with a custom query
   */
  async searchPubMed(params: SearchPubMedParams): Promise<{
    totalFound: number;
    articles: ProcessedArticle[];
    searchQuery: string;
  }> {
    const query = PubMedQueryBuilder.buildGeneralQuery(params.query, {
      dateFrom: params.dateFrom,
      dateTo: params.dateTo,
      studyTypes: params.studyTypes,
      maxResults: params.maxResults,
    });

    return this.rateLimiter.executeWithRetry(async () => {
      // Step 1: Search for article IDs
      const searchResult = await this.performSearch(query, params.maxResults);
      
      if (!searchResult.esearchresult.idlist.length) {
        return {
          totalFound: 0,
          articles: [],
          searchQuery: query,
        };
      }

      // Step 2: Fetch article details
      const articles = await this.fetchArticleDetails(searchResult.esearchresult.idlist);

      return {
        totalFound: parseInt(searchResult.esearchresult.count),
        articles,
        searchQuery: query,
      };
    });
  }

  /**
   * Get detailed information for specific articles by PMID
   */
  async getArticleDetails(params: GetArticleDetailsParams): Promise<ProcessedArticle[]> {
    return this.rateLimiter.executeWithRetry(async () => {
      return this.fetchArticleDetails(params.pmids);
    });
  }

  /**
   * Search for interactions between two substances
   */
  async searchInteractions(params: SearchInteractionsParams): Promise<InteractionSearchResult> {
    const query = PubMedQueryBuilder.buildInteractionQuery(
      params.substance1,
      params.substance2,
      {
        includeSupplements: params.includeSupplements,
        includeDrugs: params.includeDrugs,
      }
    );

    return this.rateLimiter.executeWithRetry(async () => {
      // Search for interaction articles
      const searchResult = await this.performSearch(query, 50); // Get more results for interactions

      if (!searchResult.esearchresult.idlist.length) {
        return {
          found: false,
          totalResults: 0,
          articles: [],
          searchQuery: query,
        };
      }

      // Fetch article details
      const articles = await this.fetchArticleDetails(searchResult.esearchresult.idlist);

      // Analyze articles for interaction information
      const { interactionType, severity } = this.analyzeInteractionArticles(articles, params.substance1, params.substance2);

      return {
        found: true,
        totalResults: parseInt(searchResult.esearchresult.count),
        articles,
        searchQuery: query,
        interactionType,
        severity,
      };
    });
  }

  /**
   * Search for safety information about a substance
   */
  async searchSafety(params: SearchSafetyParams): Promise<{
    totalFound: number;
    articles: ProcessedArticle[];
    searchQuery: string;
  }> {
    const query = PubMedQueryBuilder.buildSafetyQuery(
      params.substance,
      params.population,
      params.studyTypes
    );

    return this.rateLimiter.executeWithRetry(async () => {
      const searchResult = await this.performSearch(query, 30);
      
      if (!searchResult.esearchresult.idlist.length) {
        return {
          totalFound: 0,
          articles: [],
          searchQuery: query,
        };
      }

      const articles = await this.fetchArticleDetails(searchResult.esearchresult.idlist);

      return {
        totalFound: parseInt(searchResult.esearchresult.count),
        articles,
        searchQuery: query,
      };
    });
  }

  /**
   * Search for dosage information about a substance
   */
  async searchDosage(substance: string): Promise<{
    totalFound: number;
    articles: ProcessedArticle[];
    searchQuery: string;
  }> {
    const query = PubMedQueryBuilder.buildDosageQuery(substance);

    return this.rateLimiter.executeWithRetry(async () => {
      const searchResult = await this.performSearch(query, 20);
      
      if (!searchResult.esearchresult.idlist.length) {
        return {
          totalFound: 0,
          articles: [],
          searchQuery: query,
        };
      }

      const articles = await this.fetchArticleDetails(searchResult.esearchresult.idlist);

      return {
        totalFound: parseInt(searchResult.esearchresult.count),
        articles,
        searchQuery: query,
      };
    });
  }

  /**
   * Perform the actual search request to PubMed
   */
  private async performSearch(query: string, maxResults: number = 20): Promise<PubMedSearchResult> {
    const searchUrl = new URL('esearch.fcgi', this.baseUrl);
    
    const params = new URLSearchParams({
      db: 'pubmed',
      term: query,
      retmode: 'json',
      retmax: maxResults.toString(),
      sort: 'relevance',
    });

    if (this.apiKey) {
      params.append('api_key', this.apiKey);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${searchUrl}?${params}`, {
        signal: controller.signal,
        headers: {
          'User-Agent': 'VitaPlus-MCP-Server/1.0 (https://github.com/vitaplus/pubmed-mcp-server)',
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new PubMedAPIError(
          `PubMed search failed: ${response.statusText}`,
          response.status
        );
      }

      const data = await response.json();
      
      // Validate the response structure
      const validatedData = PubMedSearchResultSchema.parse(data);
      
      return validatedData;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new PubMedAPIError('Request timeout');
      }
      
      if (error instanceof PubMedAPIError) {
        throw error;
      }
      
      throw new PubMedAPIError(`Search request failed: ${error.message}`);
    }
  }

  /**
   * Fetch detailed article information
   */
  private async fetchArticleDetails(pmids: string[]): Promise<ProcessedArticle[]> {
    if (pmids.length === 0) {
      return [];
    }
    const fetchUrl = new URL('efetch.fcgi', this.baseUrl);
    
    const params = new URLSearchParams({
      db: 'pubmed',
      id: pmids.join(','),
      retmode: 'xml',
      rettype: 'abstract',
    });

    if (this.apiKey) {
      params.append('api_key', this.apiKey);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${fetchUrl}?${params}`, {
        signal: controller.signal,
        headers: {
          'User-Agent': 'VitaPlus-MCP-Server/1.0 (https://github.com/vitaplus/pubmed-mcp-server)',
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new PubMedAPIError(
          `PubMed fetch failed: ${response.statusText}`,
          response.status
        );
      }

      const xmlData = await response.text();
      const parsedArticles = await this.xmlParser.parseArticlesXML(xmlData);
      
      return parsedArticles;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new PubMedAPIError('Request timeout');
      }
      
      if (error instanceof PubMedAPIError) {
        throw error;
      }
      
      throw new PubMedAPIError(`Fetch request failed: ${error.message}`);
    }
  }

  /**
   * Analyze articles to determine interaction type and severity
   */
  private analyzeInteractionArticles(
    articles: ProcessedArticle[],
    substance1: string,
    substance2: string
  ): { interactionType?: string; severity?: string } {
    let interactionType: string | undefined;
    let severity: string | undefined;

    for (const article of articles) {
      const title = article.title.toLowerCase();
      const abstract = article.abstract.toLowerCase();
      const content = `${title} ${abstract}`;

      // Determine interaction type
      if (content.includes('contraindication') || content.includes('contraindicated')) {
        interactionType = 'contraindication';
        severity = 'severe';
        break;
      } else if (content.includes('adverse') || content.includes('toxicity')) {
        interactionType = 'adverse_effect';
        if (!severity) severity = 'moderate';
      } else if (content.includes('interaction') || content.includes('interfere')) {
        interactionType = 'interaction';
        if (!severity) severity = 'mild';
      } else if (content.includes('synergistic') || content.includes('enhanced')) {
        interactionType = 'synergistic';
        if (!severity) severity = 'mild';
      }

      // Determine severity from content
      if (content.includes('fatal') || content.includes('death') || content.includes('life-threatening')) {
        severity = 'critical';
      } else if (content.includes('serious') || content.includes('severe')) {
        severity = 'severe';
      } else if (content.includes('moderate') || content.includes('significant')) {
        severity = 'moderate';
      }
    }

    return { interactionType, severity };
  }

  /**
   * Get rate limiter status
   */
  async getRateLimitStatus() {
    return this.rateLimiter.getStatus();
  }
}