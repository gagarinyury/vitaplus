import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { CypPredictor } from '../utils/cyp-predictor.js';

const PredictCypInhibitionParamsSchema = z.object({
  supplement_name: z.string().min(1, "Supplement name is required"),
  smiles: z.string().optional(),
  check_cyps: z.array(z.string()).optional().default(['3A4', '2C9', '2C19', '2D6', '1A2', '2B6']),
  include_drug_interactions: z.boolean().optional().default(true),
  detailed_analysis: z.boolean().optional().default(false)
});

export type PredictCypInhibitionParams = z.infer<typeof PredictCypInhibitionParamsSchema>;

export class PredictCypInhibitionTool {
  private cypPredictor: CypPredictor;

  constructor() {
    this.cypPredictor = new CypPredictor();
  }

  getToolDefinition(): Tool {
    return {
      name: 'predict_cyp_inhibition',
      description: 'Предсказывает потенциальное ингибирование ферментов CYP450 для любой добавки или соединения с использованием машинного обучения и молекулярного анализа. Автоматически получает химическую структуру из PubChem или принимает SMILES структуру. Полезно для анализа новых или неизвестных добавок.',
      inputSchema: {
        type: 'object',
        properties: {
          supplement_name: {
            type: 'string',
            description: 'Название добавки или соединения для анализа. Примеры: curcumin, resveratrol, quercetin, berberine',
            minLength: 1
          },
          smiles: {
            type: 'string',
            description: 'SMILES структура молекулы (опционально). Если не указана, будет автоматически получена из PubChem'
          },
          check_cyps: {
            type: 'array',
            description: 'Список CYP ферментов для проверки',
            items: {
              type: 'string',
              enum: ['1A2', '2C9', '2C19', '2D6', '2B6', '3A4']
            },
            default: ['3A4', '2C9', '2C19', '2D6', '1A2', '2B6']
          },
          include_drug_interactions: {
            type: 'boolean',
            description: 'Включить предсказания взаимодействий с конкретными лекарствами',
            default: true
          },
          detailed_analysis: {
            type: 'boolean',
            description: 'Подробный анализ с объяснением методологии',
            default: false
          }
        },
        required: ['supplement_name'],
        additionalProperties: false
      }
    };
  }

