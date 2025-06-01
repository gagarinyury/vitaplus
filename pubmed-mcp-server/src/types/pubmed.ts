import { z } from 'zod';

// PubMed API Response Types
export const PubMedSearchResultSchema = z.object({
  esearchresult: z.object({
    count: z.string(),
    retmax: z.string(),
    retstart: z.string(),
    idlist: z.array(z.string()),
    translationset: z.array(z.any()).optional(),
    querytranslation: z.string().optional(),
  }),
});

export const PubMedAuthorSchema = z.object({
  LastName: z.array(z.string()).optional(),
  ForeName: z.array(z.string()).optional(),
  Initials: z.array(z.string()).optional(),
  AffiliationInfo: z.array(z.any()).optional(),
});

export const PubMedArticleSchema = z.object({
  MedlineCitation: z.array(z.object({
    PMID: z.array(z.object({
      _: z.string(),
      $: z.object({
        Version: z.string(),
      }),
    })),
    Article: z.array(z.object({
      ArticleTitle: z.array(z.string()),
      Abstract: z.array(z.object({
        AbstractText: z.array(z.any()).optional(),
      })).optional(),
      AuthorList: z.array(z.object({
        Author: z.array(PubMedAuthorSchema).optional(),
      })).optional(),
      Journal: z.array(z.object({
        Title: z.array(z.any()),
        ISOAbbreviation: z.array(z.any()).optional(),
      })),
      PublicationTypeList: z.array(z.object({
        PublicationType: z.array(z.any()).optional(),
      })).optional(),
    })),
    MeshHeadingList: z.array(z.object({
      MeshHeading: z.array(z.object({
        DescriptorName: z.array(z.object({
          _: z.string(),
          $: z.object({
            UI: z.string(),
            MajorTopicYN: z.string(),
          }),
        })),
      })).optional(),
    })).optional(),
    DateCompleted: z.array(z.object({
      Year: z.array(z.string()),
      Month: z.array(z.string()),
      Day: z.array(z.string()),
    })).optional(),
  })),
});

// Processed Article Types
export interface ProcessedArticle {
  pmid: string;
  title: string;
  authors: string[];
  journal: string;
  publicationDate: string;
  abstract: string;
  meshTerms: string[];
  doi?: string;
  publicationTypes: string[];
}

export interface InteractionSearchResult {
  found: boolean;
  totalResults: number;
  articles: ProcessedArticle[];
  searchQuery: string;
  interactionType?: string;
  severity?: string;
}

export interface SubstanceInfo {
  name: string;
  meshTerms: string[];
  synonyms: string[];
}

// MCP Tool Parameters
export const SearchPubMedParamsSchema = z.object({
  query: z.string().min(1, "Query cannot be empty"),
  maxResults: z.number().min(1).max(100).default(20),
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  studyTypes: z.array(z.string()).optional(),
});

export const GetArticleDetailsParamsSchema = z.object({
  pmids: z.array(z.string()).min(1, "At least one PMID required").max(20, "Maximum 20 PMIDs allowed"),
});

export const SearchInteractionsParamsSchema = z.object({
  substance1: z.string().min(1, "Substance1 cannot be empty"),
  substance2: z.string().min(1, "Substance2 cannot be empty"),
  interactionTypes: z.array(z.string()).optional(),
  includeSupplements: z.boolean().default(true),
  includeDrugs: z.boolean().default(true),
});

export const SearchSafetyParamsSchema = z.object({
  substance: z.string().min(1, "Substance cannot be empty"),
  population: z.enum(['general', 'pregnancy', 'pediatric', 'elderly']).default('general'),
  studyTypes: z.array(z.string()).optional(),
});

export type SearchPubMedParams = z.infer<typeof SearchPubMedParamsSchema>;
export type GetArticleDetailsParams = z.infer<typeof GetArticleDetailsParamsSchema>;
export type SearchInteractionsParams = z.infer<typeof SearchInteractionsParamsSchema>;
export type SearchSafetyParams = z.infer<typeof SearchSafetyParamsSchema>;
export type PubMedSearchResult = z.infer<typeof PubMedSearchResultSchema>;

// Error Types
export class PubMedAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public pubmedError?: string
  ) {
    super(message);
    this.name = 'PubMedAPIError';
  }
}

export class RateLimitError extends Error {
  constructor(message: string, public retryAfter?: number) {
    super(message);
    this.name = 'RateLimitError';
  }
}