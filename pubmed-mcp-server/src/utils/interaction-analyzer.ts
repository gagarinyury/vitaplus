import { CachedCypData } from './supplement-cache.js';

export interface SupplementInteraction {
  type: 'competitive_inhibition' | 'opposing_effects' | 'additive_effects' | 'synergistic' | 'timing_conflict';
  supplements: string[];
  mechanism: string;
  severity: 'high' | 'moderate' | 'low';
  recommendation: string;
  cyp_involved?: string[];
}

export interface MedicationInteraction {
  type: 'cyp_inhibition' | 'cyp_induction' | 'pgp_interaction' | 'absorption_interference';
  supplement: string;
  medication: string;
  mechanism: string;
  severity: 'high' | 'moderate' | 'low';
  recommendation: string;
  affected_cyp?: string[];
}

export interface TimingRecommendation {
  supplement: string;
  timing: {
    time_of_day: 'morning' | 'afternoon' | 'evening' | 'any';
    with_food: boolean;
    spacing_hours?: number;
    avoid_with?: string[];
  };
  reason: string;
}

export class InteractionAnalyzer {
  // База знаний о лекарственных препаратах и их CYP-метаболизме
  private readonly MEDICATION_CYP_SUBSTRATES = {
    // Сердечно-сосудистые
    'варфарин': { cyps: ['CYP2C9'], severity: 'high', narrow_ti: true },
    'симвастатин': { cyps: ['CYP3A4'], severity: 'high', narrow_ti: false },
    'аторвастатин': { cyps: ['CYP3A4'], severity: 'moderate', narrow_ti: false },
    'клопидогрел': { cyps: ['CYP2C19'], severity: 'high', narrow_ti: true },
    'дигоксин': { cyps: ['P-gp'], severity: 'high', narrow_ti: true },
    
    // ЦНС
    'флуоксетин': { cyps: ['CYP2D6'], severity: 'moderate', narrow_ti: false },
    'пароксетин': { cyps: ['CYP2D6'], severity: 'moderate', narrow_ti: false },
    'диазепам': { cyps: ['CYP2C19', 'CYP3A4'], severity: 'moderate', narrow_ti: false },
    'фенитоин': { cyps: ['CYP2C9', 'CYP2C19'], severity: 'high', narrow_ti: true },
    
    // Гастроэнтерология
    'омепразол': { cyps: ['CYP2C19'], severity: 'moderate', narrow_ti: false },
    'лансопразол': { cyps: ['CYP2C19'], severity: 'moderate', narrow_ti: false },
    
    // Обезболивающие
    'кодеин': { cyps: ['CYP2D6'], severity: 'high', narrow_ti: true },
    'трамадол': { cyps: ['CYP2D6'], severity: 'moderate', narrow_ti: false },
    
    // Иммунодепрессанты
    'циклоспорин': { cyps: ['CYP3A4'], severity: 'high', narrow_ti: true },
    'такролимус': { cyps: ['CYP3A4'], severity: 'high', narrow_ti: true },
    
    // Онкология
    'тамоксифен': { cyps: ['CYP2D6'], severity: 'high', narrow_ti: true },
    
    // Антиаритмики
    'хинидин': { cyps: ['CYP3A4'], severity: 'high', narrow_ti: true },
    
    // Противоэпилептические
    'карбамазепин': { cyps: ['CYP3A4'], severity: 'moderate', narrow_ti: true }
  };

  // Правила времени приема добавок
  private readonly TIMING_RULES = {
    'ashwagandha': { 
      time: 'evening' as const, 
      food: true, 
      reason: 'Седативный эффект, лучше вечером с едой',
      spacing: 4
    },
    'rhodiola': { 
      time: 'morning' as const, 
      food: false, 
      reason: 'Стимулирующий эффект, утром натощак',
      spacing: 2
    },
    'магний': { 
      time: 'evening' as const, 
      food: false, 
      reason: 'Расслабляющий эффект, вечером',
      spacing: 2
    },
    'железо': { 
      time: 'morning' as const, 
      food: false, 
      reason: 'Лучшее всасывание натощак утром',
      spacing: 4,
      avoid: ['кальций', 'цинк', 'кофе', 'чай']
    },
    'кальций': { 
      time: 'evening' as const, 
      food: true, 
      reason: 'Лучшее усвоение вечером с едой',
      spacing: 4,
      avoid: ['железо', 'цинк']
    },
    'витамин_d': { 
      time: 'morning' as const, 
      food: true, 
      reason: 'Жирорастворимый, с едой содержащей жиры',
      spacing: 1
    },
    'куркума': { 
      time: 'any' as const, 
      food: true, 
      reason: 'С едой и черным перцем для лучшего усвоения',
      spacing: 2
    },
    'зеленый_чай': { 
      time: 'morning' as const, 
      food: false, 
      reason: 'Кофеин, избегать вечером',
      spacing: 2,
      avoid: ['железо']
    },
    'гинкго': { 
      time: 'morning' as const, 
      food: true, 
      reason: 'Стимулирующий эффект, с едой',
      spacing: 2
    },
    'валериана': { 
      time: 'evening' as const, 
      food: false, 
      reason: 'Седативный эффект перед сном',
      spacing: 1
    }
  };

