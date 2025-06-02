#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Import our tools and utilities
import { PubMedClient } from './utils/pubmed-client.js';
import { SearchPubMedTool } from './tools/search-pubmed.js';
import { GetArticleDetailsTool } from './tools/get-article-details.js';
import { SearchInteractionsTool } from './tools/search-interactions.js';
import { SearchSafetyTool } from './tools/search-safety.js';
import { AnalyzeSupplementSafetyTool } from './tools/analyze-supplement-safety.js';
import { PredictCypInhibitionTool } from './tools/predict-cyp-inhibition.js';
import { AnalyzeSupplementsCompleteTool } from './tools/analyze-supplements-complete.js';

class PubMedMCPServer {
  private server: Server;
  private pubmedClient: PubMedClient;
  private tools: Map<string, any>;

  constructor() {
    // Initialize server
    this.server = new Server(
      {
        name: 'pubmed-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Initialize PubMed client
    const baseUrl = process.env.PUBMED_API_BASE_URL || 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
    const apiKey = process.env.PUBMED_API_KEY;
    const rateLimit = parseInt(process.env.PUBMED_RATE_LIMIT_RPM || '180');
    const timeout = parseInt(process.env.PUBMED_TIMEOUT_MS || '30000');

    this.pubmedClient = new PubMedClient(baseUrl, apiKey, rateLimit, timeout);

    // Initialize tools
    this.tools = new Map();
    this.initializeTools();

    // Set up request handlers
    this.setupHandlers();

    console.error('[PubMedMCPServer] Server initialized successfully');
    console.error(`[PubMedMCPServer] API URL: ${baseUrl}`);
    console.error(`[PubMedMCPServer] Rate limit: ${rateLimit} requests/minute`);
    console.error(`[PubMedMCPServer] API Key: ${apiKey ? 'Configured' : 'Not configured'}`);
  }

  private initializeTools(): void {
    // Create tool instances
    const searchPubMed = new SearchPubMedTool(this.pubmedClient);
    const getArticleDetails = new GetArticleDetailsTool(this.pubmedClient);
    const searchInteractions = new SearchInteractionsTool(this.pubmedClient);
    const searchSafety = new SearchSafetyTool(this.pubmedClient);
    const analyzeSupplementSafety = new AnalyzeSupplementSafetyTool();
    const predictCypInhibition = new PredictCypInhibitionTool();
    const analyzeSupplementsComplete = new AnalyzeSupplementsCompleteTool(this.pubmedClient);

    // Register tools
    this.tools.set('search_pubmed', searchPubMed);
    this.tools.set('get_article_details', getArticleDetails);
    this.tools.set('search_interactions', searchInteractions);
    this.tools.set('search_safety', searchSafety);
    this.tools.set('analyze_supplement_safety', analyzeSupplementSafety);
    this.tools.set('predict_cyp_inhibition', predictCypInhibition);
    this.tools.set('analyze_supplements_complete', analyzeSupplementsComplete);

    console.error(`[PubMedMCPServer] Registered ${this.tools.size} tools`);
  }

  private setupHandlers(): void {
    // Handle tool listing
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const tools = Array.from(this.tools.values()).map(tool => tool.getToolDefinition());
      
      console.error(`[PubMedMCPServer] Listing ${tools.length} available tools`);
      
      return {
        tools: tools,
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      console.error(`[PubMedMCPServer] Tool call: ${name}`);
      console.error(`[PubMedMCPServer] Arguments:`, JSON.stringify(args, null, 2));

      const tool = this.tools.get(name);
      if (!tool) {
        throw new Error(`Unknown tool: ${name}`);
      }

      try {
        const startTime = Date.now();
        const result = await tool.execute(args);
        const duration = Date.now() - startTime;
        
        console.error(`[PubMedMCPServer] Tool ${name} completed in ${duration}ms`);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        console.error(`[PubMedMCPServer] Tool ${name} failed:`, error);
        
        // Return error information
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                error: true,
                message: error instanceof Error ? error.message : 'Unknown error occurred',
                tool: name,
                timestamp: new Date().toISOString(),
              }, null, 2),
            },
          ],
          isError: true,
        };
      }
    });

    // Error handling
    this.server.onerror = (error) => {
      console.error('[PubMedMCPServer] Server error:', error);
    };

    process.on('SIGINT', async () => {
      console.error('[PubMedMCPServer] Shutting down...');
      await this.server.close();
      process.exit(0);
    });
  }

  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    
    console.error('[PubMedMCPServer] Starting server...');
    
    await this.server.connect(transport);
    
    console.error('[PubMedMCPServer] Server started and listening for requests');
  }

  async healthCheck(): Promise<boolean> {
    try {
      // Test the PubMed API connection
      const status = await this.pubmedClient.getRateLimitStatus();
      console.error('[PubMedMCPServer] Health check passed');
      console.error('[PubMedMCPServer] Rate limit status:', status);
      return true;
    } catch (error) {
      console.error('[PubMedMCPServer] Health check failed:', error);
      return false;
    }
  }
}

// Main execution
async function main() {
  console.error('PubMed MCP Server v1.0.0');
  console.error('Providing tools for PubMed API integration with Claude AI');
  console.error('=====================================');

  try {
    const server = new PubMedMCPServer();
    
    // Perform health check
    const healthy = await server.healthCheck();
    if (!healthy) {
      console.error('[Main] Health check failed - server may not function properly');
    }

    // Start the server
    await server.start();
  } catch (error) {
    console.error('[Main] Failed to start server:', error);
    process.exit(1);
  }
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('[Main] Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('[Main] Unhandled rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Start the server
if (require.main === module) {
  main().catch(error => {
    console.error('[Main] Startup error:', error);
    process.exit(1);
  });
}