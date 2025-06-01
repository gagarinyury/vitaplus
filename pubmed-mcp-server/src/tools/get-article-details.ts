import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { PubMedClient } from '../utils/pubmed-client.js';
import { GetArticleDetailsParams, GetArticleDetailsParamsSchema, PubMedAPIError } from '../types/pubmed.js';

export class GetArticleDetailsTool {
  private pubmedClient: PubMedClient;

  constructor(pubmedClient: PubMedClient) {
    this.pubmedClient = pubmedClient;
  }

  getToolDefinition(): Tool {
    return {
      name: 'get_article_details',
      description: 'Get detailed information for specific PubMed articles using their PMID (PubMed ID). Use this to retrieve full abstracts, author information, MeSH terms, and other metadata for articles found in previous searches.',
      inputSchema: {
        type: 'object',
        properties: {
          pmids: {
            type: 'array',
            description: 'Array of PubMed IDs (PMIDs) to retrieve details for',
            items: {
              type: 'string',
              pattern: '^\\d+$',
              description: 'PubMed ID (numeric string)',
            },
            minItems: 1,
            maxItems: 20,
          },
        },
        required: ['pmids'],
        additionalProperties: false,
      },
    };
  }

  async execute(params: unknown): Promise<{
    articles: Array<{
      pmid: string;
      title: string;
      authors: Array<{
        name: string;
        affiliation?: string;
      }>;
      journal: {
        name: string;
        abbreviation?: string;
      };
      publicationDate: string;
      abstract: {
        fullText: string;
        sections: Array<{
          label?: string;
          text: string;
        }>;
      };
      meshTerms: Array<{
        term: string;
        isMajorTopic: boolean;
      }>;
      publicationTypes: string[];
      doi?: string;
      citationCount?: number;
      keywords: string[];
      references?: string[];
      fundingInfo?: string;
      conflictOfInterest?: string;
    }>;
    summary: {
      totalRequested: number;
      totalRetrieved: number;
      failedPmids: string[];
    };
  }> {
    try {
      // Validate parameters
      const validatedParams = GetArticleDetailsParamsSchema.parse(params);


      // Get article details
      const articles = await this.pubmedClient.getArticleDetails(validatedParams);

      // Enhance articles with additional processing
      const enhancedArticles = articles.map(article => this.enhanceArticleDetails(article));

      // Track which PMIDs were successfully retrieved
      const retrievedPmids = enhancedArticles.map(a => a.pmid);
      const failedPmids = validatedParams.pmids.filter(pmid => !retrievedPmids.includes(pmid));

      const summary = {
        totalRequested: validatedParams.pmids.length,
        totalRetrieved: enhancedArticles.length,
        failedPmids,
      };


      if (failedPmids.length > 0) {
      }

      return {
        articles: enhancedArticles,
        summary,
      };
    } catch (error) {

      if (error instanceof PubMedAPIError) {
        throw new Error(`PubMed API error: ${error.message}`);
      }

      throw new Error(`Failed to retrieve article details: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Enhance article details with additional processing
   */
  private enhanceArticleDetails(article: any) {
    return {
      pmid: article.pmid,
      title: article.title,
      authors: this.processAuthors(article.authors),
      journal: this.processJournal(article.journal),
      publicationDate: article.publicationDate,
      abstract: this.processAbstract(article.abstract),
      meshTerms: this.processMeshTerms(article.meshTerms),
      publicationTypes: article.publicationTypes || [],
      doi: this.extractDoi(article),
      keywords: this.extractKeywords(article),
      // Note: The following fields would require additional API calls to PMC or other services
      // citationCount: await this.getCitationCount(article.pmid),
      // references: await this.getReferences(article.pmid),
      // fundingInfo: this.extractFundingInfo(article),
      // conflictOfInterest: this.extractConflictInfo(article),
    };
  }

  /**
   * Process author information
   */
  private processAuthors(authors: string[]): Array<{ name: string; affiliation?: string }> {
    return authors.map(authorName => ({
      name: authorName,
      // Note: Affiliation data would require additional processing from the raw XML
      // which is not currently captured in our ProcessedArticle type
    }));
  }

  /**
   * Process journal information
   */
  private processJournal(journalName: string): { name: string; abbreviation?: string } {
    return {
      name: journalName,
      // Note: Journal abbreviation would need to be extracted from the XML data
    };
  }

  /**
   * Process abstract into structured format
   */
  private processAbstract(abstractText: string): {
    fullText: string;
    sections: Array<{ label?: string; text: string }>;
  } {
    const sections = [];
    
    // Try to parse structured abstract
    const structuredAbstractPattern = /([A-Z][A-Z\\s]*?):\\s*([^A-Z]*?)(?=[A-Z][A-Z\\s]*?:|$)/g;
    let match;
    let hasStructuredSections = false;

    while ((match = structuredAbstractPattern.exec(abstractText)) !== null) {
      const label = match[1].trim();
      const text = match[2].trim();
      
      if (text.length > 10) { // Filter out very short sections
        sections.push({ label, text });
        hasStructuredSections = true;
      }
    }

    // If no structured sections found, treat as single section
    if (!hasStructuredSections && abstractText.trim()) {
      sections.push({ text: abstractText.trim() });
    }

    return {
      fullText: abstractText,
      sections,
    };
  }

  /**
   * Process MeSH terms with major topic indicators
   */
  private processMeshTerms(meshTerms: string[]): Array<{ term: string; isMajorTopic: boolean }> {
    return meshTerms.map(term => ({
      term,
      // Note: Major topic information would need to be preserved from XML parsing
      isMajorTopic: false, // This would require updating the XML parser
    }));
  }

  /**
   * Extract DOI from article data
   */
  private extractDoi(article: any): string | undefined {
    // Note: DOI extraction would require additional processing from the raw article data
    // This is a placeholder for future enhancement
    return undefined;
  }

  /**
   * Extract keywords from article
   */
  private extractKeywords(article: any): string[] {
    // Extract potential keywords from title and MeSH terms
    const keywords = new Set<string>();
    
    // Add MeSH terms as keywords
    article.meshTerms.forEach((term: string) => {
      keywords.add(term);
    });

    // Extract meaningful words from title (basic implementation)
    const titleWords = article.title
      .toLowerCase()
      .split(/[\\s,;:.()\\[\\]]+/)
      .filter((word: string) => word.length > 3 && !this.isCommonWord(word))
      .slice(0, 10); // Limit to prevent too many keywords

    titleWords.forEach((word: string) => keywords.add(word));

    return Array.from(keywords).slice(0, 20); // Limit total keywords
  }

  /**
   * Check if a word is too common to be a useful keyword
   */
  private isCommonWord(word: string): boolean {
    const commonWords = new Set([
      'study', 'analysis', 'effect', 'effects', 'using', 'method', 'methods',
      'results', 'conclusion', 'conclusions', 'research', 'investigation',
      'evaluation', 'assessment', 'review', 'systematic', 'meta', 'clinical',
      'trial', 'patients', 'treatment', 'therapy', 'case', 'report', 'data',
      'associated', 'related', 'potential', 'possible', 'significant',
      'important', 'novel', 'effective', 'efficacy', 'safety', 'risk'
    ]);

    return commonWords.has(word.toLowerCase());
  }

  /**
   * Get citation count (placeholder for future implementation)
   */
  private async getCitationCount(pmid: string): Promise<number | undefined> {
    // This would require integration with citation services like:
    // - Google Scholar API
    // - Crossref API
    // - OpenCitations API
    return undefined;
  }

  /**
   * Get article references (placeholder for future implementation)
   */
  private async getReferences(pmid: string): Promise<string[] | undefined> {
    // This would require additional API calls to PMC or other services
    return undefined;
  }

  /**
   * Extract funding information (placeholder)
   */
  private extractFundingInfo(article: any): string | undefined {
    // This would require parsing additional fields from the XML data
    return undefined;
  }

  /**
   * Extract conflict of interest information (placeholder)
   */
  private extractConflictInfo(article: any): string | undefined {
    // This would require parsing additional fields from the XML data
    return undefined;
  }
}