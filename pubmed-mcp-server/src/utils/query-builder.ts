export class PubMedQueryBuilder {
  /**
   * Build query for substance interactions
   */
  static buildInteractionQuery(
    substance1: string,
    substance2: string,
    options: {
      includeSupplements?: boolean;
      includeDrugs?: boolean;
      dateFrom?: string;
      dateTo?: string;
    } = {}
  ): string {
    const { includeSupplements = true, includeDrugs = true, dateFrom, dateTo } = options;

    // Base interaction terms
    const interactionTerms = [
      'interaction',
      'contraindication',
      'adverse effect',
      'drug interaction',
      'combination',
      'concurrent use'
    ];

    // Substance search terms (both MeSH and text words)
    const sub1Terms = this.buildSubstanceTerms(substance1, { includeSupplements, includeDrugs });
    const sub2Terms = this.buildSubstanceTerms(substance2, { includeSupplements, includeDrugs });

    // Interaction terms
    const interactionQuery = `(${interactionTerms.map(term => `"${term}"[tiab]`).join(' OR ')})`;

    // Combine all parts
    let query = `(${sub1Terms}) AND (${sub2Terms}) AND ${interactionQuery}`;

    // Add date range if specified
    if (dateFrom || dateTo) {
      const dateRange = this.buildDateRange(dateFrom, dateTo);
      query += ` AND ${dateRange}`;
    } else {
      // Default to last 10 years for relevance
      query += ' AND 2014:2024[pdat]';
    }

    // Prefer human studies
    query += ' AND (humans[mesh] OR clinical[tiab] OR patient[tiab])';

    return query;
  }

  /**
   * Build query for substance safety information
   */
  static buildSafetyQuery(
    substance: string,
    population: string = 'general',
    studyTypes: string[] = []
  ): string {
    const safetyTerms = [
      'safety',
      'toxicity',
      'adverse effects',
      'side effects',
      'contraindication',
      'overdose',
      'poisoning'
    ];

    const substanceTerms = this.buildSubstanceTerms(substance);
    const safetyQuery = `(${safetyTerms.map(term => `"${term}"[tiab]`).join(' OR ')})`;

    let query = `(${substanceTerms}) AND ${safetyQuery}`;

    // Add population-specific terms
    const populationTerms = this.getPopulationTerms(population);
    if (populationTerms) {
      query += ` AND ${populationTerms}`;
    }

    // Add study type filters
    if (studyTypes.length > 0) {
      const studyTypeQuery = studyTypes.map(type => `"${type}"[pt]`).join(' OR ');
      query += ` AND (${studyTypeQuery})`;
    }

    // Add date range (last 10 years)
    query += ' AND 2014:2024[pdat]';

    // Prefer human studies
    query += ' AND humans[mesh]';

    return query;
  }

  /**
   * Build query for dosage information
   */
  static buildDosageQuery(substance: string): string {
    const dosageTerms = [
      'dosage',
      'dose',
      'administration',
      'recommended daily allowance',
      'therapeutic dose',
      'maximum dose',
      'minimum dose',
      'bioavailability'
    ];

    const substanceTerms = this.buildSubstanceTerms(substance);
    const dosageQuery = `(${dosageTerms.map(term => `"${term}"[tiab]`).join(' OR ')})`;

    let query = `(${substanceTerms}) AND ${dosageQuery}`;

    // Prefer clinical trials and systematic reviews
    query += ' AND (clinical trial[pt] OR systematic review[pt] OR randomized controlled trial[pt])';

    // Add date range (last 5 years for most current recommendations)
    query += ' AND 2019:2024[pdat]';

    // Human studies only
    query += ' AND humans[mesh]';

    return query;
  }

  /**
   * Build comprehensive substance search terms
   */
  private static buildSubstanceTerms(
    substance: string,
    options: { includeSupplements?: boolean; includeDrugs?: boolean } = {}
  ): string {
    const { includeSupplements = true, includeDrugs = true } = options;

    // Clean and normalize substance name
    const cleanSubstance = substance.trim().toLowerCase();
    
    // Core search terms
    const terms: string[] = [
      `"${substance}"[tiab]`,
      `"${substance}"[mesh]`,
    ];

    // Add common variations and synonyms
    const variations = this.getSubstanceVariations(cleanSubstance);
    variations.forEach(variation => {
      terms.push(`"${variation}"[tiab]`);
    });

    // Add supplement-specific terms if enabled
    if (includeSupplements) {
      terms.push(`"${substance}"[Supplementary Concept]`);
      
      // Common supplement terms
      const supplementTerms = [
        `"${substance} supplement"[tiab]`,
        `"${substance} supplementation"[tiab]`,
      ];
      terms.push(...supplementTerms);
    }

    // Add drug-specific terms if enabled
    if (includeDrugs) {
      const drugTerms = [
        `"${substance}"[Substance Name]`,
        `"${substance}"[Pharmacological Action]`,
      ];
      terms.push(...drugTerms);
    }

    return terms.join(' OR ');
  }

  /**
   * Get common variations and synonyms for substances
   */
  private static getSubstanceVariations(substance: string): string[] {
    const variations: string[] = [];

    // Common vitamin variations
    const vitaminVariations: Record<string, string[]> = {
      'vitamin d': ['cholecalciferol', 'ergocalciferol', 'calcitriol', 'vitamin d3', 'vitamin d2'],
      'vitamin c': ['ascorbic acid', 'l-ascorbic acid', 'ascorbate'],
      'vitamin e': ['tocopherol', 'alpha-tocopherol', 'tocotrienol'],
      'vitamin k': ['phylloquinone', 'menaquinone', 'vitamin k1', 'vitamin k2'],
      'vitamin b12': ['cobalamin', 'cyanocobalamin', 'methylcobalamin'],
      'vitamin b6': ['pyridoxine', 'pyridoxal', 'pyridoxamine'],
      'folate': ['folic acid', 'pteroylglutamic acid', 'vitamin b9'],
      'niacin': ['nicotinic acid', 'nicotinamide', 'vitamin b3'],
    };

    // Common mineral variations
    const mineralVariations: Record<string, string[]> = {
      'calcium': ['calcium carbonate', 'calcium citrate', 'calcium phosphate'],
      'magnesium': ['magnesium oxide', 'magnesium citrate', 'magnesium glycinate'],
      'iron': ['ferrous sulfate', 'ferrous fumarate', 'ferric iron'],
      'zinc': ['zinc sulfate', 'zinc gluconate', 'zinc picolinate'],
    };

    // Check for vitamin variations
    for (const [key, vars] of Object.entries(vitaminVariations)) {
      if (substance.includes(key)) {
        variations.push(...vars);
      }
    }

    // Check for mineral variations
    for (const [key, vars] of Object.entries(mineralVariations)) {
      if (substance.includes(key)) {
        variations.push(...vars);
      }
    }

    return variations;
  }

  /**
   * Get population-specific search terms
   */
  private static getPopulationTerms(population: string): string | null {
    const populationTerms: Record<string, string> = {
      pregnancy: '(pregnancy[mesh] OR pregnant[tiab] OR prenatal[tiab] OR gestational[tiab])',
      pediatric: '(pediatric[mesh] OR child[mesh] OR children[tiab] OR infant[mesh] OR adolescent[mesh])',
      elderly: '(aged[mesh] OR elderly[tiab] OR geriatric[tiab] OR "older adult"[tiab])',
      general: '',
    };

    return populationTerms[population] || null;
  }

  /**
   * Build date range query
   */
  private static buildDateRange(dateFrom?: string, dateTo?: string): string {
    if (dateFrom && dateTo) {
      return `${dateFrom}:${dateTo}[pdat]`;
    } else if (dateFrom) {
      return `${dateFrom}:3000[pdat]`;
    } else if (dateTo) {
      return `1900:${dateTo}[pdat]`;
    }
    return '';
  }

  /**
   * Build general search query with advanced options
   */
  static buildGeneralQuery(
    query: string,
    options: {
      dateFrom?: string;
      dateTo?: string;
      studyTypes?: string[];
      maxResults?: number;
    } = {}
  ): string {
    const { dateFrom, dateTo, studyTypes } = options;

    let finalQuery = query;

    // Add study type filters
    if (studyTypes && studyTypes.length > 0) {
      const studyTypeQuery = studyTypes.map(type => `"${type}"[pt]`).join(' OR ');
      finalQuery += ` AND (${studyTypeQuery})`;
    }

    // Add date range
    if (dateFrom || dateTo) {
      const dateRange = this.buildDateRange(dateFrom, dateTo);
      finalQuery += ` AND ${dateRange}`;
    }

    // Prefer human studies by default
    if (!query.includes('humans[mesh]') && !query.includes('animals[mesh]')) {
      finalQuery += ' AND humans[mesh]';
    }

    return finalQuery;
  }
}