  async execute(params: unknown): Promise<{
    prediction_summary: {
      supplement: string;
      overall_risk: string;
      high_risk_cyps: string[];
      moderate_risk_cyps: string[];
      methodology: string;
    };
    cyp_predictions: Array<{
      cyp_enzyme: string;
      inhibitor: boolean;
      confidence: number;
      probability: number;
      method: string;
      interpretation: string;
    }>;
    drug_interactions?: Array<{
      drug: string;
      cyp_enzyme: string;
      risk_description: string;
      severity: string;
      recommendation: string;
    }>;
    chemical_info?: {
      smiles?: string;
      source: string;
      molecular_features?: any;
    };
    recommendations: string[];
    disclaimer: string;
  }> {
    try {
      const validatedParams = PredictCypInhibitionParamsSchema.parse(params);

      // Выполняем предсказание
      const result = await this.cypPredictor.predictCypInhibition(
        validatedParams.supplement_name,
        validatedParams.smiles,
        validatedParams.check_cyps
      );

      // Форматируем CYP предсказания
      const cypPredictions = Object.entries(result.predictions)
        .filter(([_, prediction]) => !('error' in prediction))
        .map(([cyp, prediction]) => {
          const pred = prediction as any; // избегаем ошибки типов
          return {
            cyp_enzyme: cyp,
            inhibitor: pred.inhibitor,
            confidence: Math.round(pred.confidence * 100) / 100,
            probability: Math.round(pred.probability * 100) / 100,
            method: pred.method,
            interpretation: this.interpretSinglePrediction(cyp, pred)
          };
        });

      // Форматируем взаимодействия с лекарствами
      let drugInteractions;
      if (validatedParams.include_drug_interactions) {
        drugInteractions = result.potential_drug_interactions.map(interaction => ({
          drug: interaction.drug,
          cyp_enzyme: interaction.cyp,
          risk_description: interaction.risk,
          severity: interaction.severity,
          recommendation: this.getDrugRecommendation(interaction.severity, interaction.drug)
        }));
      }

      // Информация о химической структуре
      const chemicalInfo = {
        smiles: result.smiles,
        source: result.smiles ? 'PubChem API' : 'Not available',
        ...(validatedParams.detailed_analysis && result.smiles && {
          molecular_features: this.describeMolecularFeatures(result.smiles)
        })
      };

      // Генерируем рекомендации
      const recommendations = this.generateRecommendations(result, validatedParams.supplement_name);

      // Определяем методологию
      const methodology = this.describeMethodology(cypPredictions, validatedParams.detailed_analysis);

      return {
        prediction_summary: {
          supplement: validatedParams.supplement_name,
          overall_risk: result.summary.risk_level,
          high_risk_cyps: result.summary.high_risk_cyps,
          moderate_risk_cyps: result.summary.moderate_risk_cyps,
          methodology
        },
        cyp_predictions: cypPredictions,
        ...(drugInteractions && { drug_interactions: drugInteractions }),
        chemical_info: chemicalInfo,
        recommendations,
        disclaimer: this.getDisclaimer()
      };

    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new Error(`Invalid parameters: ${error.errors.map(e => e.message).join(', ')}`);
      }

      throw new Error(`CYP prediction failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private interpretSinglePrediction(cyp: string, prediction: any): string {
    const confidence = Math.round(prediction.confidence * 100);
    
    if (prediction.inhibitor) {
      if (prediction.confidence > 0.8) {
        return `🔴 Высокая вероятность ингибирования ${cyp} (${confidence}% уверенность)`;
      } else if (prediction.confidence > 0.6) {
        return `🟡 Умеренная вероятность ингибирования ${cyp} (${confidence}% уверенность)`;
      } else {
        return `🟠 Низкая вероятность ингибирования ${cyp} (${confidence}% уверенность)`;
      }
    } else {
      return `🟢 Ингибирование ${cyp} маловероятно (${confidence}% уверенность)`;
    }
  }

  private getDrugRecommendation(severity: string, drug: string): string {
    switch (severity) {
      case 'major':
        return `⚠️ КРИТИЧНО: Избегайте одновременного приема с ${drug}. Обязательная консультация врача.`;
      case 'moderate':
        return `⚡ ОСТОРОЖНО: Мониторинг эффектов ${drug}. Возможна корректировка дозы.`;
      case 'minor':
        return `💡 ИНФОРМАЦИЯ: Минимальный риск взаимодействия с ${drug}. Наблюдение.`;
      default:
        return `Мониторинг взаимодействия с ${drug}`;
    }
  }

  private describeMolecularFeatures(smiles: string): any {
    // Простой анализ SMILES структуры
    return {
      estimated_atoms: smiles.length,
      contains_nitrogen: smiles.includes('N') || smiles.includes('n'),
      contains_oxygen: smiles.includes('O') || smiles.includes('o'),
      contains_sulfur: smiles.includes('S') || smiles.includes('s'),
      aromatic_systems: (smiles.match(/c|C/g) || []).length > 6,
      complexity_score: Math.min(10, Math.round(smiles.length / 10))
    };
  }

  private generateRecommendations(result: any, supplementName: string): string[] {
    const recommendations: string[] = [];

    // Основные рекомендации на основе риска
    if (result.summary.risk_level === 'high') {
      recommendations.push('🚨 ВЫСОКИЙ РИСК: Обязательно проконсультируйтесь с врачом перед приемом');
      recommendations.push('📋 Предоставьте врачу список всех принимаемых лекарств');
      recommendations.push('🕒 Если врач разрешит прием, разделяйте с лекарствами на 4-6 часов');
    } else if (result.summary.risk_level === 'moderate') {
      recommendations.push('⚡ УМЕРЕННЫЙ РИСК: Рекомендуется консультация врача');
      recommendations.push('📊 Ведите дневник самочувствия для отслеживания изменений');
      recommendations.push('🕒 Разделяйте прием с лекарствами на 2-4 часа');
    } else {
      recommendations.push('✅ НИЗКИЙ РИСК: Значимые взаимодействия маловероятны');
      recommendations.push('👨‍⚕️ При приеме лекарств всё равно уведомите врача');
    }

    // Специфические рекомендации
    if (result.potential_drug_interactions.length > 0) {
      recommendations.push('💊 Особое внимание к указанным лекарственным взаимодействиям');
    }

    // Общие рекомендации
    recommendations.push(`🧪 Начните с минимальной дозы ${supplementName} для оценки переносимости`);
    recommendations.push('📚 Изучите научную литературу о безопасности данной добавки');
    
    return recommendations;
  }

  private describeMethodology(predictions: any[], detailed: boolean): string {
    const methods = [...new Set(predictions.map(p => p.method))];
    
    let description = 'Анализ выполнен с использованием: ';
    
    if (methods.includes('api')) {
      description += 'машинное обучение (внешний API), ';
    }
    if (methods.includes('database')) {
      description += 'база известных взаимодействий, ';
    }
    if (methods.includes('local')) {
      description += 'молекулярные дескрипторы и структурные правила';
    }

    if (detailed) {
      description += '. Предсказания основаны на анализе химической структуры, молекулярных свойств и известных паттернов взаимодействий с CYP450 ферментами.';
    }

    return description.replace(/, $/, '');
  }

  private getDisclaimer(): string {
    return '⚠️ ВНИМАНИЕ: Это предсказательная модель, не заменяющая медицинскую консультацию. Результаты носят информационный характер. Обязательно консультируйтесь с врачом перед изменением схемы приема лекарств или добавлением новых добавок.';
  }
}