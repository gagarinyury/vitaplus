import xml2js from 'xml2js';
import { ProcessedArticle, PubMedArticleSchema } from '../types/pubmed.js';

export class PubMedXMLParser {
  private parser: xml2js.Parser;

  constructor() {
    this.parser = new xml2js.Parser({
      explicitArray: true,
      mergeAttrs: false,
      explicitCharkey: true,
      charkey: '_',
      attrkey: '$',
    });
  }

  async parseArticlesXML(xmlData: string): Promise<ProcessedArticle[]> {
    try {
      if (xmlData.length < 100) {
        return [];
      }
      
      const result = await this.parser.parseStringPromise(xmlData);
      
      if (!result.PubmedArticleSet?.PubmedArticle) {
        return [];
      }

      const articles = result.PubmedArticleSet.PubmedArticle;
      
      return articles
        .map((article: any) => this.parseArticle(article))
        .filter((article: ProcessedArticle | null) => article !== null) as ProcessedArticle[];
    } catch (error) {
      process.stderr.write(`Error parsing PubMed XML: ${error}\n`);
      throw new Error(`Failed to parse PubMed XML response: ${error}`);
    }
  }

  private parseArticle(articleData: any): ProcessedArticle | null {
    try {
      if (!articleData.MedlineCitation || !Array.isArray(articleData.MedlineCitation)) {
        return null;
      }
      
      const medlineCitation = articleData.MedlineCitation[0];
      const article = medlineCitation.Article[0];

      // Extract PMID
      const pmid = medlineCitation.PMID[0]._;

      // Extract title (handle both string and object cases)
      const titleRaw = article.ArticleTitle[0];
      const title = typeof titleRaw === 'string' ? titleRaw : (titleRaw?._ || 'No Title');

      // Extract authors
      const authors = this.extractAuthors(article);

      // Extract journal
      const journal = typeof article.Journal[0].Title[0] === 'string' 
        ? article.Journal[0].Title[0] 
        : article.Journal[0].Title[0]._ || 'Unknown Journal';

      // Extract abstract
      const abstract = this.extractAbstract(article);

      // Extract MeSH terms
      const meshTerms = this.extractMeshTerms(medlineCitation);

      // Extract publication date
      const publicationDate = this.extractPublicationDate(medlineCitation);

      // Extract publication types
      const publicationTypes = this.extractPublicationTypes(article);

      return {
        pmid,
        title,
        authors,
        journal,
        publicationDate,
        abstract,
        meshTerms,
        publicationTypes,
      };
    } catch (error) {
      process.stderr.write(`Failed to parse individual article: ${error}\n`);
      return null;
    }
  }

  private extractAuthors(article: any): string[] {
    try {
      if (!article.AuthorList?.[0]?.Author) {
        return [];
      }

      return article.AuthorList[0].Author.map((author: any) => {
        const lastName = typeof author.LastName?.[0] === 'string' ? author.LastName[0] : author.LastName?.[0]?._ || '';
        const foreName = typeof author.ForeName?.[0] === 'string' ? author.ForeName[0] : author.ForeName?.[0]?._ || '';
        const initials = typeof author.Initials?.[0] === 'string' ? author.Initials[0] : author.Initials?.[0]?._ || '';
        
        if (lastName && foreName) {
          return `${lastName} ${foreName}`;
        } else if (lastName && initials) {
          return `${lastName} ${initials}`;
        } else if (lastName) {
          return lastName;
        }
        return 'Unknown Author';
      }).filter((name: string) => name !== 'Unknown Author');
    } catch (error) {
      return [];
    }
  }

  private extractAbstract(article: any): string {
    try {
      if (!article.Abstract?.[0]?.AbstractText) {
        return '';
      }

      const abstractTexts = article.Abstract[0].AbstractText;
      
      if (Array.isArray(abstractTexts)) {
        return abstractTexts
          .map((text: any) => {
            if (typeof text === 'string') {
              return text;
            } else if (text._ && typeof text._ === 'string') {
              return text._;
            } else if (text.$?.Label && text._) {
              return `${text.$.Label}: ${text._}`;
            }
            return '';
          })
          .filter(Boolean)
          .join(' ');
      }
      
      return '';
    } catch (error) {
      return '';
    }
  }

  private extractMeshTerms(medlineCitation: any): string[] {
    try {
      if (!medlineCitation.MeshHeadingList?.[0]?.MeshHeading) {
        return [];
      }

      return medlineCitation.MeshHeadingList[0].MeshHeading
        .map((meshHeading: any) => {
          return meshHeading.DescriptorName?.[0]?._ || '';
        })
        .filter(Boolean);
    } catch (error) {
      return [];
    }
  }

  private extractPublicationDate(medlineCitation: any): string {
    try {
      if (medlineCitation.DateCompleted?.[0]) {
        const dateCompleted = medlineCitation.DateCompleted[0];
        const year = dateCompleted.Year?.[0] || '';
        const month = dateCompleted.Month?.[0] || '';
        const day = dateCompleted.Day?.[0] || '';
        
        if (year && month && day) {
          return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        } else if (year && month) {
          return `${year}-${month.padStart(2, '0')}`;
        } else if (year) {
          return year;
        }
      }
      
      // Fallback to other date fields if available
      return '';
    } catch (error) {
      return '';
    }
  }

  private extractPublicationTypes(article: any): string[] {
    try {
      if (!article.PublicationTypeList?.[0]?.PublicationType) {
        return [];
      }

      return article.PublicationTypeList[0].PublicationType
        .map((pubType: any) => {
          if (typeof pubType === 'string') {
            return pubType;
          } else if (pubType._) {
            return pubType._;
          }
          return '';
        })
        .filter(Boolean);
    } catch (error) {
      return [];
    }
  }
}