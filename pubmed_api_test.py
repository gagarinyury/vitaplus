#!/usr/bin/env python3
"""
PubMed API тест для поиска информации о БАДах и их взаимодействиях
Использует Entrez API от NCBI
"""

import requests
import xml.etree.ElementTree as ET
import json
import time
from urllib.parse import quote

# PubMed API endpoints
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Список БАДов для исследования
SUPPLEMENTS = [
    {"name": "Echinacea", "search_terms": ["echinacea", "echinacea purpurea"]},
    {"name": "Ginkgo", "search_terms": ["ginkgo biloba", "ginkgo"]},
    {"name": "St Johns Wort", "search_terms": ["hypericum perforatum", "st john's wort"]},
    {"name": "Ginseng", "search_terms": ["panax ginseng", "ginseng"]},
    {"name": "Garlic", "search_terms": ["allium sativum", "garlic"]},
    {"name": "Turmeric", "search_terms": ["curcuma longa", "turmeric", "curcumin"]},
    {"name": "Milk Thistle", "search_terms": ["silybum marianum", "milk thistle", "silymarin"]},
    {"name": "Saw Palmetto", "search_terms": ["serenoa repens", "saw palmetto"]},
    {"name": "Green Tea", "search_terms": ["camellia sinensis", "green tea", "EGCG"]},
    {"name": "Ashwagandha", "search_terms": ["withania somnifera", "ashwagandha"]}
]

def search_pubmed(query, retmax=10):
    """Поиск в PubMed по запросу"""
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': retmax,
        'retmode': 'xml',
        'usehistory': 'y'
    }
    
    try:
        response = requests.get(ESEARCH_URL, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        # Получаем общее количество результатов
        count_elem = root.find('Count')
        total_count = int(count_elem.text) if count_elem is not None else 0
        
        # Получаем ID статей
        id_list = []
        id_list_elem = root.find('IdList')
        if id_list_elem is not None:
            for id_elem in id_list_elem.findall('Id'):
                id_list.append(id_elem.text)
        
        # Получаем WebEnv и QueryKey для больших запросов
        webenv = root.find('WebEnv')
        query_key = root.find('QueryKey')
        
        return {
            'total_count': total_count,
            'ids': id_list,
            'webenv': webenv.text if webenv is not None else None,
            'query_key': query_key.text if query_key is not None else None
        }
        
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return None

def get_article_details(pmids):
    """Получение деталей статей по PMID"""
    if not pmids:
        return []
    
    params = {
        'db': 'pubmed',
        'id': ','.join(pmids),
        'retmode': 'xml'
    }
    
    try:
        response = requests.get(EFETCH_URL, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        articles = []
        
        for article in root.findall('.//PubmedArticle'):
            try:
                # Заголовок
                title_elem = article.find('.//ArticleTitle')
                title = title_elem.text if title_elem is not None else "Нет заголовка"
                
                # Абстракт
                abstract_elem = article.find('.//AbstractText')
                abstract = abstract_elem.text if abstract_elem is not None else "Нет абстракта"
                
                # Год публикации
                year_elem = article.find('.//PubDate/Year')
                year = year_elem.text if year_elem is not None else "Неизвестно"
                
                # PMID
                pmid_elem = article.find('.//PMID')
                pmid = pmid_elem.text if pmid_elem is not None else "Неизвестно"
                
                articles.append({
                    'pmid': pmid,
                    'title': title,
                    'abstract': abstract,
                    'year': year
                })
                
            except Exception as e:
                print(f"Ошибка обработки статьи: {e}")
                continue
        
        return articles
        
    except Exception as e:
        print(f"Ошибка получения деталей: {e}")
        return []

def search_supplement_interactions(supplement_name, search_terms):
    """Поиск взаимодействий для конкретного БАДа"""
    results = {}
    
    print(f"\n=== Исследуем {supplement_name} ===")
    
    # 1. Общий поиск по БАДу
    general_query = f"({' OR '.join([f'"{term}"' for term in search_terms])}) AND humans[MeSH]"
    general_results = search_pubmed(general_query, retmax=5)
    
    if general_results:
        results['general'] = {
            'total_count': general_results['total_count'],
            'query': general_query
        }
        print(f"Общих публикаций: {general_results['total_count']}")
        
        # Получаем детали нескольких статей
        if general_results['ids']:
            articles = get_article_details(general_results['ids'][:3])
            results['general']['sample_articles'] = articles
    
    # 2. Поиск взаимодействий с лекарствами
    interaction_query = f"({' OR '.join([f'"{term}"' for term in search_terms])}) AND (drug interactions[MeSH] OR herb-drug interactions[tw] OR drug interaction[tw]) AND humans[MeSH]"
    interaction_results = search_pubmed(interaction_query, retmax=5)
    
    if interaction_results:
        results['interactions'] = {
            'total_count': interaction_results['total_count'],
            'query': interaction_query
        }
        print(f"Публикаций о взаимодействиях: {interaction_results['total_count']}")
        
        # Получаем детали статей о взаимодействиях
        if interaction_results['ids']:
            articles = get_article_details(interaction_results['ids'][:2])
            results['interactions']['sample_articles'] = articles
    
    # 3. Поиск побочных эффектов
    adverse_query = f"({' OR '.join([f'"{term}"' for term in search_terms])}) AND (adverse effects[MeSH] OR side effects[tw] OR toxicity[MeSH]) AND humans[MeSH]"
    adverse_results = search_pubmed(adverse_query, retmax=3)
    
    if adverse_results:
        results['adverse_effects'] = {
            'total_count': adverse_results['total_count'],
            'query': adverse_query
        }
        print(f"Публикаций о побочных эффектах: {adverse_results['total_count']}")
    
    # Пауза между запросами (рекомендация NCBI)
    time.sleep(0.5)
    
    return results

def main():
    """Основная функция для тестирования API"""
    print("=== ТЕСТ PubMed API ===")
    print("Поиск информации о популярных БАДах...")
    
    all_results = {}
    
    # Тестируем несколько БАДов
    test_supplements = SUPPLEMENTS[:5]  # Первые 5 для теста
    
    for supplement in test_supplements:
        try:
            results = search_supplement_interactions(
                supplement['name'], 
                supplement['search_terms']
            )
            all_results[supplement['name']] = results
            
        except Exception as e:
            print(f"Ошибка с {supplement['name']}: {e}")
            continue
    
    # Сохраняем результаты
    with open('pubmed_api_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== ИТОГИ ===")
    print(f"Обработано БАДов: {len(all_results)}")
    print("Результаты сохранены в pubmed_api_results.json")
    
    # Показываем топ по количеству публикаций
    print("\nТОП по количеству публикаций:")
    for name, data in all_results.items():
        general_count = data.get('general', {}).get('total_count', 0)
        interaction_count = data.get('interactions', {}).get('total_count', 0)
        print(f"{name}: {general_count} общих, {interaction_count} о взаимодействиях")

if __name__ == "__main__":
    main()