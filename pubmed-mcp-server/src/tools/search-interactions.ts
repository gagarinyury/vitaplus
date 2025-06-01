import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { PubMedClient } from '../utils/pubmed-client.js';
import { SearchInteractionsParams, SearchInteractionsParamsSchema, PubMedAPIError } from '../types/pubmed.js';

export class SearchInteractionsTool {
  private pubmedClient: PubMedClient;

  constructor(pubmedClient: PubMedClient) {
    this.pubmedClient = pubmedClient;
  }

  getToolDefinition(): Tool {
    return {
      name: 'search_interactions',
      description: 'Search for drug-drug, drug-supplement, or supplement-supplement interactions between two substances. This tool specifically looks for interaction studies, contraindications, and safety data.',
      inputSchema: {
        type: 'object',
        properties: {
          substance1: {
            type: 'string',
            description: 'First substance (drug, supplement, vitamin, mineral, herb)',
            minLength: 1,
          },
          substance2: {
            type: 'string',
            description: 'Second substance to check for interactions with the first',
            minLength: 1,
          },
          interactionTypes: {
            type: 'array',
            description: 'Specific types of interactions to search for',
            items: {
              type: 'string',
              enum: [
                'drug-drug',
                'drug-supplement',
                'supplement-supplement',
                'contraindication',
                'adverse_effect',
                'synergistic',
                'antagonistic',
                'pharmacokinetic',
                'pharmacodynamic'
              ],
            },
          },
          includeSupplements: {
            type: 'boolean',
            description: 'Include dietary supplements and vitamins in search',
            default: true,
          },
          includeDrugs: {
            type: 'boolean',
            description: 'Include pharmaceutical drugs in search',
            default: true,
          },
        },
        required: ['substance1', 'substance2'],
        additionalProperties: false,
      },
    };
  }

