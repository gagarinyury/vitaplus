# PubMed MCP Server

A Model Context Protocol (MCP) server that provides tools for searching and analyzing medical literature from PubMed. This server enables AI assistants like Claude to access scientific research data for drug interactions, safety information, and medical research.

## Features

### Available Tools

1. **search_pubmed** - Search PubMed for medical and scientific articles
2. **get_article_details** - Get detailed information for specific articles by PMID
3. **search_interactions** - Find drug-drug, drug-supplement, or supplement-supplement interactions
4. **search_safety** - Search for safety information, adverse effects, and contraindications

### Key Capabilities

- **Intelligent Query Building** - Automatically constructs optimized PubMed queries with MeSH terms
- **Rate Limiting** - Respects PubMed's API limits (3 requests/second)
- **Structured Data Extraction** - Parses XML responses into structured, usable data
- **Relevance Scoring** - Ranks results by relevance to the query
- **Safety Analysis** - Analyzes articles for interaction evidence and safety signals
- **Population-Specific Search** - Tailored searches for pregnancy, pediatric, elderly populations

## Installation

1. **Clone and setup:**
```bash
cd pubmed-mcp-server
npm install
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Build:**
```bash
npm run build
```

## Configuration

### Environment Variables

Create a `.env` file with the following settings:

```bash
# PubMed API Configuration
PUBMED_API_BASE_URL=https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
PUBMED_API_KEY=your_ncbi_api_key_here  # Optional but recommended

# Rate Limiting (requests per minute)
PUBMED_RATE_LIMIT_RPM=180

# Server Configuration
NODE_ENV=production
LOG_LEVEL=info

# Request Timeouts (milliseconds)
PUBMED_TIMEOUT_MS=30000
```

### NCBI API Key

While optional, getting an NCBI API key is recommended for:
- Higher rate limits (10 requests/second vs 3/second)
- More reliable service
- Priority access during high traffic

Get your free API key at: https://www.ncbi.nlm.nih.gov/account/settings/

## Usage

### Running the Server

```bash
# Development mode
npm run dev

# Production mode
npm start

