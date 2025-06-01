import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { PubMedClient } from '../utils/pubmed-client.js';
import { SearchSafetyParams, SearchSafetyParamsSchema, PubMedAPIError } from '../types/pubmed.js';

export class SearchSafetyTool {
  private pubmedClient: PubMedClient;

  constructor(pubmedClient: PubMedClient) {
    this.pubmedClient = pubmedClient;
  }

  getToolDefinition(): Tool {
    return {
      name: 'search_safety',
      description: 'Search for safety information, adverse effects, contraindications, and toxicity data for a specific substance (drug, supplement, vitamin, etc.). Useful for understanding potential risks and safety considerations.',
      inputSchema: {
        type: 'object',
        properties: {
          substance: {
            type: 'string',
            description: 'The substance to search safety information for (drug, supplement, vitamin, mineral, herb)',
            minLength: 1,
          },
          population: {
            type: 'string',
            description: 'Specific population to focus safety search on',
            enum: ['general', 'pregnancy', 'pediatric', 'elderly'],
            default: 'general',
          },
          studyTypes: {
            type: 'array',
            description: 'Types of studies to focus on for safety data',
            items: {
              type: 'string',
              enum: [
                'systematic review',
                'meta analysis',
                'clinical trial',
                'randomized controlled trial',
                'case report',
                'cohort study',
                'case-control study'
              ],
            },
          },
        },
        required: ['substance'],
        additionalProperties: false,
      },
    };
  }

