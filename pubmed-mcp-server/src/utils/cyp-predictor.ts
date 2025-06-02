import fetch from 'node-fetch';

export interface CypPrediction {
  inhibitor: boolean;
  confidence: number;
  probability: number;
  method: 'api' | 'local' | 'database';
}

export interface CypPredictionResult {
  supplement: string;
  smiles?: string;
  predictions: {
    [cyp: string]: CypPrediction | { error: string };
  };
  summary: {
    risk_level: 'high' | 'moderate' | 'low';
    high_risk_cyps: string[];
    moderate_risk_cyps: string[];
    interpretation: string;
  };
  potential_drug_interactions: Array<{
    drug: string;
    cyp: string;
    risk: string;
    severity: 'major' | 'moderate' | 'minor';
  }>;
}

export class CypPredictor {
  private readonly DRUG_SUBSTRATES = {
    'CYP3A4': [
      { name: 'симвастатин', severity: 'major' as const },
      { name: 'аторвастатин', severity: 'major' as const },
      { name: 'циклоспорин', severity: 'major' as const },
      { name: 'такролимус', severity: 'major' as const },
      { name: 'мидазолам', severity: 'moderate' as const },
      { name: 'нифедипин', severity: 'moderate' as const },
      { name: 'силденафил', severity: 'moderate' as const }
    ],
    'CYP2C9': [
      { name: 'варфарин', severity: 'major' as const },
      { name: 'фенитоин', severity: 'major' as const },
      { name: 'ибупрофен', severity: 'moderate' as const },
      { name: 'диклофенак', severity: 'moderate' as const },
      { name: 'лозартан', severity: 'moderate' as const }
    ],
    'CYP2D6': [
      { name: 'флуоксетин', severity: 'major' as const },
      { name: 'пароксетин', severity: 'major' as const },
      { name: 'метопролол', severity: 'moderate' as const },
      { name: 'кодеин', severity: 'major' as const },
      { name: 'тамоксифен', severity: 'major' as const }
    ],
    'CYP2C19': [
      { name: 'омепразол', severity: 'moderate' as const },
      { name: 'клопидогрел', severity: 'major' as const },
      { name: 'диазепам', severity: 'moderate' as const },
      { name: 'фенитоин', severity: 'major' as const }
    ],
    'CYP1A2': [
      { name: 'кофеин', severity: 'minor' as const },
      { name: 'теофиллин', severity: 'major' as const },
      { name: 'клозапин', severity: 'major' as const },
      { name: 'оланзапин', severity: 'moderate' as const }
    ],
    'CYP2B6': [
      { name: 'бупропион', severity: 'moderate' as const },
      { name: 'эфавиренз', severity: 'major' as const },
      { name: 'метадон', severity: 'moderate' as const }
    ]
  };

  private readonly MOLECULAR_RULES = {
    // Простые правила на основе структурных особенностей
    'CYP3A4': {
      // Большие, липофильные молекулы
      mw_threshold: 400,
      logp_min: 2,
      aromatic_rings_min: 2
    },
    'CYP2C9': {
      // Кислые соединения
      has_carboxyl: true,
      mw_range: [200, 500]
    },
    'CYP2D6': {
      // Основные соединения с азотом
      has_nitrogen: true,
      basic_nitrogen: true
    },
    'CYP1A2': {
      // Плоские ароматические системы
      aromatic_rings_min: 2,
      planar: true
    }
  };

