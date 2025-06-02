import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { PubMedClient } from '../utils/pubmed-client.js';
import { SupplementCacheManager, CachedCypData } from '../utils/supplement-cache.js';
import { CypSearchAnalyzer } from '../utils/cyp-search-analyzer.js';
import { InteractionAnalyzer } from '../utils/interaction-analyzer.js';
import { SupplementSafetyChecker } from '../utils/supplement-safety-checker.js';
import { CypPredictor } from '../utils/cyp-predictor.js';

const AnalyzeSupplementsCompleteParamsSchema = z.object({
  supplements: z.array(z.string()).min(1, "At least one supplement is required").max(8, "Maximum 8 supplements allowed"),
  medications: z.array(z.string()).optional().default([]),
  include_timing: z.boolean().optional().default(true),
  include_pubmed_search: z.boolean().optional().default(true),
  detailed_analysis: z.boolean().optional().default(false),
  force_refresh: z.boolean().optional().default(false)
});

export type AnalyzeSupplementsCompleteParams = z.infer<typeof AnalyzeSupplementsCompleteParamsSchema>;

export class AnalyzeSupplementsCompleteTool {
  private pubmedClient: PubMedClient;
  private cacheManager: SupplementCacheManager;
  private cypSearchAnalyzer: CypSearchAnalyzer;
  private interactionAnalyzer: InteractionAnalyzer;
  private safetyChecker: SupplementSafetyChecker;
  private cypPredictor: CypPredictor;

  constructor(pubmedClient: PubMedClient) {
    this.pubmedClient = pubmedClient;
    this.cacheManager = new SupplementCacheManager();
    this.cypSearchAnalyzer = new CypSearchAnalyzer(pubmedClient, this.cacheManager);
    this.interactionAnalyzer = new InteractionAnalyzer();
    this.safetyChecker = new SupplementSafetyChecker();
    this.cypPredictor = new CypPredictor();
  }

  getToolDefinition(): Tool {
    return {
      name: 'analyze_supplements_complete',
      description: 'Комплексный анализ добавок: автоматически собирает данные из PubMed, анализирует CYP450 взаимодействия, предсказывает риски и оптимизирует время приема. Объединяет все возможности системы в одном инструменте. Идеально для полного анализа схемы приема добавок.',
      inputSchema: {
        type: 'object',
        properties: {
          supplements: {
            type: 'array',
            description: 'Список добавок для комплексного анализа (на английском или русском). Максимум 8 добавок',
            items: {
              type: 'string'
            },
            minItems: 1,
            maxItems: 8
          },
          medications: {
            type: 'array',
            description: 'Опциональный список принимаемых лекарственных препаратов для анализа взаимодействий',
            items: {
              type: 'string'
            },
            default: []
          },
          include_timing: {
            type: 'boolean',
            description: 'Включить оптимизацию времени приема добавок',
            default: true
          },
          include_pubmed_search: {
            type: 'boolean',
            description: 'Выполнить поиск в PubMed для добавок не найденных в базе данных',
            default: true
          },
          detailed_analysis: {
            type: 'boolean',
            description: 'Подробный анализ с объяснением методологии и дополнительными данными',
            default: false
          },
          force_refresh: {
            type: 'boolean',
            description: 'Принудительно обновить данные из PubMed (игнорировать кэш)',
            default: false
          }
        },
        required: ['supplements'],
        additionalProperties: false
      }
    };
  }

