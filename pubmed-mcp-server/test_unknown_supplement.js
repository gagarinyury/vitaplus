#!/usr/bin/env node

// Test that unknown supplements get ML predictions instead of empty profiles
const { AnalyzeSupplementsCompleteTool } = require('./dist/tools/analyze-supplements-complete.js');
const { PubMedClient } = require('./dist/utils/pubmed-client.js');

async function testUnknownSupplement() {
  console.log('🧪 Testing Unknown Supplement ML Fallback...\n');
  
  try {
    const baseUrl = process.env.PUBMED_API_BASE_URL || 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
    const apiKey = process.env.PUBMED_API_KEY;
    const rateLimit = parseInt(process.env.PUBMED_RATE_LIMIT_RPM || '600');
    const timeout = parseInt(process.env.PUBMED_TIMEOUT_MS || '30000');
    
    const pubmedClient = new PubMedClient(baseUrl, apiKey, rateLimit, timeout);
    const tool = new AnalyzeSupplementsCompleteTool(pubmedClient);
    
    // Test: Unknown supplement (quercetin) - should get ML prediction
    console.log('📝 Testing: Quercetin (unknown supplement)');
    try {
      const result = await tool.execute({
        supplements: ['quercetin'],
        include_timing: false,
        include_pubmed_search: false,  // Force database/ML path only
        detailed_analysis: false
      });
      
      console.log('✅ Test Success!');
      console.log('Supplement:', Object.keys(result.supplements_data)[0]);
      console.log('Data source:', result.supplements_data.quercetin.data_source);
      console.log('Confidence:', result.supplements_data.quercetin.confidence);
      
      // Check if we got actual data instead of empty profile
      if (result.supplements_data.quercetin.confidence > 0) {
        console.log('✅ ML prediction working - got confidence > 0');
        console.log('CYP3A4 action:', result.supplements_data.quercetin.cyp_profile.CYP3A4.action);
        console.log('CYP3A4 strength:', result.supplements_data.quercetin.cyp_profile.CYP3A4.strength);
      } else {
        console.log('❌ Still getting empty profile');
      }
      console.log('');
      
    } catch (error) {
      console.error('❌ Test failed:', error.message);
    }
    
  } catch (error) {
    console.error('❌ Tool initialization failed:', error.message);
  }
  
  console.log('🎉 Unknown supplement testing completed!');
}

if (require.main === module) {
  testUnknownSupplement().catch(console.error);
}