  async getSmilesFromPubChem(compoundName: string): Promise<string | null> {
    try {
      // Нормализуем название для поиска
      const cleanName = compoundName.toLowerCase()
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, ' ')
        .trim();

      const url = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent(cleanName)}/property/CanonicalSMILES/JSON`;
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'User-Agent': 'VitaPlus-MCP-Server/1.0'
        }
      });
      
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json() as any;
        return data.PropertyTable?.Properties?.[0]?.CanonicalSMILES || null;
      }
    } catch (error) {
      console.error(`Failed to get SMILES for ${compoundName}:`, error);
    }

    return null;
  }

  async predictCypInhibition(
    supplementName: string,
    smiles?: string,
    checkCyps: string[] = ['3A4', '2C9', '2C19', '2D6', '1A2', '2B6']
  ): Promise<CypPredictionResult> {
    
    // 1. Получаем SMILES если не предоставлен
    if (!smiles) {
      smiles = await this.getSmilesFromPubChem(supplementName);
    }

    const predictions: { [cyp: string]: CypPrediction | { error: string } } = {};

    // 2. Пытаемся использовать внешние API или локальные предсказания
    for (const cyp of checkCyps) {
      const cypKey = `CYP${cyp}`;
      
      try {
        // Сначала пробуем API предсказание (если доступно)
        // const apiPrediction = await this.tryApiPrediction(smiles, cypKey);
        // if (apiPrediction) {
        //   predictions[cypKey] = apiPrediction;
        //   continue;
        // }

        // Fallback на локальные правила
        const localPrediction = this.predictLocalCyp(smiles, cypKey, supplementName);
        predictions[cypKey] = localPrediction;
        
      } catch (error) {
        predictions[cypKey] = { error: error.message };
      }
    }

    // 3. Интерпретируем результаты
    const summary = this.interpretPredictions(predictions);
    const drugInteractions = this.getPotentialDrugInteractions(predictions);

    return {
      supplement: supplementName,
      smiles,
      predictions,
      summary,
      potential_drug_interactions: drugInteractions
    };
  }

  private predictLocalCyp(smiles: string | undefined, cyp: string, supplementName: string): CypPrediction {
    // Локальные правила предсказания на основе известных паттернов
    
    if (!smiles) {
      // Если нет SMILES, используем название добавки для эвристического предсказания
      return this.predictBySupplement(supplementName, cyp);
    }

    // Простой анализ SMILES структуры
    const features = this.extractSimpleFeatures(smiles);
    const rules = this.MOLECULAR_RULES[cyp];

    if (!rules) {
      return {
        inhibitor: false,
        confidence: 0.3,
        probability: 0.2,
        method: 'local'
      };
    }

    let score = 0;
    let maxScore = 0;

    // Проверяем молекулярную массу (приблизительная оценка)
    if (rules.mw_threshold) {
      maxScore += 1;
      if (features.estimatedMW > rules.mw_threshold) {
        score += 1;
      }
    }

    // Проверяем количество ароматических колец
    if (rules.aromatic_rings_min) {
      maxScore += 1;
      if (features.aromaticRings >= rules.aromatic_rings_min) {
        score += 1;
      }
    }

    // Проверяем наличие азота
    if (rules.has_nitrogen) {
      maxScore += 1;
      if (features.hasNitrogen) {
        score += 1;
      }
    }

    // Проверяем наличие карбоксильной группы
    if (rules.has_carboxyl) {
      maxScore += 1;
      if (features.hasCarboxyl) {
        score += 1;
      }
    }

    const probability = maxScore > 0 ? score / maxScore : 0.3;
    const inhibitor = probability > 0.6;
    const confidence = Math.min(0.8, probability + 0.2); // Ограничиваем уверенность для локальных предсказаний

    return {
      inhibitor,
      confidence,
      probability,
      method: 'local'
    };
  }

  private predictBySupplement(supplementName: string, cyp: string): CypPrediction {
    // Эвристические правила на основе известных добавок
    const name = supplementName.toLowerCase();
    
    // Известные паттерны
    const knownInhibitors = {
      'CYP3A4': ['грейпфрут', 'зверобой', 'куркума', 'гинкго'],
      'CYP2C9': ['куркума', 'гинкго', 'чеснок'],
      'CYP2D6': ['куркума'],
      'CYP1A2': ['зеленый_чай', 'куркума'],
      'CYP2C19': ['зверобой', 'гинкго']
    };

    const inhibitorsList = knownInhibitors[cyp] || [];
    const isKnownInhibitor = inhibitorsList.some(inhibitor => 
      name.includes(inhibitor) || name.includes(inhibitor.replace('_', ' '))
    );

    if (isKnownInhibitor) {
      return {
        inhibitor: true,
        confidence: 0.7,
        probability: 0.8,
        method: 'database'
      };
    }

    // Общие правила для растительных экстрактов
    const plantKeywords = ['экстракт', 'extract', 'трава', 'herb', 'корень', 'root', 'лист', 'leaf'];
    const isPlantBased = plantKeywords.some(keyword => name.includes(keyword));

    if (isPlantBased) {
      return {
        inhibitor: false,
        confidence: 0.5,
        probability: 0.3,
        method: 'local'
      };
    }

    return {
      inhibitor: false,
      confidence: 0.4,
      probability: 0.2,
      method: 'local'
    };
  }

  private extractSimpleFeatures(smiles: string): {
    estimatedMW: number;
    aromaticRings: number;
    hasNitrogen: boolean;
    hasCarboxyl: boolean;
    hasSulfur: boolean;
  } {
    // Простой анализ SMILES без RDKit
    return {
      estimatedMW: smiles.length * 12, // Очень грубая оценка
      aromaticRings: (smiles.match(/c|C/g) || []).length / 6, // Примерная оценка
      hasNitrogen: smiles.includes('N') || smiles.includes('n'),
      hasCarboxyl: smiles.includes('C(=O)O') || smiles.includes('COOH'),
      hasSulfur: smiles.includes('S') || smiles.includes('s')
    };
  }

  private interpretPredictions(predictions: { [cyp: string]: CypPrediction | { error: string } }): {
    risk_level: 'high' | 'moderate' | 'low';
    high_risk_cyps: string[];
    moderate_risk_cyps: string[];
    interpretation: string;
  } {
    const highRiskCyps: string[] = [];
    const moderateRiskCyps: string[] = [];

    for (const [cyp, prediction] of Object.entries(predictions)) {
      if ('error' in prediction) continue;

      if (prediction.inhibitor && prediction.confidence > 0.8) {
        highRiskCyps.push(cyp);
      } else if (prediction.inhibitor && prediction.confidence > 0.6) {
        moderateRiskCyps.push(cyp);
      }
    }

    const riskLevel = highRiskCyps.length > 0 ? 'high' : 
                     moderateRiskCyps.length > 0 ? 'moderate' : 'low';

    const interpretation = this.generateInterpretation(highRiskCyps, moderateRiskCyps);

    return {
      risk_level: riskLevel,
      high_risk_cyps: highRiskCyps,
      moderate_risk_cyps: moderateRiskCyps,
      interpretation
    };
  }

  private generateInterpretation(highRiskCyps: string[], moderateRiskCyps: string[]): string {
    if (highRiskCyps.length > 0) {
      return `⚠️ ВЫСОКИЙ РИСК: Вероятно сильное ингибирование ${highRiskCyps.join(', ')}. Требуется осторожность с лекарствами.`;
    }
    
    if (moderateRiskCyps.length > 0) {
      return `⚡ УМЕРЕННЫЙ РИСК: Возможное ингибирование ${moderateRiskCyps.join(', ')}. Рекомендуется мониторинг.`;
    }
    
    return `✅ НИЗКИЙ РИСК: Минимальная вероятность клинически значимого ингибирования CYP450.`;
  }

  private getPotentialDrugInteractions(predictions: { [cyp: string]: CypPrediction | { error: string } }): Array<{
    drug: string;
    cyp: string;
    risk: string;
    severity: 'major' | 'moderate' | 'minor';
  }> {
    const interactions: Array<{
      drug: string;
      cyp: string;
      risk: string;
      severity: 'major' | 'moderate' | 'minor';
    }> = [];

    for (const [cyp, prediction] of Object.entries(predictions)) {
      if ('error' in prediction || !prediction.inhibitor) continue;

      const substrates = this.DRUG_SUBSTRATES[cyp] || [];
      
      for (const substrate of substrates) {
        // Определяем серьезность на основе уверенности предсказания и важности препарата
        let severity = substrate.severity;
        if (prediction.confidence < 0.7) {
          severity = severity === 'major' ? 'moderate' : 'minor';
        }

        interactions.push({
          drug: substrate.name,
          cyp,
          risk: `Ингибирование ${cyp} может повысить концентрацию препарата`,
          severity
        });
      }
    }

    // Сортируем по серьезности
    interactions.sort((a, b) => {
      const severityOrder = { 'major': 3, 'moderate': 2, 'minor': 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });

    return interactions;
  }
}