  async execute(params: unknown): Promise<{
    interactionFound: boolean;
    severity: string;
    interactionType: string;
    evidence: {
      totalStudies: number;
      highQualityStudies: number;
      recentStudies: number;
    };
    recommendations: string[];
    articles: Array<{
      pmid: string;
      title: string;
      authors: string[];
      journal: string;
      publicationDate: string;
      abstract: string;
      meshTerms: string[];
      relevanceScore: number;
      interactionEvidence: {
        mentionsInteraction: boolean;
        severityIndicators: string[];
        mechanismMentioned: boolean;
        clinicalSignificance: string;
      };
    }>;
    searchQuery: string;
    summary: string;
  }> {
    try {
      // Validate parameters
      const validatedParams = SearchInteractionsParamsSchema.parse(params);


      // Execute interaction search
      const result = await this.pubmedClient.searchInteractions(validatedParams);

      // Analyze articles for interaction evidence
      const analyzedArticles = result.articles.map(article => ({
        ...article,
        relevanceScore: this.calculateInteractionRelevance(article, validatedParams.substance1, validatedParams.substance2),
        interactionEvidence: this.analyzeInteractionEvidence(article, validatedParams.substance1, validatedParams.substance2),
      }));

      // Sort by relevance score
      analyzedArticles.sort((a, b) => b.relevanceScore - a.relevanceScore);

      // Determine overall interaction assessment
      const assessment = this.assessOverallInteraction(analyzedArticles, validatedParams);

      // Generate evidence summary
      const evidence = this.analyzeEvidence(analyzedArticles);

      // Generate recommendations
      const recommendations = this.generateRecommendations(assessment, evidence, validatedParams);

      const summary = this.generateInteractionSummary(assessment, evidence, validatedParams);


      return {
        interactionFound: assessment.interactionFound,
        severity: assessment.severity,
        interactionType: assessment.interactionType,
        evidence,
        recommendations,
        articles: analyzedArticles,
        searchQuery: result.searchQuery,
        summary,
      };
    } catch (error) {

      if (error instanceof PubMedAPIError) {
        throw new Error(`PubMed API error: ${error.message}`);
      }

      throw new Error(`Interaction search failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Calculate how relevant an article is for interaction analysis
   */
  private calculateInteractionRelevance(article: any, substance1: string, substance2: string): number {
    const title = article.title.toLowerCase();
    const abstract = article.abstract.toLowerCase();
    const meshTerms = article.meshTerms.map((term: string) => term.toLowerCase()).join(' ');
    
    const sub1Lower = substance1.toLowerCase();
    const sub2Lower = substance2.toLowerCase();
    
    let score = 0;

    // Both substances mentioned in title = highest relevance
    if (title.includes(sub1Lower) && title.includes(sub2Lower)) {
      score += 50;
    } else if (title.includes(sub1Lower) || title.includes(sub2Lower)) {
      score += 20;
    }

    // Interaction keywords in title
    const interactionKeywords = ['interaction', 'contraindication', 'concurrent', 'combination', 'co-administration'];
    interactionKeywords.forEach(keyword => {
      if (title.includes(keyword)) score += 15;
    });

    // Both substances in abstract
    if (abstract.includes(sub1Lower) && abstract.includes(sub2Lower)) {
      score += 30;
    }

    // Interaction evidence in abstract
    const evidenceKeywords = [
      'adverse effect', 'side effect', 'contraindicated', 'avoid concurrent',
      'drug interaction', 'synergistic', 'antagonistic', 'interfere',
      'absorption', 'metabolism', 'clearance', 'bioavailability'
    ];
    evidenceKeywords.forEach(keyword => {
      if (abstract.includes(keyword)) score += 8;
    });

    // MeSH terms for interactions
    const interactionMeshTerms = ['drug interactions', 'contraindications', 'adverse effects'];
    interactionMeshTerms.forEach(term => {
      if (meshTerms.includes(term)) score += 12;
    });

    // Study quality bonus
    const highQualityStudies = ['systematic review', 'meta analysis', 'randomized controlled trial', 'clinical trial'];
    if (article.publicationTypes.some((type: string) => 
      highQualityStudies.some(hqs => type.toLowerCase().includes(hqs.toLowerCase()))
    )) {
      score *= 1.5;
    }

    // Recent publication bonus
    const currentYear = new Date().getFullYear();
    const publicationYear = parseInt(article.publicationDate.substring(0, 4)) || 0;
    const yearDiff = currentYear - publicationYear;
    
    if (yearDiff <= 5) {
      score *= 1.2;
    }

    return Math.round(score * 100) / 100;
  }

  /**
   * Analyze individual article for interaction evidence
   */
  private analyzeInteractionEvidence(article: any, substance1: string, substance2: string): {
    mentionsInteraction: boolean;
    severityIndicators: string[];
    mechanismMentioned: boolean;
    clinicalSignificance: string;
  } {
    const content = `${article.title} ${article.abstract}`.toLowerCase();
    const sub1 = substance1.toLowerCase();
    const sub2 = substance2.toLowerCase();

    // Check if interaction is mentioned
    const interactionKeywords = [
      'interaction', 'contraindication', 'adverse effect', 'side effect',
      'concurrent use', 'combination', 'co-administration', 'interfere'
    ];
    const mentionsInteraction = interactionKeywords.some(keyword => content.includes(keyword)) &&
                               content.includes(sub1) && content.includes(sub2);

    // Identify severity indicators
    const severityIndicators: string[] = [];
    const severityMap = {
      'fatal': 'critical',
      'life-threatening': 'critical',
      'death': 'critical',
      'serious': 'severe',
      'severe': 'severe',
      'contraindicated': 'severe',
      'avoid': 'severe',
      'moderate': 'moderate',
      'significant': 'moderate',
      'mild': 'mild',
      'minor': 'mild',
      'caution': 'mild'
    };

    Object.entries(severityMap).forEach(([keyword, severity]) => {
      if (content.includes(keyword) && !severityIndicators.includes(severity)) {
        severityIndicators.push(severity);
      }
    });

    // Check for mechanism mention
    const mechanismKeywords = [
      'absorption', 'metabolism', 'clearance', 'bioavailability',
      'cytochrome', 'p450', 'transporter', 'enzyme induction',
      'enzyme inhibition', 'pharmacokinetic', 'pharmacodynamic'
    ];
    const mechanismMentioned = mechanismKeywords.some(keyword => content.includes(keyword));

    // Determine clinical significance
    let clinicalSignificance = 'unknown';
    if (content.includes('clinically significant') || content.includes('clinical importance')) {
      clinicalSignificance = 'high';
    } else if (content.includes('clinically relevant') || content.includes('clinical consideration')) {
      clinicalSignificance = 'moderate';
    } else if (content.includes('not clinically significant') || content.includes('minor clinical relevance')) {
      clinicalSignificance = 'low';
    }

    return {
      mentionsInteraction,
      severityIndicators,
      mechanismMentioned,
      clinicalSignificance,
    };
  }

  /**
   * Assess overall interaction based on all articles
   */
  private assessOverallInteraction(articles: any[], params: SearchInteractionsParams): {
    interactionFound: boolean;
    severity: string;
    interactionType: string;
  } {
    const articlesWithInteractions = articles.filter(a => a.interactionEvidence.mentionsInteraction);
    
    if (articlesWithInteractions.length === 0) {
      return {
        interactionFound: false,
        severity: 'none',
        interactionType: 'none',
      };
    }

    // Determine highest severity
    const allSeverities = articlesWithInteractions.flatMap(a => a.interactionEvidence.severityIndicators);
    const severityHierarchy = ['critical', 'severe', 'moderate', 'mild'];
    const severity = severityHierarchy.find(s => allSeverities.includes(s)) || 'mild';

    // Determine interaction type
    const content = articlesWithInteractions.map(a => `${a.title} ${a.abstract}`).join(' ').toLowerCase();
    let interactionType = 'general_interaction';

    if (content.includes('contraindication') || content.includes('contraindicated')) {
      interactionType = 'contraindication';
    } else if (content.includes('adverse') || content.includes('toxicity')) {
      interactionType = 'adverse_effect';
    } else if (content.includes('synergistic') || content.includes('enhanced') || content.includes('potentiate')) {
      interactionType = 'synergistic';
    } else if (content.includes('antagonistic') || content.includes('inhibit') || content.includes('reduce')) {
      interactionType = 'antagonistic';
    } else if (content.includes('absorption') || content.includes('bioavailability')) {
      interactionType = 'pharmacokinetic';
    }

    return {
      interactionFound: true,
      severity,
      interactionType,
    };
  }

  /**
   * Analyze evidence quality and quantity
   */
  private analyzeEvidence(articles: any[]): {
    totalStudies: number;
    highQualityStudies: number;
    recentStudies: number;
  } {
    const currentYear = new Date().getFullYear();
    const highQualityTypes = ['systematic review', 'meta analysis', 'randomized controlled trial'];
    
    const highQualityStudies = articles.filter(article =>
      article.publicationTypes.some((type: string) =>
        highQualityTypes.some(hqt => type.toLowerCase().includes(hqt.toLowerCase()))
      )
    ).length;

    const recentStudies = articles.filter(article => {
      const year = parseInt(article.publicationDate.substring(0, 4)) || 0;
      return (currentYear - year) <= 5;
    }).length;

    return {
      totalStudies: articles.length,
      highQualityStudies,
      recentStudies,
    };
  }

  /**
   * Generate recommendations based on interaction assessment
   */
  private generateRecommendations(assessment: any, evidence: any, params: SearchInteractionsParams): string[] {
    const recommendations = [];

    if (!assessment.interactionFound) {
      recommendations.push(`No significant interactions found between ${params.substance1} and ${params.substance2} in current literature.`);
      recommendations.push('This does not guarantee safety - consult healthcare provider before combining substances.');
      return recommendations;
    }

    switch (assessment.severity) {
      case 'critical':
        recommendations.push(`CRITICAL: Avoid concurrent use of ${params.substance1} and ${params.substance2}.`);
        recommendations.push('Seek immediate medical attention if already taking both substances.');
        recommendations.push('Alternative treatments should be considered.');
        break;

      case 'severe':
        recommendations.push(`SEVERE interaction detected between ${params.substance1} and ${params.substance2}.`);
        recommendations.push('Concurrent use is generally contraindicated.');
        recommendations.push('If combination is necessary, close medical supervision is required.');
        break;

      case 'moderate':
        recommendations.push(`MODERATE interaction possible between ${params.substance1} and ${params.substance2}.`);
        recommendations.push('Use with caution and monitor for adverse effects.');
        recommendations.push('Consider dose adjustment or timing separation.');
        break;

      case 'mild':
        recommendations.push(`MILD interaction potential between ${params.substance1} and ${params.substance2}.`);
        recommendations.push('Generally safe with proper monitoring.');
        recommendations.push('Consider separating administration times if possible.');
        break;
    }

    // Add evidence-based recommendations
    if (evidence.highQualityStudies > 0) {
      recommendations.push(`Evidence quality: ${evidence.highQualityStudies} high-quality studies support these findings.`);
    } else {
      recommendations.push('Limited high-quality evidence available - recommendations based on case reports and lower-quality studies.');
    }

    recommendations.push('Always consult with a healthcare provider before making changes to medication or supplement regimens.');

    return recommendations;
  }

  /**
   * Generate interaction summary
   */
  private generateInteractionSummary(assessment: any, evidence: any, params: SearchInteractionsParams): string {
    if (!assessment.interactionFound) {
      return `No documented interactions found between ${params.substance1} and ${params.substance2} based on ${evidence.totalStudies} studies reviewed. However, absence of documented interactions does not guarantee safety.`;
    }

    return `${assessment.severity.toUpperCase()} ${assessment.interactionType.replace('_', ' ')} detected between ${params.substance1} and ${params.substance2}. Evidence based on ${evidence.totalStudies} studies (${evidence.highQualityStudies} high-quality, ${evidence.recentStudies} recent). Clinical significance requires healthcare provider evaluation.`;
  }
}