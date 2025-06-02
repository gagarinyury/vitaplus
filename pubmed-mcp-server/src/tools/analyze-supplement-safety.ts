import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { SupplementSafetyChecker } from '../utils/supplement-safety-checker.js';

const AnalyzeSupplementSafetyParamsSchema = z.object({
  supplements: z.array(z.string()).min(1, "At least one supplement is required").max(10, "Maximum 10 supplements allowed"),
  drugs: z.array(z.string()).optional().default([]),
  include_mechanisms: z.boolean().optional().default(true),
  detailed_analysis: z.boolean().optional().default(false)
});

export type AnalyzeSupplementSafetyParams = z.infer<typeof AnalyzeSupplementSafetyParamsSchema>;

export class AnalyzeSupplementSafetyTool {
  private safetyChecker: SupplementSafetyChecker;

  constructor() {
    this.safetyChecker = new SupplementSafetyChecker();
  }

  getToolDefinition(): Tool {
    return {
      name: 'analyze_supplement_safety',
      description: 'Анализирует безопасность комбинации добавок на основе CYP450 взаимодействий. Проверяет потенциальные конфликты между добавками и взаимодействия с лекарственными препаратами. Использует предрассчитанную базу данных по 200+ популярным добавкам.',
      inputSchema: {
        type: 'object',
        properties: {
          supplements: {
            type: 'array',
            description: 'Список добавок для анализа (на английском). Примеры: ashwagandha, rhodiola, turmeric, ginkgo, vitamin_d',
            items: {
              type: 'string'
            },
            minItems: 1,
            maxItems: 10
          },
          drugs: {
            type: 'array',
            description: 'Опциональный список принимаемых лекарственных препаратов для проверки взаимодействий',
            items: {
              type: 'string'
            },
            default: []
          },
          include_mechanisms: {
            type: 'boolean',
            description: 'Включить описание механизмов взаимодействий (CYP450)',
            default: true
          },
          detailed_analysis: {
            type: 'boolean',
            description: 'Подробный анализ с дополнительными рекомендациями',
            default: false
          }
        },
        required: ['supplements'],
        additionalProperties: false
      }
    };
  }

