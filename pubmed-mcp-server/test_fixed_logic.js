#!/usr/bin/env node

// Test the fixed data source logic
const { AnalyzeSupplementsCompleteTool } = require('./dist/tools/analyze-supplements-complete.js');
const { PubMedClient } = require('./dist/utils/pubmed-client.js');

async function testFixedLogic() {
  console.log('🔧 Testing Fixed Data Source Logic...\n');
  
  try {
    const baseUrl = process.env.PUBMED_API_BASE_URL || 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
    const apiKey = process.env.PUBMED_API_KEY;
    const rateLimit = parseInt(process.env.PUBMED_RATE_LIMIT_RPM || '600');
    const timeout = parseInt(process.env.PUBMED_TIMEOUT_MS || '30000');
    
    const pubmedClient = new PubMedClient(baseUrl, apiKey, rateLimit, timeout);
    const tool = new AnalyzeSupplementsCompleteTool(pubmedClient);
    
    // Test 1: Curcumin with ML fallback (no PubMed)
    console.log('📝 Test 1: Curcumin with ML fallback');
    try {
      const result1 = await tool.execute({
        supplements: ['curcumin'],
        include_timing: false,
        include_pubmed_search: false,  // Force ML path
        detailed_analysis: false
      });
      
      console.log('✅ Test 1 Success!');
      console.log('Data source:', result1.supplements_data.curcumin.data_source);
      console.log('Confidence:', result1.supplements_data.curcumin.confidence);
      console.log('CYP3A4 action:', result1.supplements_data.curcumin.cyp_profile.CYP3A4.action);
      console.log('');
      
    } catch (error) {
      console.error('❌ Test 1 failed:', error.message);
    }
    
    // Test 2: Known supplement from database (turmeric)
    console.log('📝 Test 2: Turmeric from database');
    try {
      const result2 = await tool.execute({
        supplements: ['turmeric'],
        include_timing: false,
        include_pubmed_search: false,
        detailed_analysis: false
      });
      
      console.log('✅ Test 2 Success!');
      console.log('Data source:', result2.supplements_data.turmeric.data_source);
      console.log('Confidence:', result2.supplements_data.turmeric.confidence);
      console.log('');
      
    } catch (error) {
      console.error('❌ Test 2 failed:', error.message);
    }
    
    // Test 3: Multiple supplements with timing
    console.log('📝 Test 3: Multiple supplements with timing');
    try {
      const result3 = await tool.execute({
        supplements: ['curcumin', 'ashwagandha'],
        include_timing: true,
        include_pubmed_search: false,
        detailed_analysis: false
      });
      
      console.log('✅ Test 3 Success!');
      console.log('Safety score:', result3.analysis_summary.safety_score);
      console.log('Morning supplements:', result3.timing_recommendations?.morning?.map(t => t.supplement));
      console.log('Evening supplements:', result3.timing_recommendations?.evening?.map(t => t.supplement));
      console.log('');
      
    } catch (error) {
      console.error('❌ Test 3 failed:', error.message);
    }
    
  } catch (error) {
    console.error('❌ Tool initialization failed:', error.message);
  }
  
  console.log('🎉 Fixed logic testing completed!');
}

if (require.main === module) {
  testFixedLogic().catch(console.error);
}