  async execute(params: unknown): Promise<{
    analysis_summary: {
      supplements_analyzed: number;
      data_sources: string[];
      safety_score: string;
      total_interactions: number;
      analysis_method: string;
    };
    supplements_data: {
      [supplement: string]: {
        cyp_profile: any;
        data_source: string;
        confidence: number;
        last_updated: string;
        references?: string[];
      };
    };
    interactions: {
      supplement_interactions: any[];
      medication_interactions: any[];
      interaction_summary: string;
    };
    timing_recommendations?: {
      morning: any[];
      afternoon: any[];
      evening: any[];
      spacing_notes: string[];
      optimal_schedule: string;
    };
    safety_assessment: {
      overall_safety: string;
      risk_factors: string[];
      contraindications: string[];
      monitoring_recommendations: string[];
    };
    actionable_recommendations: string[];
    references: {
      pubmed_articles: number;
      database_entries: number;
      total_sources: number;
    };
    methodology?: {
      data_collection: string;
      analysis_approach: string;
      limitation: string;
    };
  }> {
    try {
      const validatedParams = AnalyzeSupplementsCompleteParamsSchema.parse(params);

      // 1. Сбор данных по каждой добавке
      const supplementsData: { [key: string]: CachedCypData } = {};
      const dataSourceInfo: { [key: string]: { source: string; confidence: number; updated: string } } = {};
      let pubmedArticles = 0;
      let databaseEntries = 0;

      for (const supplement of validatedParams.supplements) {
        let dataFound = false;
        
        try {
          // 1. Пытаемся использовать готовую базу данных
          const knownSupplement = await this.safetyChecker.getSupplementInfo(supplement);
          
          if (knownSupplement && !validatedParams.force_refresh) {
            supplementsData[supplement] = this.convertDatabaseToCacheFormat(knownSupplement, supplement);
            dataSourceInfo[supplement] = {
              source: 'Database',
              confidence: 0.85,
              updated: new Date().toISOString()
            };
            databaseEntries++;
            dataFound = true;
          }
        } catch (error) {
          console.error(`Database lookup failed for ${supplement}:`, error);
        }

        // 2. Если нет в базе, пробуем ML предсказание (более надежно)
        if (!dataFound) {
          try {
            const prediction = await this.cypPredictor.predictCypInhibition(supplement);
            supplementsData[supplement] = this.convertPredictionToCacheFormat(prediction, supplement);
            dataSourceInfo[supplement] = {
              source: 'ML Prediction',
              confidence: 0.7,
              updated: new Date().toISOString()
            };
            dataFound = true;
          } catch (error) {
            console.error(`ML prediction failed for ${supplement}:`, error);
          }
        }

        // 3. Если включен поиск PubMed и ML не сработал, пробуем PubMed
        if (!dataFound && validatedParams.include_pubmed_search) {
          try {
            const searchData = await this.cypSearchAnalyzer.getOrSearchCypData(supplement);
            supplementsData[supplement] = searchData.cypProfile;
            dataSourceInfo[supplement] = {
              source: searchData.cypProfile.source === 'pubmed' ? 'PubMed Search' : 'Cache',
              confidence: searchData.confidence,
              updated: searchData.cypProfile.updated
            };
            
            if (searchData.cypProfile.source === 'pubmed') {
              pubmedArticles += searchData.cypProfile.references.length;
            }
            dataFound = true;
          } catch (error) {
            console.error(`PubMed search failed for ${supplement}:`, error);
          }
        }

        // 4. Fallback - создаем базовый профиль если ничего не сработало
        if (!dataFound) {
          console.warn(`No data found for ${supplement}, creating basic profile`);
          supplementsData[supplement] = this.createEmptyProfile(supplement);
          dataSourceInfo[supplement] = {
            source: 'Basic Profile',
            confidence: 0.3,
            updated: new Date().toISOString()
          };
        }
      }

      // 2. Анализ взаимодействий
      const supplementInteractions = this.interactionAnalyzer.analyzeSupplementInteractions(
        validatedParams.supplements,
        supplementsData
      );

      const medicationInteractions = this.interactionAnalyzer.analyzeMedicationInteractions(
        validatedParams.supplements,
        supplementsData,
        validatedParams.medications
      );

      // 3. Рекомендации по времени приема
      let timingRecommendations;
      if (validatedParams.include_timing) {
        const timingPlan = this.interactionAnalyzer.optimizeTiming(
          validatedParams.supplements,
          supplementInteractions
        );
        
        timingRecommendations = {
          ...timingPlan,
          optimal_schedule: this.generateOptimalSchedule(timingPlan)
        };
      }

      // 4. Общая оценка безопасности
      const safetySummary = this.interactionAnalyzer.generateSafetySummary(
        supplementInteractions,
        medicationInteractions
      );

      const safetyAssessment = this.generateSafetyAssessment(
        supplementInteractions,
        medicationInteractions,
        supplementsData
      );

      // 5. Практические рекомендации
      const recommendations = this.generateActionableRecommendations(
        supplementInteractions,
        medicationInteractions,
        timingRecommendations,
        validatedParams.supplements
      );

      // 6. Определение методологии
      const dataSources = Array.from(new Set(Object.values(dataSourceInfo).map(info => info.source)));
      const analysisMethod = this.determineAnalysisMethod(dataSources, validatedParams);

      return {
        analysis_summary: {
          supplements_analyzed: validatedParams.supplements.length,
          data_sources: dataSources,
          safety_score: this.extractSafetyScore(safetySummary),
          total_interactions: supplementInteractions.length + medicationInteractions.length,
          analysis_method: analysisMethod
        },
        supplements_data: this.formatSupplementsData(supplementsData, dataSourceInfo),
        interactions: {
          supplement_interactions: supplementInteractions,
          medication_interactions: medicationInteractions,
          interaction_summary: safetySummary
        },
        ...(timingRecommendations && { timing_recommendations: timingRecommendations }),
        safety_assessment: safetyAssessment,
        actionable_recommendations: recommendations,
        references: {
          pubmed_articles: pubmedArticles,
          database_entries: databaseEntries,
          total_sources: pubmedArticles + databaseEntries
        },
        ...(validatedParams.detailed_analysis && {
          methodology: {
            data_collection: 'Комбинация базы данных CYP450, поиска в PubMed и ML предсказаний',
            analysis_approach: 'Анализ парных взаимодействий, временные конфликты, фармакокинетические взаимодействия',
            limitation: 'Предсказательная модель. Не заменяет медицинскую консультацию.'
          }
        })
      };

    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new Error(`Invalid parameters: ${error.errors.map(e => e.message).join(', ')}`);
      }

      throw new Error(`Complete supplement analysis failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private convertDatabaseToCacheFormat(dbData: any, supplement: string): CachedCypData {
    const cacheData: CachedCypData = {
      CYP3A4: { action: 'unknown' },
      CYP2C9: { action: 'unknown' },
      CYP2C19: { action: 'unknown' },
      CYP2D6: { action: 'unknown' },
      CYP1A2: { action: 'unknown' },
      CYP2B6: { action: 'unknown' },
      references: dbData.references || [],
      updated: new Date().toISOString(),
      source: 'database'
    };

    // Конвертируем данные из базы
    if (dbData.cyp_effects) {
      for (const [cyp, effect] of Object.entries(dbData.cyp_effects)) {
        if (cacheData[cyp]) {
          cacheData[cyp] = {
            action: (effect as any).action,
            strength: (effect as any).strength,
            confidence: (effect as any).confidence
          };
        }
      }
    }

    return cacheData;
  }

  private convertPredictionToCacheFormat(prediction: any, supplement: string): CachedCypData {
    const cacheData: CachedCypData = {
      CYP3A4: { action: 'unknown' },
      CYP2C9: { action: 'unknown' },
      CYP2C19: { action: 'unknown' },
      CYP2D6: { action: 'unknown' },
      CYP1A2: { action: 'unknown' },
      CYP2B6: { action: 'unknown' },
      references: [],
      updated: new Date().toISOString(),
      source: 'prediction'
    };

    // Конвертируем предсказания
    if (prediction.predictions) {
      for (const [cyp, pred] of Object.entries(prediction.predictions)) {
        if (cacheData[cyp] && typeof pred === 'object' && !('error' in pred)) {
          cacheData[cyp] = {
            action: (pred as any).inhibitor ? 'inhibitor' : 'none',
            confidence: (pred as any).confidence
          };
        }
      }
    }

    return cacheData;
  }

  private createEmptyProfile(supplement: string): CachedCypData {
    return {
      CYP3A4: { action: 'unknown' },
      CYP2C9: { action: 'unknown' },
      CYP2C19: { action: 'unknown' },
      CYP2D6: { action: 'unknown' },
      CYP1A2: { action: 'unknown' },
      CYP2B6: { action: 'unknown' },
      references: [],
      updated: new Date().toISOString(),
      source: 'database'
    };
  }

  private formatSupplementsData(
    supplementsData: { [key: string]: CachedCypData },
    dataSourceInfo: { [key: string]: { source: string; confidence: number; updated: string } }
  ): any {
    const formatted: any = {};

    for (const [supplement, data] of Object.entries(supplementsData)) {
      const sourceInfo = dataSourceInfo[supplement];
      formatted[supplement] = {
        cyp_profile: data,
        data_source: sourceInfo.source,
        confidence: Math.round(sourceInfo.confidence * 100) / 100,
        last_updated: sourceInfo.updated,
        ...(data.references.length > 0 && { references: data.references })
      };
    }

    return formatted;
  }

  private generateOptimalSchedule(timingPlan: any): string {
    const morningSupps = timingPlan.morning.map((t: any) => t.supplement);
    const eveningSupps = timingPlan.evening.map((t: any) => t.supplement);
    
    let schedule = '';
    
    if (morningSupps.length > 0) {
      schedule += `🌅 Утром: ${morningSupps.join(', ')}`;
    }
    
    if (eveningSupps.length > 0) {
      if (schedule) schedule += '\n';
      schedule += `🌙 Вечером: ${eveningSupps.join(', ')}`;
    }
    
    if (timingPlan.spacing_notes.length > 0) {
      schedule += '\n⚡ Особые указания: ' + timingPlan.spacing_notes.join('; ');
    }
    
    return schedule || 'Время приема можно выбрать произвольно';
  }

  private generateSafetyAssessment(
    supplementInteractions: any[],
    medicationInteractions: any[],
    supplementsData: { [key: string]: CachedCypData }
  ): any {
    const riskFactors: string[] = [];
    const contraindications: string[] = [];
    const monitoring: string[] = [];

    // Анализ рисков
    const highRiskSupp = supplementInteractions.filter(i => i.severity === 'high');
    const highRiskMed = medicationInteractions.filter(i => i.severity === 'high');

    if (highRiskSupp.length > 0) {
      riskFactors.push(`Серьезные взаимодействия между добавками: ${highRiskSupp.length}`);
    }

    if (highRiskMed.length > 0) {
      riskFactors.push(`Критические взаимодействия с лекарствами: ${highRiskMed.length}`);
      contraindications.push('Избегать одновременного приема с указанными лекарствами');
    }

    // Мониторинг
    if (supplementInteractions.length > 0 || medicationInteractions.length > 0) {
      monitoring.push('Ведение дневника самочувствия');
      monitoring.push('Контроль эффективности лекарственных препаратов');
    }

    if (highRiskMed.length > 0) {
      monitoring.push('Регулярные лабораторные анализы');
      monitoring.push('Консультации с врачом каждые 2-4 недели');
    }

    const overallSafety = this.determineOverallSafety(supplementInteractions, medicationInteractions);

    return {
      overall_safety: overallSafety,
      risk_factors: riskFactors,
      contraindications: contraindications,
      monitoring_recommendations: monitoring
    };
  }

  private determineOverallSafety(supplementInteractions: any[], medicationInteractions: any[]): string {
    const highRisk = supplementInteractions.filter(i => i.severity === 'high').length +
                    medicationInteractions.filter(i => i.severity === 'high').length;

    const moderateRisk = supplementInteractions.filter(i => i.severity === 'moderate').length +
                        medicationInteractions.filter(i => i.severity === 'moderate').length;

    if (highRisk > 0) {
      return 'Высокий риск - требует медицинского наблюдения';
    } else if (moderateRisk > 2) {
      return 'Умеренный риск - рекомендуется консультация врача';
    } else if (supplementInteractions.length + medicationInteractions.length > 0) {
      return 'Низкий риск - следуйте рекомендациям';
    } else {
      return 'Минимальный риск - можно принимать согласно инструкциям';
    }
  }

  private generateActionableRecommendations(
    supplementInteractions: any[],
    medicationInteractions: any[],
    timingRecommendations: any,
    supplements: string[]
  ): string[] {
    const recommendations: string[] = [];

    // Высокоприоритетные рекомендации
    const criticalInteractions = medicationInteractions.filter(i => i.severity === 'high');
    if (criticalInteractions.length > 0) {
      recommendations.push('🚨 ПРИОРИТЕТ: Немедленно проконсультируйтесь с врачом о совместимости с лекарствами');
    }

    // Рекомендации по времени
    if (timingRecommendations) {
      recommendations.push('⏰ Следуйте оптимальному расписанию приема для минимизации взаимодействий');
    }

    // Мониторинг
    if (supplementInteractions.length > 0 || medicationInteractions.length > 0) {
      recommendations.push('📊 Ведите дневник приема и отмечайте любые изменения в самочувствии');
    }

    // Начало приема
    if (supplements.length > 2) {
      recommendations.push('🐌 Начните с одной добавки, добавляйте по одной каждую неделю');
    }

    // Качество
    recommendations.push('✅ Выбирайте добавки от сертифицированных производителей (GMP, NSF)');

    // Дозировки
    recommendations.push('📏 Начинайте с минимальных рекомендуемых доз');

    return recommendations;
  }

  private extractSafetyScore(safetySummary: string): string {
    if (safetySummary.includes('ВЫСОКИЙ РИСК')) return 'high_risk';
    if (safetySummary.includes('УМЕРЕННЫЙ РИСК')) return 'moderate_risk';
    if (safetySummary.includes('НИЗКИЙ РИСК')) return 'low_risk';
    return 'minimal_risk';
  }

  private determineAnalysisMethod(dataSources: string[], params: any): string {
    const methods = [];
    
    if (dataSources.includes('Database')) methods.push('База данных CYP450');
    if (dataSources.includes('PubMed Search')) methods.push('Поиск в PubMed');
    if (dataSources.includes('Cache')) methods.push('Кэшированные данные');
    if (dataSources.includes('ML Prediction')) methods.push('ML предсказания');
    
    return methods.join(' + ') || 'Базовый анализ';
  }
}