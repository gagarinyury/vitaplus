import { readFile } from 'fs/promises';
import { join } from 'path';

export interface CypEffect {
  action: 'none' | 'weak_inhibitor' | 'inhibitor' | 'weak_inducer' | 'inducer';
  strength?: 'weak' | 'moderate' | 'strong';
  confidence?: number;
  ic50?: number;
}

export interface SupplementData {
  aliases: string[];
  cyp_effects: {
    [key: string]: CypEffect;
  };
  safety_notes: string;
  references: string[];
}

export interface SafetyDatabase {
  supplements_cyp_data: {
    [supplement: string]: SupplementData;
  };
  drug_substrates: {
    [cyp: string]: string[];
  };
  interaction_severity: {
    [level: string]: {
      description: string;
      color: string;
    };
  };
}

export interface CypConflict {
  supplement1: string;
  supplement2: string;
  cyp_enzyme: string;
  conflict_type: string;
  severity: 'minor' | 'moderate' | 'major' | 'theoretical';
  description: string;
}

export interface DrugInteraction {
  drug: string;
  supplement: string;
  cyp_enzyme: string;
  mechanism: string;
  severity: 'minor' | 'moderate' | 'major' | 'theoretical';
  recommendation: string;
}

export interface SafetyAnalysisResult {
  safety_score: 'high' | 'moderate' | 'low';
  cyp_conflicts: CypConflict[];
  drug_interactions: DrugInteraction[];
  recommendations: string[];
  references: string[];
  summary: string;
}

export class SupplementSafetyChecker {
  private database: SafetyDatabase | null = null;
  private dataPath: string;

  constructor(dataPath?: string) {
    this.dataPath = dataPath || join(process.cwd(), 'data', 'supplement_cyp_database.json');
  }

  private async loadDatabase(): Promise<void> {
    if (this.database) return;
    
    try {
      const data = await readFile(this.dataPath, 'utf-8');
      this.database = JSON.parse(data);
    } catch (error) {
      throw new Error(`Failed to load supplement database: ${error.message}`);
    }
  }

  private normalizeSupplementName(name: string): string {
    return name.toLowerCase()
      .replace(/[^a-z0-9_]/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '');
  }

  private findSupplementByName(name: string): string | null {
    if (!this.database) return null;
    
    const normalized = this.normalizeSupplementName(name);
    
    // Direct match
    if (this.database.supplements_cyp_data[normalized]) {
      return normalized;
    }

    // Search in aliases
    for (const [suppName, data] of Object.entries(this.database.supplements_cyp_data)) {
      if (data.aliases.some(alias => 
        this.normalizeSupplementName(alias) === normalized
      )) {
        return suppName;
      }
    }

    return null;
  }