  analyzeSupplementInteractions(
    supplements: string[],
    supplementsData: { [key: string]: CachedCypData }
  ): SupplementInteraction[] {
    const interactions: SupplementInteraction[] = [];

    // Проверяем парные взаимодействия
    for (let i = 0; i < supplements.length; i++) {
      for (let j = i + 1; j < supplements.length; j++) {
        const supp1 = supplements[i];
        const supp2 = supplements[j];
        const data1 = supplementsData[supp1];
        const data2 = supplementsData[supp2];

        if (!data1 || !data2) continue;

        const interaction = this.checkSupplementPairInteraction(supp1, data1, supp2, data2);
        if (interaction) {
          interactions.push(interaction);
        }
      }
    }

    return interactions;
  }

  private checkSupplementPairInteraction(
    supp1: string,
    data1: CachedCypData,
    supp2: string,
    data2: CachedCypData
  ): SupplementInteraction | null {
    
    const cypEnzymes = ['CYP3A4', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP1A2', 'CYP2B6'];
    
    for (const cyp of cypEnzymes) {
      const action1 = data1[cyp]?.action;
      const action2 = data2[cyp]?.action;

      if (!action1 || !action2 || action1 === 'unknown' || action2 === 'unknown') {
        continue;
      }

      // Competitive inhibition - оба ингибируют один CYP
      if (action1 === 'inhibitor' && action2 === 'inhibitor') {
        const strength1 = data1[cyp]?.strength || 'unknown';
        const strength2 = data2[cyp]?.strength || 'unknown';
        
        let severity: 'high' | 'moderate' | 'low' = 'moderate';
        if (strength1 === 'strong' || strength2 === 'strong') {
          severity = 'high';
        } else if (strength1 === 'weak' && strength2 === 'weak') {
          severity = 'low';
        }

        return {
          type: 'competitive_inhibition',
          supplements: [supp1, supp2],
          mechanism: `Оба ингибируют ${cyp}, что может привести к аддитивному эффекту`,
          severity,
          recommendation: severity === 'high' 
            ? 'Избегать одновременного приема или значительно снизить дозы'
            : 'Рассмотреть снижение дозы одной из добавок или разделение приема на 4-6 часов',
          cyp_involved: [cyp]
        };
      }

      // Opposing effects - индуктор vs ингибитор
      if ((action1 === 'inducer' && action2 === 'inhibitor') ||
          (action1 === 'inhibitor' && action2 === 'inducer')) {
        
        return {
          type: 'opposing_effects',
          supplements: [supp1, supp2],
          mechanism: `${supp1} и ${supp2} оказывают противоположное влияние на ${cyp}`,
          severity: 'moderate',
          recommendation: 'Эффекты могут взаимно нейтрализоваться, мониторинг эффективности',
          cyp_involved: [cyp]
        };
      }

      // Additive induction
      if (action1 === 'inducer' && action2 === 'inducer') {
        return {
          type: 'additive_effects',
          supplements: [supp1, supp2],
          mechanism: `Оба индуцируют ${cyp}, возможен аддитивный эффект`,
          severity: 'moderate',
          recommendation: 'Может привести к ускоренному метаболизму лекарств, требует мониторинга',
          cyp_involved: [cyp]
        };
      }
    }

    // Проверяем специфические взаимодействия
    return this.checkSpecificInteractions(supp1, supp2);
  }

  private checkSpecificInteractions(supp1: string, supp2: string): SupplementInteraction | null {
    // Железо и кальций
    if ((supp1.includes('железо') && supp2.includes('кальций')) ||
        (supp1.includes('кальций') && supp2.includes('железо'))) {
      return {
        type: 'timing_conflict',
        supplements: [supp1, supp2],
        mechanism: 'Кальций снижает всасывание железа',
        severity: 'moderate',
        recommendation: 'Принимать с интервалом минимум 2 часа'
      };
    }

    // Железо и цинк
    if ((supp1.includes('железо') && supp2.includes('цинк')) ||
        (supp1.includes('цинк') && supp2.includes('железо'))) {
      return {
        type: 'timing_conflict',
        supplements: [supp1, supp2],
        mechanism: 'Конкуренция за всасывание в кишечнике',
        severity: 'moderate',
        recommendation: 'Принимать с интервалом 2-3 часа'
      };
    }

    return null;
  }

  analyzeMedicationInteractions(
    supplements: string[],
    supplementsData: { [key: string]: CachedCypData },
    medications: string[]
  ): MedicationInteraction[] {
    const interactions: MedicationInteraction[] = [];

    for (const supplement of supplements) {
      const suppData = supplementsData[supplement];
      if (!suppData) continue;

      for (const medication of medications) {
        const medInteraction = this.checkMedicationInteraction(supplement, suppData, medication);
        if (medInteraction) {
          interactions.push(medInteraction);
        }
      }
    }

    return interactions;
  }

  private checkMedicationInteraction(
    supplement: string,
    suppData: CachedCypData,
    medication: string
  ): MedicationInteraction | null {
    
    const normalizedMed = medication.toLowerCase();
    const medData = this.MEDICATION_CYP_SUBSTRATES[normalizedMed];
    
    if (!medData) return null;

    // Проверяем каждый CYP, которым метаболизируется лекарство
    for (const cyp of medData.cyps) {
      const suppAction = suppData[cyp]?.action;
      
      if (!suppAction || suppAction === 'unknown') continue;

      let severity: 'high' | 'moderate' | 'low' = 'moderate';
      let mechanism = '';
      let recommendation = '';

      if (suppAction === 'inhibitor') {
        mechanism = `${supplement} ингибирует ${cyp}, может повысить концентрацию ${medication}`;
        
        if (medData.narrow_ti) {
          severity = 'high';
          recommendation = '⚠️ КРИТИЧНО: Избегать комбинации или требуется коррекция дозы под контролем врача';
        } else {
          severity = medData.severity === 'high' ? 'high' : 'moderate';
          recommendation = severity === 'high' 
            ? 'Требуется мониторинг и возможная коррекция дозы лекарства'
            : 'Наблюдение за усилением эффектов лекарства';
        }
      } else if (suppAction === 'inducer') {
        mechanism = `${supplement} индуцирует ${cyp}, может снизить эффективность ${medication}`;
        
        if (medData.narrow_ti) {
          severity = 'high';
          recommendation = '⚠️ КРИТИЧНО: Может потребоваться увеличение дозы лекарства под контролем врача';
        } else {
          severity = 'moderate';
          recommendation = 'Мониторинг эффективности лекарства, возможна коррекция дозы';
        }
      }

      if (mechanism) {
        return {
          type: suppAction === 'inhibitor' ? 'cyp_inhibition' : 'cyp_induction',
          supplement,
          medication,
          mechanism,
          severity,
          recommendation,
          affected_cyp: [cyp]
        };
      }
    }

    return null;
  }

  optimizeTiming(
    supplements: string[],
    interactions: SupplementInteraction[]
  ): { 
    morning: TimingRecommendation[];
    afternoon: TimingRecommendation[];
    evening: TimingRecommendation[];
    spacing_notes: string[];
  } {
    
    const timingPlan = {
      morning: [] as TimingRecommendation[],
      afternoon: [] as TimingRecommendation[],
      evening: [] as TimingRecommendation[],
      spacing_notes: [] as string[]
    };

    // Сначала применяем базовые правила
    for (const supplement of supplements) {
      const rule = this.getTimingRule(supplement);
      const timing: TimingRecommendation = {
        supplement,
        timing: {
          time_of_day: rule.time,
          with_food: rule.food,
          spacing_hours: rule.spacing,
          avoid_with: rule.avoid || []
        },
        reason: rule.reason
      };

      // Добавляем в соответствующий временной слот
      if (rule.time === 'morning') {
        timingPlan.morning.push(timing);
      } else if (rule.time === 'afternoon') {
        timingPlan.afternoon.push(timing);
      } else if (rule.time === 'evening') {
        timingPlan.evening.push(timing);
      } else {
        // Для 'any' добавляем в утро по умолчанию
        timingPlan.morning.push(timing);
      }
    }

    // Корректируем на основе взаимодействий
    for (const interaction of interactions) {
      if (interaction.severity === 'high' || interaction.type === 'timing_conflict') {
        // Разделяем конфликтующие добавки
        const [supp1, supp2] = interaction.supplements;
        
        // Если обе добавки в одном временном слоте, переносим одну
        const morning = timingPlan.morning.map(t => t.supplement);
        const evening = timingPlan.evening.map(t => t.supplement);
        
        if (morning.includes(supp1) && morning.includes(supp2)) {
          // Переносим вторую добавку на вечер
          const suppToMove = timingPlan.morning.find(t => t.supplement === supp2);
          if (suppToMove) {
            timingPlan.morning = timingPlan.morning.filter(t => t.supplement !== supp2);
            suppToMove.timing.time_of_day = 'evening';
            timingPlan.evening.push(suppToMove);
            timingPlan.spacing_notes.push(
              `${supp1} и ${supp2} разделены из-за взаимодействия: ${interaction.mechanism}`
            );
          }
        }
        
        if (evening.includes(supp1) && evening.includes(supp2)) {
          // Переносим вторую добавку на утро
          const suppToMove = timingPlan.evening.find(t => t.supplement === supp2);
          if (suppToMove) {
            timingPlan.evening = timingPlan.evening.filter(t => t.supplement !== supp2);
            suppToMove.timing.time_of_day = 'morning';
            timingPlan.morning.push(suppToMove);
            timingPlan.spacing_notes.push(
              `${supp1} и ${supp2} разделены из-за взаимодействия: ${interaction.mechanism}`
            );
          }
        }
      }
    }

    return timingPlan;
  }

  private getTimingRule(supplement: string): {
    time: 'morning' | 'afternoon' | 'evening' | 'any';
    food: boolean;
    reason: string;
    spacing?: number;
    avoid?: string[];
  } {
    const normalizedSupp = supplement.toLowerCase().replace(/[^a-z]/g, '_');
    
    // Проверяем точные совпадения
    for (const [key, rule] of Object.entries(this.TIMING_RULES)) {
      if (normalizedSupp.includes(key) || key.includes(normalizedSupp)) {
        return {
          time: rule.time,
          food: rule.food,
          reason: rule.reason,
          spacing: rule.spacing,
          avoid: (rule as any).avoid || []
        };
      }
    }

    // Дефолтные правила на основе типа добавки
    if (normalizedSupp.includes('витамин')) {
      return {
        time: 'morning',
        food: true,
        reason: 'Витамины лучше усваиваются утром с едой',
        avoid: []
      };
    }

    if (normalizedSupp.includes('минерал') || normalizedSupp.includes('магний') || 
        normalizedSupp.includes('цинк') || normalizedSupp.includes('кальций')) {
      return {
        time: 'evening',
        food: false,
        reason: 'Минералы лучше усваиваются вечером',
        avoid: []
      };
    }

    if (normalizedSupp.includes('травяной') || normalizedSupp.includes('экстракт')) {
      return {
        time: 'any',
        food: true,
        reason: 'Растительные экстракты с едой для лучшей переносимости',
        avoid: []
      };
    }

    // Дефолт
    return {
      time: 'any',
      food: true,
      reason: 'Универсальная рекомендация с едой',
      avoid: []
    };
  }

  generateSafetySummary(
    interactions: SupplementInteraction[],
    medInteractions: MedicationInteraction[]
  ): string {
    
    const totalInteractions = interactions.length + medInteractions.length;
    const highRiskInteractions = [
      ...interactions.filter(i => i.severity === 'high'),
      ...medInteractions.filter(i => i.severity === 'high')
    ].length;

    const moderateRiskInteractions = [
      ...interactions.filter(i => i.severity === 'moderate'),
      ...medInteractions.filter(i => i.severity === 'moderate')
    ].length;

    if (highRiskInteractions > 0) {
      return `⚠️ ВЫСОКИЙ РИСК: Обнаружено ${highRiskInteractions} серьезных взаимодействий. Обязательная консультация врача перед началом приема.`;
    }

    if (moderateRiskInteractions > 2) {
      return `⚡ УМЕРЕННЫЙ РИСК: ${moderateRiskInteractions} взаимодействий средней степени. Рекомендуется медицинский контроль и мониторинг.`;
    }

    if (totalInteractions > 0) {
      return `✓ НИЗКИЙ РИСК: ${totalInteractions} минимальных взаимодействий. Следуйте рекомендациям по времени приема.`;
    }

    return `✅ БЕЗОПАСНО: Значимых взаимодействий не обнаружено. Можно принимать согласно стандартным рекомендациям.`;
  }
}