# With custom configuration
PUBMED_API_KEY=your_key npm start
```

### Connecting to Claude

1. **Add to Claude Desktop configuration:**

```json
{
  "mcp_servers": {
    "pubmed": {
      "command": "node",
      "args": ["/path/to/pubmed-mcp-server/dist/index.js"],
      "env": {
        "PUBMED_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Test the connection:**
Ask Claude: "Search PubMed for vitamin D deficiency studies"

## Tool Documentation

### search_pubmed

Search PubMed for medical literature.

**Parameters:**
- `query` (string, required) - Search query using medical terms
- `maxResults` (number, optional) - Maximum articles to return (1-100, default: 20)
- `dateFrom` (string, optional) - Start date (YYYY or YYYY/MM or YYYY/MM/DD)
- `dateTo` (string, optional) - End date (YYYY or YYYY/MM or YYYY/MM/DD)
- `studyTypes` (array, optional) - Filter by study types

**Example:**
```javascript
{
  \"query\": \"vitamin D deficiency treatment\",
  \"maxResults\": 10,
  \"dateFrom\": \"2020\",
  \"studyTypes\": [\"randomized controlled trial\", \"systematic review\"]
}
```

### search_interactions

Search for substance interactions.

**Parameters:**
- `substance1` (string, required) - First substance
- `substance2` (string, required) - Second substance  
- `includeSupplements` (boolean, optional) - Include supplements (default: true)
- `includeDrugs` (boolean, optional) - Include drugs (default: true)

**Example:**
```javascript
{
  \"substance1\": \"warfarin\",
  \"substance2\": \"vitamin K\",
  \"includeSupplements\": true,
  \"includeDrugs\": true
}
```

### search_safety

Search for safety information about a substance.

**Parameters:**
- `substance` (string, required) - Substance to search
- `population` (string, optional) - Target population (general, pregnancy, pediatric, elderly)
- `studyTypes` (array, optional) - Study types to focus on

**Example:**
```javascript
{
  \"substance\": \"St. John's wort\",
  \"population\": \"pregnancy\",
  \"studyTypes\": [\"systematic review\", \"meta analysis\"]
}
```

### get_article_details

Get detailed information for specific articles.

**Parameters:**
- `pmids` (array, required) - Array of PubMed IDs (1-20 articles)

**Example:**
```javascript
{
  \"pmids\": [\"12345678\", \"87654321\"]
}
```

## Example Interactions

### Finding Drug Interactions

**User:** \"Are there any interactions between calcium and iron supplements?\"

**Claude with PubMed MCP:**
```
I'll search for interactions between calcium and iron supplements.

[Calls search_interactions tool]

Based on PubMed research, there IS a significant interaction between calcium and iron:

**Interaction Found:** YES
**Severity:** MODERATE  
**Type:** Antagonistic (absorption interference)

**Key Findings:**
- Calcium significantly reduces iron absorption when taken together
- Effect is dose-dependent - higher calcium doses cause greater interference  
- Mechanism: Competition for absorption pathways in the intestine

**Recommendations:**
- Take calcium and iron supplements at different times
- Separate by at least 2 hours
- Take iron on empty stomach when possible
- Consider taking vitamin C with iron to enhance absorption

**Evidence:** Based on 15 studies including 3 randomized controlled trials
```

### Safety Information Search

**User:** \"Is ashwagandha safe during pregnancy?\"

**Claude with PubMed MCP:**
```
[Calls search_safety tool with population: \"pregnancy\"]

**Safety Assessment for Ashwagandha During Pregnancy:**

**Overall Safety:** CAUTION ⚠️
**Risk Level:** MODERATE to HIGH
**Evidence Quality:** MODERATE

**Key Safety Concerns:**
- Limited human pregnancy data available
- Animal studies suggest potential reproductive effects
- May affect hormone levels
- Potential for uterine stimulation

**Recommendations:**
- AVOID during pregnancy due to insufficient safety data
- Consult healthcare provider before use
- Alternative stress-management approaches recommended

**Evidence:** Based on 8 relevant studies, mostly animal research and case reports
```

## Architecture

### Components

1. **PubMedClient** - Handles API communication with rate limiting
2. **XMLParser** - Processes PubMed XML responses into structured data
3. **QueryBuilder** - Constructs optimized search queries with MeSH terms
4. **Tools** - Individual MCP tools for different search types
5. **RateLimiter** - Ensures compliance with API limits

### Data Flow

```
Claude Request → MCP Tool → QueryBuilder → PubMed API → XMLParser → Structured Response → Claude
```

### Error Handling

- Automatic retry with exponential backoff
- Rate limit respect and queuing
- Graceful degradation on API failures
- Detailed error reporting

## Development

### Project Structure

```
src/
├── index.ts              # Main server entry point
├── types/
│   └── pubmed.ts        # TypeScript types and schemas
├── utils/
│   ├── pubmed-client.ts # PubMed API client
│   ├── xml-parser.ts    # XML response parser
│   ├── query-builder.ts # Query construction utilities
│   └── rate-limiter.ts  # Rate limiting implementation
└── tools/
    ├── search-pubmed.ts     # General PubMed search
    ├── search-interactions.ts # Interaction search
    ├── search-safety.ts     # Safety information search
    └── get-article-details.ts # Article details retrieval
```

### Adding New Tools

1. Create new tool class in `src/tools/`
2. Implement the tool interface with `getToolDefinition()` and `execute()`
3. Register in `src/index.ts`
4. Add appropriate types to `src/types/pubmed.ts`

### Testing

```bash
npm test
npm run lint
npm run type-check
```

## Performance

### Optimizations

- **Intelligent Caching** - Caches frequent queries to reduce API calls
- **Batch Processing** - Groups related requests when possible  
- **Query Optimization** - Uses MeSH terms and filters for precise results
- **Relevance Ranking** - Scores and sorts results by relevance

### Rate Limiting

- Respects PubMed's 3 requests/second limit (180/minute)
- Automatic backoff on rate limit hits
- Queue management for burst requests
- API key support for higher limits (10 req/sec)

## Troubleshooting

### Common Issues

**\"Rate limit exceeded\"**
- Solution: Wait 60 seconds or get NCBI API key
- Check: `PUBMED_RATE_LIMIT_RPM` setting

**\"Request timeout\"** 
- Solution: Increase `PUBMED_TIMEOUT_MS`
- Check: Network connectivity to NCBI

**\"No results found\"**
- Solution: Try broader search terms
- Check: Spelling and terminology
- Use: MeSH term browser for precise terms

**\"XML parsing error\"**
- Solution: Usually temporary - retry the request
- Check: PubMed API status page

### Debugging

Enable debug logging:
```bash
LOG_LEVEL=debug npm start
```

Check rate limit status:
```javascript
// The server logs rate limit status on startup
// Look for \"Rate limit status\" in console output
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines

- Follow TypeScript best practices
- Add tests for new features
- Update documentation
- Ensure rate limiting compliance
- Handle errors gracefully

## License

MIT License - see LICENSE file for details.

## Support

- **Issues:** Report bugs and feature requests on GitHub
- **Documentation:** Full API documentation in `/docs`
- **Examples:** Sample queries and use cases in `/examples`

## Related Projects

- **VitaPlus** - Supplement interaction checker using this MCP server
- **Claude Desktop** - AI assistant with MCP support
- **Model Context Protocol** - Open standard for AI tool integration

---

**Note:** This server provides access to scientific literature for informational purposes only. Always consult healthcare providers for medical advice.