  private checkCypConflicts(supplement1: string, supplement2: string): CypConflict[] {
    if (!this.database) return [];

    const data1 = this.database.supplements_cyp_data[supplement1];
    const data2 = this.database.supplements_cyp_data[supplement2];
    
    if (!data1 || !data2) return [];

    const conflicts: CypConflict[] = [];

    // Check each CYP enzyme for conflicts
    const cypEnzymes = ['CYP1A2', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP2B6', 'CYP3A4'];

    for (const cyp of cypEnzymes) {
      const effect1 = data1.cyp_effects[cyp];
      const effect2 = data2.cyp_effects[cyp];

      if (!effect1 || !effect2) continue;

      // Check for conflicting effects
      const conflict = this.detectCypConflict(supplement1, supplement2, cyp, effect1, effect2);
      if (conflict) {
        conflicts.push(conflict);
      }
    }

    return conflicts;
  }

  private detectCypConflict(
    supplement1: string, 
    supplement2: string, 
    cyp: string, 
    effect1: CypEffect, 
    effect2: CypEffect
  ): CypConflict | null {
    // Inducer vs Inhibitor = conflict
    if ((effect1.action.includes('inducer') && effect2.action.includes('inhibitor')) ||
        (effect1.action.includes('inhibitor') && effect2.action.includes('inducer'))) {
      
      const severity = this.calculateConflictSeverity(effect1, effect2);
      
      return {
        supplement1,
        supplement2,
        cyp_enzyme: cyp,
        conflict_type: 'opposing_effects',
        severity,
        description: `${supplement1} ${effect1.action}s ${cyp} while ${supplement2} ${effect2.action}s it`
      };
    }

    // Multiple strong inhibitors = additive effect
    if (effect1.action.includes('inhibitor') && effect2.action.includes('inhibitor') &&
        (effect1.strength === 'strong' || effect2.strength === 'strong')) {
      
      return {
        supplement1,
        supplement2,
        cyp_enzyme: cyp,
        conflict_type: 'additive_inhibition',
        severity: 'moderate',
        description: `Combined inhibition of ${cyp} may be clinically significant`
      };
    }

    return null;
  }

  private calculateConflictSeverity(effect1: CypEffect, effect2: CypEffect): 'minor' | 'moderate' | 'major' | 'theoretical' {
    const confidence = Math.min(effect1.confidence || 0.5, effect2.confidence || 0.5);
    
    if (confidence < 0.7) return 'theoretical';
    
    const hasStrong = effect1.strength === 'strong' || effect2.strength === 'strong';
    const hasModerate = effect1.strength === 'moderate' || effect2.strength === 'moderate';
    
    if (hasStrong) return 'major';
    if (hasModerate) return 'moderate';
    return 'minor';
  }

  private checkDrugInteractions(supplements: string[], drugs: string[]): DrugInteraction[] {
    if (!this.database || !drugs.length) return [];

    const interactions: DrugInteraction[] = [];

    for (const supplement of supplements) {
      const suppData = this.database.supplements_cyp_data[supplement];
      if (!suppData) continue;

      for (const drug of drugs) {
        const drugInteractions = this.findDrugInteractions(supplement, drug, suppData);
        interactions.push(...drugInteractions);
      }
    }

    return interactions;
  }

  private findDrugInteractions(supplement: string, drug: string, suppData: SupplementData): DrugInteraction[] {
    if (!this.database) return [];

    const interactions: DrugInteraction[] = [];
    const normalizedDrug = this.normalizeSupplementName(drug);

    // Check each CYP enzyme
    for (const [cyp, effect] of Object.entries(suppData.cyp_effects)) {
      if (effect.action === 'none') continue;

      const substrates = this.database.drug_substrates[cyp] || [];
      const isSubstrate = substrates.some(substrate => 
        this.normalizeSupplementName(substrate) === normalizedDrug
      );

      if (isSubstrate) {
        const interaction = this.createDrugInteraction(supplement, drug, cyp, effect);
        interactions.push(interaction);
      }
    }

    return interactions;
  }

  private createDrugInteraction(supplement: string, drug: string, cyp: string, effect: CypEffect): DrugInteraction {
    let mechanism: string;
    let recommendation: string;
    let severity: 'minor' | 'moderate' | 'major' | 'theoretical';

    if (effect.action.includes('inhibitor')) {
      mechanism = `${supplement} inhibits ${cyp}, may increase ${drug} levels`;
      recommendation = `Monitor for increased ${drug} effects, consider dose reduction`;
    } else {
      mechanism = `${supplement} induces ${cyp}, may decrease ${drug} levels`;
      recommendation = `Monitor for reduced ${drug} effectiveness, consider dose increase`;
    }

    // Determine severity
    if (effect.strength === 'strong') {
      severity = 'major';
    } else if (effect.strength === 'moderate') {
      severity = 'moderate';
    } else if ((effect.confidence || 0.5) < 0.7) {
      severity = 'theoretical';
    } else {
      severity = 'minor';
    }

    return {
      drug,
      supplement,
      cyp_enzyme: cyp,
      mechanism,
      severity,
      recommendation
    };
  }

  private generateRecommendations(
    conflicts: CypConflict[], 
    drugInteractions: DrugInteraction[],
    supplements: string[]
  ): string[] {
    const recommendations: string[] = [];

    // General recommendations based on conflicts
    if (conflicts.length > 0) {
      const majorConflicts = conflicts.filter(c => c.severity === 'major');
      const moderateConflicts = conflicts.filter(c => c.severity === 'moderate');

      if (majorConflicts.length > 0) {
        recommendations.push('⚠️ MAJOR: Избегайте одновременного приема указанных комбинаций');
        recommendations.push('🕒 Разделяйте прием на 4-6 часов если возможно');
      }

      if (moderateConflicts.length > 0) {
        recommendations.push('⚡ Разделяйте прием добавок на 2-4 часа');
        recommendations.push('📊 Рекомендуется мониторинг эффектов');
      }
    }

    // Drug interaction recommendations
    if (drugInteractions.length > 0) {
      const majorDrugInteractions = drugInteractions.filter(i => i.severity === 'major');
      
      if (majorDrugInteractions.length > 0) {
        recommendations.push('🏥 ОБЯЗАТЕЛЬНО: Консультация с врачом перед началом приема');
        recommendations.push('🔬 Может потребоваться коррекция дозы препаратов');
      } else {
        recommendations.push('👨‍⚕️ Уведомите врача о приеме добавок');
      }
    }

    // Specific supplement recommendations
    if (supplements.includes('st_johns_wort')) {
      recommendations.push('🚨 Зверобой: мощное взаимодействие с большинством лекарств');
    }

    if (supplements.includes('kava')) {
      recommendations.push('⚠️ Кава: риск гепатотоксичности, избегайте с алкоголем');
    }

    // General safety recommendations
    if (supplements.length > 3) {
      recommendations.push('📋 При приеме >3 добавок рекомендуется консультация нутрициолога');
    }

    return recommendations;
  }

  private calculateSafetyScore(conflicts: CypConflict[], drugInteractions: DrugInteraction[]): 'high' | 'moderate' | 'low' {
    const majorIssues = conflicts.filter(c => c.severity === 'major').length +
                       drugInteractions.filter(i => i.severity === 'major').length;

    const moderateIssues = conflicts.filter(c => c.severity === 'moderate').length +
                          drugInteractions.filter(i => i.severity === 'moderate').length;

    if (majorIssues > 0) return 'low';
    if (moderateIssues > 1 || conflicts.length + drugInteractions.length > 3) return 'moderate';
    return 'high';
  }

  private generateSummary(
    supplements: string[], 
    conflicts: CypConflict[], 
    drugInteractions: DrugInteraction[],
    safetyScore: string
  ): string {
    const totalIssues = conflicts.length + drugInteractions.length;
    
    if (totalIssues === 0) {
      return `✅ Комбинация ${supplements.length} добавок выглядит безопасной. Известных значимых взаимодействий не обнаружено.`;
    }

    let summary = `⚖️ Анализ ${supplements.length} добавок: `;
    
    if (safetyScore === 'low') {
      summary += '🔴 ВЫСОКИЙ РИСК взаимодействий';
    } else if (safetyScore === 'moderate') {
      summary += '🟡 УМЕРЕННЫЙ РИСК взаимодействий';
    } else {
      summary += '🟢 НИЗКИЙ РИСК взаимодействий';
    }

    summary += `. Обнаружено: ${conflicts.length} конфликтов CYP450`;
    
    if (drugInteractions.length > 0) {
      summary += `, ${drugInteractions.length} взаимодействий с лекарствами`;
    }

    return summary;
  }

  async analyzeCombination(
    supplements: string[], 
    drugs: string[] = []
  ): Promise<SafetyAnalysisResult> {
    await this.loadDatabase();

    // Normalize and validate supplement names
    const normalizedSupplements: string[] = [];
    const unknownSupplements: string[] = [];

    for (const supplement of supplements) {
      const found = this.findSupplementByName(supplement);
      if (found) {
        normalizedSupplements.push(found);
      } else {
        unknownSupplements.push(supplement);
      }
    }

    if (unknownSupplements.length > 0) {
      throw new Error(`Unknown supplements: ${unknownSupplements.join(', ')}. Use PubMed search for more information.`);
    }

    // Check for conflicts between supplements
    const cypConflicts: CypConflict[] = [];
    for (let i = 0; i < normalizedSupplements.length; i++) {
      for (let j = i + 1; j < normalizedSupplements.length; j++) {
        const conflicts = this.checkCypConflicts(normalizedSupplements[i], normalizedSupplements[j]);
        cypConflicts.push(...conflicts);
      }
    }

    // Check drug interactions
    const drugInteractions = this.checkDrugInteractions(normalizedSupplements, drugs);

    // Generate recommendations
    const recommendations = this.generateRecommendations(cypConflicts, drugInteractions, normalizedSupplements);

    // Calculate safety score
    const safetyScore = this.calculateSafetyScore(cypConflicts, drugInteractions);

    // Generate summary
    const summary = this.generateSummary(normalizedSupplements, cypConflicts, drugInteractions, safetyScore);

    // Collect references
    const references: string[] = [];
    for (const supplement of normalizedSupplements) {
      const data = this.database?.supplements_cyp_data[supplement];
      if (data) {
        references.push(...data.references);
      }
    }

    return {
      safety_score: safetyScore,
      cyp_conflicts: cypConflicts,
      drug_interactions: drugInteractions,
      recommendations,
      references: [...new Set(references)], // Remove duplicates
      summary
    };
  }

  async getSupplementInfo(supplementName: string): Promise<SupplementData | null> {
    await this.loadDatabase();
    
    const found = this.findSupplementByName(supplementName);
    if (!found || !this.database) return null;
    
    return this.database.supplements_cyp_data[found];
  }

  async listAvailableSupplements(): Promise<string[]> {
    await this.loadDatabase();
    
    if (!this.database) return [];
    
    return Object.keys(this.database.supplements_cyp_data);
  }
}