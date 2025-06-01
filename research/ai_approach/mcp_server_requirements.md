# Требования для создания MCP сервера для PubMed

## Что такое MCP сервер

Model Context Protocol (MCP) - это протокол от Anthropic для стандартизации взаимодействия AI с внешними системами через инструменты (tools).

## Основные компоненты MCP сервера

### 1. Манифест сервера
```json
{
  "name": "pubmed-mcp-server",
  "version": "1.0.0",
  "description": "MCP server for PubMed API interactions",
  "tools": [
    {
      "name": "search_pubmed",
      "description": "Search PubMed for articles about substance interactions"
    },
    {
      "name": "get_article_details", 
      "description": "Get detailed information about specific articles"
    }
  ]
}
```

### 2. Инструменты (Tools) которые нужно реализовать

#### search_pubmed
```typescript
interface SearchPubMedTool {
  name: "search_pubmed";
  parameters: {
    query: string;           // Поисковый запрос
    max_results?: number;    // Максимум результатов (по умолчанию 20)
    date_from?: string;      // Дата начала (YYYY/MM/DD)
    date_to?: string;        // Дата окончания (YYYY/MM/DD)
    study_types?: string[];  // Типы исследований ['clinical trial', 'meta analysis']
  };
  returns: {
    total_found: number;
    articles: Array<{
      pmid: string;
      title: string;
      authors: string[];
      journal: string;
      publication_date: string;
      abstract: string;
      mesh_terms: string[];
      doi?: string;
    }>;
  };
}
```

#### get_article_details
```typescript
interface GetArticleDetailsTool {
  name: "get_article_details";
  parameters: {
    pmids: string[];  // Массив PubMed ID
  };
  returns: {
    articles: Array<{
      pmid: string;
      full_abstract: string;
      mesh_terms: string[];
      keywords: string[];
      references: string[];
      funding_info?: string;
      conflict_of_interest?: string;
    }>;
  };
}
```

#### search_interactions
```typescript
interface SearchInteractionsTool {
  name: "search_interactions";
  parameters: {
    substance1: string;
    substance2: string;
    interaction_types?: string[];  // ['drug-drug', 'drug-supplement', 'supplement-supplement']
  };
  returns: {
    interactions_found: boolean;
    relevant_articles: Array<{
      pmid: string;
      title: string;
      interaction_description: string;
      severity_mentioned: string;
      evidence_level: string;
    }>;
  };
}
```

### 3. Технические требования

#### Зависимости
```json
{
  "dependencies": {
    "@anthropic-ai/mcp-sdk": "^0.1.0",
    "node-fetch": "^3.0.0",
    "xml2js": "^0.4.23",
    "rate-limiter-flexible": "^2.4.0"
  }
}
```

#### Структура проекта
```
pubmed-mcp-server/
├── src/
│   ├── index.ts              # Основной файл сервера
│   ├── pubmed-client.ts      # Клиент для PubMed API
│   ├── tools/
│   │   ├── search-pubmed.ts
│   │   ├── get-article.ts
│   │   └── search-interactions.ts
│   └── utils/
│       ├── rate-limiter.ts
│       ├── xml-parser.ts
│       └── query-builder.ts
├── package.json
├── tsconfig.json
└── README.md
```

### 4. Конфигурация

#### Переменные окружения
```bash
# .env
PUBMED_API_BASE_URL=https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
PUBMED_API_KEY=your_ncbi_api_key  # Опционально, для больших лимитов
RATE_LIMIT_RPM=180               # 3 запроса в секунду = 180 в минуту
MCP_SERVER_PORT=3000
```

#### Настройки rate limiting
```typescript
const rateLimiter = new RateLimiterFlexible({
  keyPrefix: 'pubmed_api',
  points: 3,        // 3 запроса
  duration: 1,      // за 1 секунду
  blockDuration: 1, // блокировка на 1 секунду при превышении
});
```

## Реализация основных функций