  async execute(params: unknown): Promise<{
    substance: string;
    population: string;
    safetyProfile: {
      overallSafety: 'safe' | 'caution' | 'unsafe' | 'unknown';
      riskLevel: 'low' | 'moderate' | 'high' | 'unknown';
      evidenceQuality: 'high' | 'moderate' | 'low';
    };
    adverseEffects: Array<{
      effect: string;
      frequency: 'rare' | 'uncommon' | 'common' | 'very_common' | 'unknown';
      severity: 'mild' | 'moderate' | 'severe' | 'life_threatening';
      description: string;
      sources: string[];
    }>;
    contraindications: Array<{
      condition: string;
      severity: 'absolute' | 'relative';
      description: string;
      sources: string[];
    }>;
    dosageSafety: {
      therapeuticRange?: string;
      maximumSafeDose?: string;
      toxicDose?: string;
      recommendations: string[];
    };
    populationSpecific: {
      pregnancy?: {
        category?: string;
        recommendations: string[];
        risks: string[];
      };
      pediatric?: {
        ageRestrictions: string[];
        dosageAdjustments: string[];
        risks: string[];
      };
      elderly?: {
        considerations: string[];
        dosageAdjustments: string[];
        risks: string[];
      };
    };
    monitoring: {
      required: boolean;
      parameters: string[];
      frequency: string;
      recommendations: string[];
    };
    articles: Array<{
      pmid: string;
      title: string;
      authors: string[];
      journal: string;
      publicationDate: string;
      abstract: string;
      safetyRelevance: {
        type: 'adverse_effect' | 'contraindication' | 'toxicity' | 'dosage' | 'general_safety';
        severity: 'mild' | 'moderate' | 'severe';
        populationRelevant: boolean;
      };
      relevanceScore: number;
    }>;
    summary: string;
    recommendations: string[];
  }> {
    try {
      // Validate parameters
      const validatedParams = SearchSafetyParamsSchema.parse(params);


      // Execute safety search
      const result = await this.pubmedClient.searchSafety(validatedParams);

      // Analyze articles for safety information
      const analyzedArticles = result.articles.map(article => ({
        ...article,
        safetyRelevance: this.analyzeSafetyRelevance(article, validatedParams),
        relevanceScore: this.calculateSafetyRelevance(article, validatedParams.substance),
      }));

      // Sort by relevance
      analyzedArticles.sort((a, b) => b.relevanceScore - a.relevanceScore);

      // Extract safety information
      const safetyProfile = this.assessSafetyProfile(analyzedArticles, validatedParams);
      const adverseEffects = this.extractAdverseEffects(analyzedArticles);
      const contraindications = this.extractContraindications(analyzedArticles);
      const dosageSafety = this.extractDosageSafety(analyzedArticles);
      const populationSpecific = this.extractPopulationSpecific(analyzedArticles, validatedParams.population);
      const monitoring = this.extractMonitoringRequirements(analyzedArticles);

      // Generate recommendations
      const recommendations = this.generateSafetyRecommendations(safetyProfile, validatedParams);
      const summary = this.generateSafetySummary(safetyProfile, analyzedArticles.length, validatedParams);


      return {
        substance: validatedParams.substance,
        population: validatedParams.population,
        safetyProfile,
        adverseEffects,
        contraindications,
        dosageSafety,
        populationSpecific,
        monitoring,
        articles: analyzedArticles,
        summary,
        recommendations,
      };
    } catch (error) {

      if (error instanceof PubMedAPIError) {
        throw new Error(`PubMed API error: ${error.message}`);
      }

      throw new Error(`Safety search failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Calculate relevance score for safety information
   */
  private calculateSafetyRelevance(article: any, substance: string): number {
    const title = article.title.toLowerCase();
    const abstract = article.abstract.toLowerCase();
    const substanceLower = substance.toLowerCase();

    let score = 0;

    // Substance mentioned in title
    if (title.includes(substanceLower)) score += 20;

    // Safety keywords in title
    const safetyKeywords = ['safety', 'adverse', 'toxicity', 'side effect', 'contraindication'];
    safetyKeywords.forEach(keyword => {
      if (title.includes(keyword)) score += 15;
    });

    // Safety content in abstract
    const safetyContent = [
      'adverse effect', 'side effect', 'toxicity', 'poisoning', 'overdose',
      'contraindication', 'warning', 'precaution', 'safety', 'risk'
    ];
    safetyContent.forEach(keyword => {
      const matches = (abstract.match(new RegExp(keyword, 'g')) || []).length;
      score += matches * 5;
    });

    // Study quality bonus
    const highQualityTypes = ['systematic review', 'meta analysis', 'clinical trial'];
    if (article.publicationTypes.some((type: string) =>
      highQualityTypes.some(hqt => type.toLowerCase().includes(hqt.toLowerCase()))
    )) {
      score *= 1.4;
    }

    return Math.round(score * 100) / 100;
  }

  /**
   * Analyze safety relevance of an article
   */
  private analyzeSafetyRelevance(article: any, params: SearchSafetyParams): {
    type: 'adverse_effect' | 'contraindication' | 'toxicity' | 'dosage' | 'general_safety';
    severity: 'mild' | 'moderate' | 'severe';
    populationRelevant: boolean;
  } {
    const content = `${article.title} ${article.abstract}`.toLowerCase();

    // Determine safety information type
    let type: 'adverse_effect' | 'contraindication' | 'toxicity' | 'dosage' | 'general_safety' = 'general_safety';
    
    if (content.includes('contraindication') || content.includes('contraindicated')) {
      type = 'contraindication';
    } else if (content.includes('toxicity') || content.includes('toxic') || content.includes('poisoning')) {
      type = 'toxicity';
    } else if (content.includes('adverse effect') || content.includes('side effect')) {
      type = 'adverse_effect';
    } else if (content.includes('dose') || content.includes('dosage') || content.includes('overdose')) {
      type = 'dosage';
    }

    // Determine severity
    let severity: 'mild' | 'moderate' | 'severe' = 'mild';
    if (content.includes('fatal') || content.includes('death') || content.includes('life-threatening')) {
      severity = 'severe';
    } else if (content.includes('serious') || content.includes('severe') || content.includes('hospitalization')) {
      severity = 'severe';
    } else if (content.includes('moderate') || content.includes('significant')) {
      severity = 'moderate';
    }

    // Check population relevance
    const populationKeywords = {
      pregnancy: ['pregnancy', 'pregnant', 'prenatal', 'gestational', 'fetal'],
      pediatric: ['pediatric', 'children', 'child', 'infant', 'adolescent'],
      elderly: ['elderly', 'geriatric', 'aged', 'older adult'],
      general: []
    };

    const relevantKeywords = populationKeywords[params.population as keyof typeof populationKeywords] || [];
    const populationRelevant = params.population === 'general' || 
                              relevantKeywords.some(keyword => content.includes(keyword));

    return { type, severity, populationRelevant };
  }

  /**
   * Assess overall safety profile
   */
  private assessSafetyProfile(articles: any[], params: SearchSafetyParams): {
    overallSafety: 'safe' | 'caution' | 'unsafe' | 'unknown';
    riskLevel: 'low' | 'moderate' | 'high' | 'unknown';
    evidenceQuality: 'high' | 'moderate' | 'low';
  } {
    if (articles.length === 0) {
      return {
        overallSafety: 'unknown',
        riskLevel: 'unknown',
        evidenceQuality: 'low',
      };
    }

    const severeArticles = articles.filter(a => a.safetyRelevance.severity === 'severe');
    const moderateArticles = articles.filter(a => a.safetyRelevance.severity === 'moderate');

    // Assess overall safety
    let overallSafety: 'safe' | 'caution' | 'unsafe' | 'unknown' = 'safe';
    let riskLevel: 'low' | 'moderate' | 'high' | 'unknown' = 'low';

    if (severeArticles.length > 2) {
      overallSafety = 'unsafe';
      riskLevel = 'high';
    } else if (severeArticles.length > 0 || moderateArticles.length > 3) {
      overallSafety = 'caution';
      riskLevel = 'moderate';
    }

    // Assess evidence quality
    const highQualityStudies = articles.filter(a =>
      a.publicationTypes.some((type: string) =>
        ['systematic review', 'meta analysis', 'randomized controlled trial'].some(hqt =>
          type.toLowerCase().includes(hqt.toLowerCase())
        )
      )
    );

    let evidenceQuality: 'high' | 'moderate' | 'low' = 'low';
    if (highQualityStudies.length >= 3) {
      evidenceQuality = 'high';
    } else if (highQualityStudies.length >= 1 || articles.length >= 5) {
      evidenceQuality = 'moderate';
    }

    return { overallSafety, riskLevel, evidenceQuality };
  }

  /**
   * Extract adverse effects information
   */
  private extractAdverseEffects(articles: any[]): Array<{
    effect: string;
    frequency: 'rare' | 'uncommon' | 'common' | 'very_common' | 'unknown';
    severity: 'mild' | 'moderate' | 'severe' | 'life_threatening';
    description: string;
    sources: string[];
  }> {
    const effects = new Map<string, any>();

    articles.forEach(article => {
      const content = `${article.title} ${article.abstract}`.toLowerCase();
      
      // Common adverse effects patterns
      const effectPatterns = [
        /nausea/g, /vomiting/g, /diarrhea/g, /headache/g, /dizziness/g,
        /fatigue/g, /rash/g, /itching/g, /allergic reaction/g,
        /liver toxicity/g, /hepatotoxicity/g, /kidney damage/g,
        /cardiac arrhythmia/g, /hypertension/g, /hypotension/g
      ];

      effectPatterns.forEach(pattern => {
        const matches = content.match(pattern);
        if (matches) {
          const effect = matches[0];
          if (!effects.has(effect)) {
            effects.set(effect, {
              effect,
              frequency: this.determineFrequency(content, effect),
              severity: this.determineSeverity(content, effect),
              description: this.extractEffectDescription(article, effect),
              sources: [article.pmid],
            });
          } else {
            const existing = effects.get(effect);
            if (!existing.sources.includes(article.pmid)) {
              existing.sources.push(article.pmid);
            }
          }
        }
      });
    });

    return Array.from(effects.values()).slice(0, 10); // Limit to top 10
  }

  /**
   * Extract contraindications
   */
  private extractContraindications(articles: any[]): Array<{
    condition: string;
    severity: 'absolute' | 'relative';
    description: string;
    sources: string[];
  }> {
    const contraindications: any[] = [];
    
    articles.forEach(article => {
      const content = `${article.title} ${article.abstract}`.toLowerCase();
      
      if (content.includes('contraindicated') || content.includes('contraindication')) {
        // Extract conditions
        const conditions = this.extractContraindicatedConditions(content);
        
        conditions.forEach(condition => {
          const severity = content.includes('absolute') ? 'absolute' : 'relative';
          
          contraindications.push({
            condition,
            severity,
            description: this.extractContraindicationDescription(article, condition),
            sources: [article.pmid],
          });
        });
      }
    });

    return contraindications.slice(0, 5); // Limit results
  }

  /**
   * Extract dosage safety information
   */
  private extractDosageSafety(articles: any[]): {
    therapeuticRange?: string;
    maximumSafeDose?: string;
    toxicDose?: string;
    recommendations: string[];
  } {
    const recommendations: string[] = [];
    let therapeuticRange: string | undefined;
    let maximumSafeDose: string | undefined;
    let toxicDose: string | undefined;

    articles.forEach(article => {
      const content = `${article.title} ${article.abstract}`;
      
      // Extract dosage information (simplified)
      if (content.toLowerCase().includes('therapeutic range') || content.toLowerCase().includes('therapeutic dose')) {
        recommendations.push('Therapeutic dosing information available - see source articles');
      }
      
      if (content.toLowerCase().includes('maximum') && content.toLowerCase().includes('dose')) {
        recommendations.push('Maximum dose limitations identified - see source articles');
      }
      
      if (content.toLowerCase().includes('toxic') && content.toLowerCase().includes('dose')) {
        recommendations.push('Toxic dose levels documented - see source articles');
      }
    });

    if (recommendations.length === 0) {
      recommendations.push('Specific dosage safety information not found in available literature');
    }

    return { therapeuticRange, maximumSafeDose, toxicDose, recommendations };
  }

  /**
   * Extract population-specific information
   */
  private extractPopulationSpecific(articles: any[], population: string): any {
    const populationData: any = {};

    if (population === 'pregnancy' || population === 'general') {
      const pregnancyArticles = articles.filter(a => 
        a.abstract.toLowerCase().includes('pregnancy') || 
        a.title.toLowerCase().includes('pregnancy')
      );
      
      if (pregnancyArticles.length > 0) {
        populationData.pregnancy = {
          recommendations: ['Consult healthcare provider before use during pregnancy'],
          risks: this.extractPregnancyRisks(pregnancyArticles),
        };
      }
    }

    // Similar logic for pediatric and elderly populations...

    return populationData;
  }

  /**
   * Extract monitoring requirements
   */
  private extractMonitoringRequirements(articles: any[]): {
    required: boolean;
    parameters: string[];
    frequency: string;
    recommendations: string[];
  } {
    const monitoringKeywords = ['monitor', 'monitoring', 'surveillance', 'follow-up'];
    const hasMonitoring = articles.some(article =>
      monitoringKeywords.some(keyword =>
        article.abstract.toLowerCase().includes(keyword)
      )
    );

    return {
      required: hasMonitoring,
      parameters: hasMonitoring ? ['Clinical symptoms', 'Laboratory values'] : [],
      frequency: hasMonitoring ? 'As clinically indicated' : 'Not specified',
      recommendations: hasMonitoring ? 
        ['Regular monitoring recommended - see source articles for details'] :
        ['No specific monitoring requirements identified'],
    };
  }

  // Helper methods (simplified implementations)
  private determineFrequency(content: string, effect: string): 'rare' | 'uncommon' | 'common' | 'very_common' | 'unknown' {
    if (content.includes('common')) return 'common';
    if (content.includes('rare')) return 'rare';
    if (content.includes('frequent')) return 'common';
    return 'unknown';
  }

  private determineSeverity(content: string, effect: string): 'mild' | 'moderate' | 'severe' | 'life_threatening' {
    if (content.includes('life-threatening') || content.includes('fatal')) return 'life_threatening';
    if (content.includes('severe')) return 'severe';
    if (content.includes('moderate')) return 'moderate';
    return 'mild';
  }

  private extractEffectDescription(article: any, effect: string): string {
    // Simplified - would need more sophisticated text extraction
    return `${effect} reported in: ${article.title}`;
  }

  private extractContraindicatedConditions(content: string): string[] {
    // Simplified extraction
    const conditions = [];
    if (content.includes('liver disease')) conditions.push('liver disease');
    if (content.includes('kidney disease')) conditions.push('kidney disease');
    if (content.includes('heart disease')) conditions.push('heart disease');
    return conditions;
  }

  private extractContraindicationDescription(article: any, condition: string): string {
    return `Contraindicated in ${condition} - see: ${article.title}`;
  }

  private extractPregnancyRisks(articles: any[]): string[] {
    const risks: string[] = [];
    articles.forEach(article => {
      const content = article.abstract.toLowerCase();
      if (content.includes('teratogenic')) risks.push('Potential teratogenic effects');
      if (content.includes('fetal')) risks.push('Fetal risks reported');
    });
    return risks;
  }

  private generateSafetyRecommendations(safetyProfile: any, params: SearchSafetyParams): string[] {
    const recommendations = [];

    switch (safetyProfile.overallSafety) {
      case 'unsafe':
        recommendations.push(`AVOID ${params.substance} - significant safety concerns identified`);
        recommendations.push('Consult healthcare provider immediately if currently using');
        break;
      case 'caution':
        recommendations.push(`Use ${params.substance} with CAUTION`);
        recommendations.push('Close medical supervision recommended');
        break;
      case 'safe':
        recommendations.push(`${params.substance} appears generally safe when used appropriately`);
        recommendations.push('Follow recommended dosing guidelines');
        break;
      default:
        recommendations.push(`Safety profile for ${params.substance} requires further evaluation`);
        recommendations.push('Consult healthcare provider before use');
    }

    recommendations.push('Always inform healthcare providers of all substances being used');
    return recommendations;
  }

  private generateSafetySummary(safetyProfile: any, articleCount: number, params: SearchSafetyParams): string {
    return `Safety assessment for ${params.substance} based on ${articleCount} studies. Overall safety: ${safetyProfile.overallSafety.toUpperCase()}, Risk level: ${safetyProfile.riskLevel.toUpperCase()}, Evidence quality: ${safetyProfile.evidenceQuality.toUpperCase()}. Population focus: ${params.population}.`;
  }
}