  async execute(params: unknown): Promise<{
    safety_analysis: {
      safety_score: string;
      total_interactions: number;
      summary: string;
    };
    cyp_conflicts: Array<{
      supplements: string[];
      cyp_enzyme: string;
      conflict_type: string;
      severity: string;
      description: string;
      mechanism?: string;
    }>;
    drug_interactions: Array<{
      drug: string;
      supplement: string;
      cyp_enzyme: string;
      mechanism: string;
      severity: string;
      recommendation: string;
    }>;
    recommendations: string[];
    safety_tips: string[];
    references: {
      pubmed_links: string[];
      total_studies: number;
    };
    available_supplements?: string[];
  }> {
    try {
      // Validate parameters
      const validatedParams = AnalyzeSupplementSafetyParamsSchema.parse(params);

      // Perform safety analysis
      const result = await this.safetyChecker.analyzeCombination(
        validatedParams.supplements,
        validatedParams.drugs
      );

      // Enhance conflicts with mechanisms if requested
      const enhancedConflicts = validatedParams.include_mechanisms 
        ? result.cyp_conflicts.map(conflict => ({
            supplements: [conflict.supplement1, conflict.supplement2],
            cyp_enzyme: conflict.cyp_enzyme,
            conflict_type: conflict.conflict_type,
            severity: conflict.severity,
            description: conflict.description,
            mechanism: this.generateMechanismExplanation(conflict.cyp_enzyme, conflict.conflict_type)
          }))
        : result.cyp_conflicts.map(conflict => ({
            supplements: [conflict.supplement1, conflict.supplement2],
            cyp_enzyme: conflict.cyp_enzyme,
            conflict_type: conflict.conflict_type,
            severity: conflict.severity,
            description: conflict.description
          }));

      // Generate safety tips
      const safetyTips = this.generateSafetyTips(validatedParams.supplements, result);

      // Convert PMID references to PubMed links
      const pubmedLinks = result.references
        .filter(ref => ref.startsWith('PMID:'))
        .map(ref => `https://pubmed.ncbi.nlm.nih.gov/${ref.replace('PMID:', '')}/`);

      // Get available supplements list if requested
      let availableSupplements: string[] | undefined;
      if (validatedParams.detailed_analysis) {
        availableSupplements = await this.safetyChecker.listAvailableSupplements();
      }

      return {
        safety_analysis: {
          safety_score: result.safety_score,
          total_interactions: result.cyp_conflicts.length + result.drug_interactions.length,
          summary: result.summary
        },
        cyp_conflicts: enhancedConflicts,
        drug_interactions: result.drug_interactions,
        recommendations: result.recommendations,
        safety_tips: safetyTips,
        references: {
          pubmed_links: pubmedLinks,
          total_studies: result.references.length
        },
        ...(availableSupplements && { available_supplements: availableSupplements })
      };

    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new Error(`Invalid parameters: ${error.errors.map(e => e.message).join(', ')}`);
      }

      if (error.message.includes('Unknown supplements')) {
        // Get list of available supplements for helpful error message
        const availableSupplements = await this.safetyChecker.listAvailableSupplements();
        throw new Error(`${error.message}. Available supplements: ${availableSupplements.slice(0, 20).join(', ')}... (showing first 20)`);
      }

      throw new Error(`Safety analysis failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private generateMechanismExplanation(cypEnzyme: string, conflictType: string): string {
    const enzymeDescriptions = {
      'CYP3A4': 'метаболизирует ~50% всех лекарств, включая статины, иммунодепрессанты',
      'CYP2D6': 'метаболизирует антидепрессанты, бета-блокаторы, обезболивающие',
      'CYP2C9': 'метаболизирует варфарин, НПВС, некоторые диабетические препараты',
      'CYP2C19': 'метаболизирует ингибиторы протонной помпы, клопидогрел',
      'CYP1A2': 'метаболизирует кофеин, теофиллин, некоторые антипсихотики',
      'CYP2B6': 'метаболизирует бупропион, эфавиренз, циклофосфамид'
    };

    const baseDescription = enzymeDescriptions[cypEnzyme] || 'участвует в метаболизме лекарств';

    if (conflictType === 'opposing_effects') {
      return `${cypEnzyme} ${baseDescription}. Противоположные эффекты могут привести к непредсказуемым изменениям уровня препаратов.`;
    } else if (conflictType === 'additive_inhibition') {
      return `${cypEnzyme} ${baseDescription}. Суммарное ингибирование может значительно повысить уровень препаратов.`;
    }

    return `${cypEnzyme} ${baseDescription}.`;
  }

  private generateSafetyTips(supplements: string[], analysisResult: any): string[] {
    const tips: string[] = [];

    // General timing tips
    if (analysisResult.cyp_conflicts.length > 0) {
      tips.push('⏰ Принимайте конфликтующие добавки в разное время дня (интервал 2-4 часа)');
      tips.push('🍽️ Некоторые добавки лучше усваиваются с едой, другие - натощак');
    }

    // Monitoring tips
    if (analysisResult.drug_interactions.length > 0) {
      tips.push('📊 Ведите дневник самочувствия для отслеживания изменений');
      tips.push('🩺 Регулярно контролируйте эффективность лекарственных препаратов');
    }

    // Specific supplement tips
    if (supplements.includes('turmeric') || supplements.includes('curcumin')) {
      tips.push('🌶️ Куркумин: принимайте с черным перцем (пиперин) для лучшего усвоения');
    }

    if (supplements.includes('ashwagandha')) {
      tips.push('🌙 Ашваганда: лучше принимать вечером из-за седативного эффекта');
    }

    if (supplements.includes('rhodiola')) {
      tips.push('☀️ Родиола: принимайте утром, может влиять на сон');
    }

    if (supplements.includes('green_tea') || supplements.includes('egcg')) {
      tips.push('☕ Зеленый чай: ограничьте кофеин, может усилить стимулирующий эффект');
    }

    // Start slow tip
    if (supplements.length > 2) {
      tips.push('🐌 Начните с одной добавки, постепенно добавляйте остальные (1 новая в неделю)');
    }

    // Quality tip
    tips.push('✅ Выбирайте добавки от проверенных производителей с сертификатами качества');

    return tips;
  }
}