### 1. PubMed API клиент
```typescript
class PubMedClient {
  private baseUrl = process.env.PUBMED_API_BASE_URL;
  private apiKey = process.env.PUBMED_API_KEY;
  
  async search(query: string, maxResults: number = 20): Promise<SearchResult> {
    // Поиск через esearch.fcgi
    const searchUrl = `${this.baseUrl}esearch.fcgi`;
    const params = new URLSearchParams({
      db: 'pubmed',
      term: query,
      retmode: 'json',
      retmax: maxResults.toString(),
      ...(this.apiKey && { api_key: this.apiKey })
    });
    
    const response = await fetch(`${searchUrl}?${params}`);
    return response.json();
  }
  
  async fetchArticles(pmids: string[]): Promise<ArticleData[]> {
    // Получение деталей через efetch.fcgi
    const fetchUrl = `${this.baseUrl}efetch.fcgi`;
    const params = new URLSearchParams({
      db: 'pubmed',
      id: pmids.join(','),
      retmode: 'xml',
      rettype: 'abstract',
      ...(this.apiKey && { api_key: this.apiKey })
    });
    
    const response = await fetch(`${fetchUrl}?${params}`);
    const xmlData = await response.text();
    return this.parseXMLToArticles(xmlData);
  }
}
```

### 2. Построение умных запросов
```typescript
class QueryBuilder {
  static buildInteractionQuery(substance1: string, substance2: string): string {
    const interactions = ['interaction', 'contraindication', 'adverse effect'];
    const timeLimit = '2019:2024[pdat]'; // Последние 5 лет
    
    return `(${substance1}[mesh] OR "${substance1}"[tiab]) AND (${substance2}[mesh] OR "${substance2}"[tiab]) AND (${interactions.join(' OR ')}) AND ${timeLimit}`;
  }
  
  static buildSafetyQuery(substance: string): string {
    const safetyTerms = ['safety', 'toxicity', 'adverse effects', 'side effects'];
    return `${substance}[mesh] AND (${safetyTerms.join(' OR ')}) AND systematic review[pt]`;
  }
}
```

### 3. Парсинг XML ответов
```typescript
import xml2js from 'xml2js';

class XMLParser {
  static async parseArticlesXML(xmlData: string): Promise<ArticleData[]> {
    const parser = new xml2js.Parser();
    const result = await parser.parseStringPromise(xmlData);
    
    const articles = result.PubmedArticleSet?.PubmedArticle || [];
    
    return articles.map(article => ({
      pmid: article.MedlineCitation[0].PMID[0]._,
      title: article.MedlineCitation[0].Article[0].ArticleTitle[0],
      authors: this.extractAuthors(article),
      journal: article.MedlineCitation[0].Article[0].Journal[0].Title[0],
      abstract: this.extractAbstract(article),
      meshTerms: this.extractMeshTerms(article),
      publicationDate: this.extractPubDate(article)
    }));
  }
}
```

## Интеграция с AI

### Промпт для использования MCP сервера
```
У тебя есть доступ к MCP серверу для PubMed. Используй следующие инструменты:

1. search_pubmed - для поиска статей
2. get_article_details - для получения полной информации 
3. search_interactions - для поиска взаимодействий

ВСЕГДА используй эти инструменты перед анализом взаимодействий.
НИКОГДА не придумывай данные - только на основе найденных статей.
```

### Пример использования в Claude
```typescript
// Claude будет автоматически вызывать эти функции:
const searchResults = await tools.search_interactions({
  substance1: "Vitamin D",
  substance2: "Calcium"
});

const articleDetails = await tools.get_article_details({
  pmids: searchResults.relevant_articles.map(a => a.pmid).slice(0, 5)
});
```

## Деплой и использование

### 1. Локальный запуск
```bash
npm install
npm run build
npm start
```

### 2. Подключение к Claude
```json
{
  "mcp_servers": {
    "pubmed": {
      "url": "http://localhost:3000",
      "tools": ["search_pubmed", "get_article_details", "search_interactions"]
    }
  }
}
```

### 3. Мониторинг
- Логирование всех API вызовов
- Метрики производительности  
- Алерты при превышении rate limits
- Статистика использования инструментов

## Преимущества MCP подхода

1. **Стандартизация**: Унифицированный интерфейс для AI
2. **Переиспользование**: Сервер можно использовать в других проектах
3. **Изоляция**: Логика работы с PubMed отделена от AI логики
4. **Масштабируемость**: Легко добавлять новые инструменты
5. **Тестируемость**: Каждый инструмент можно тестировать отдельно

## Время реализации

- **MCP сервер**: 3-5 дней
- **Базовые инструменты**: 2-3 дня  
- **Интеграция с AI**: 1-2 дня
- **Тестирование**: 2-3 дня

**Итого**: 8-13 дней для полнофункционального MCP сервера