#!/usr/bin/env python3
"""
Полный анализ топ-20 БАДов через PubMed API
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def search_pubmed(query, retmax=10):
    """Поиск в PubMed"""
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': str(retmax),
        'retmode': 'xml'
    }
    
    url = ESEARCH_URL + '?' + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
        
        root = ET.fromstring(content)
        count_elem = root.find('Count')
        total_count = int(count_elem.text) if count_elem is not None else 0
        
        id_list = []
        id_list_elem = root.find('IdList')
        if id_list_elem is not None:
            for id_elem in id_list_elem.findall('Id'):
                id_list.append(id_elem.text)
        
        return {'total_count': total_count, 'ids': id_list}
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return {'total_count': 0, 'ids': []}

def get_abstracts(pmids):
    """Получение абстрактов"""
    if not pmids:
        return []
    
    params = {
        'db': 'pubmed',
        'id': ','.join(pmids[:3]),  # Берем только первые 3
        'retmode': 'xml'
    }
    
    url = EFETCH_URL + '?' + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
        
        root = ET.fromstring(content)
        abstracts = []
        
        for article in root.findall('.//PubmedArticle'):
            title_elem = article.find('.//ArticleTitle')
            abstract_elem = article.find('.//AbstractText')
            year_elem = article.find('.//PubDate/Year')
            pmid_elem = article.find('.//PMID')
            
            if title_elem is not None and abstract_elem is not None:
                abstracts.append({
                    'pmid': pmid_elem.text if pmid_elem is not None else '',
                    'title': title_elem.text or '',
                    'abstract': abstract_elem.text or '',
                    'year': year_elem.text if year_elem is not None else ''
                })
        
        return abstracts
        
    except Exception as e:
        print(f"Ошибка получения абстрактов: {e}")
        return []

def analyze_supplement(name, search_terms):
    """Полный анализ БАДа"""
    print(f"\n🔍 Анализируем {name}...")
    
    results = {'name': name, 'search_terms': search_terms}
    
    # 1. Общий поиск
    general_query = f"({' OR '.join(search_terms)}) AND humans[MeSH]"
    general_result = search_pubmed(general_query)
    results['general'] = {
        'count': general_result['total_count'],
        'query': general_query
    }
    
    # 2. Взаимодействия с лекарствами
    interaction_query = f"({' OR '.join(search_terms)}) AND (drug interactions[MeSH] OR herb-drug interactions[tw]) AND humans[MeSH]"
    interaction_result = search_pubmed(interaction_query)
    results['interactions'] = {
        'count': interaction_result['total_count'],
        'query': interaction_query
    }
    
    # 3. Побочные эффекты
    adverse_query = f"({' OR '.join(search_terms)}) AND (adverse effects[MeSH] OR side effects[tw]) AND humans[MeSH]"
    adverse_result = search_pubmed(adverse_query)
    results['adverse_effects'] = {
        'count': adverse_result['total_count'],
        'query': adverse_query
    }
    
    # 4. Клинические испытания
    rct_query = f"({' OR '.join(search_terms)}) AND (randomized controlled trial[pt] OR clinical trial[pt]) AND humans[MeSH]"
    rct_result = search_pubmed(rct_query)
    results['clinical_trials'] = {
        'count': rct_result['total_count'],
        'query': rct_query
    }
    
    # 5. Получаем примеры абстрактов о взаимодействиях
    if interaction_result['ids']:
        interaction_abstracts = get_abstracts(interaction_result['ids'])
        results['sample_interactions'] = interaction_abstracts
    
    # Расчет процентов
    total = results['general']['count']
    if total > 0:
        results['interaction_percentage'] = round(results['interactions']['count'] / total * 100, 1)
        results['adverse_percentage'] = round(results['adverse_effects']['count'] / total * 100, 1)
        results['rct_percentage'] = round(results['clinical_trials']['count'] / total * 100, 1)
    
    print(f"  📊 Всего: {total:,}")
    print(f"  ⚠️  Взаимодействия: {results['interactions']['count']:,} ({results.get('interaction_percentage', 0)}%)")
    print(f"  🚨 Побочные эффекты: {results['adverse_effects']['count']:,} ({results.get('adverse_percentage', 0)}%)")
    print(f"  🧪 Клинические испытания: {results['clinical_trials']['count']:,} ({results.get('rct_percentage', 0)}%)")
    
    time.sleep(0.5)  # Пауза между запросами
    return results

def main():
    """Анализ топ-20 БАДов"""
    
    supplements = [
        {"name": "Женьшень", "terms": ["ginseng", "panax ginseng", "panax quinquefolius"]},
        {"name": "Чеснок", "terms": ["garlic", "allium sativum"]},
        {"name": "Гинкго", "terms": ["ginkgo", "ginkgo biloba"]},
        {"name": "Зверобой", "terms": ["st john's wort", "hypericum perforatum"]},
        {"name": "Эхинацея", "terms": ["echinacea", "echinacea purpurea"]},
        {"name": "Куркума", "terms": ["turmeric", "curcuma longa", "curcumin"]},
        {"name": "Молочный чертополох", "terms": ["milk thistle", "silybum marianum", "silymarin"]},
        {"name": "Зеленый чай", "terms": ["green tea", "camellia sinensis", "EGCG"]},
        {"name": "Пальметто", "terms": ["saw palmetto", "serenoa repens"]},
        {"name": "Ашвагандха", "terms": ["ashwagandha", "withania somnifera"]},
        {"name": "Валериана", "terms": ["valerian", "valeriana officinalis"]},
        {"name": "Имбирь", "terms": ["ginger", "zingiber officinale"]},
        {"name": "Алоэ", "terms": ["aloe vera", "aloe barbadensis"]},
        {"name": "Женьшень сибирский", "terms": ["eleuthero", "eleutherococcus"]},
        {"name": "Клюква", "terms": ["cranberry", "vaccinium macrocarpon"]},
    ]
    
    print("=== ПОЛНЫЙ АНАЛИЗ БАДов через PubMed API ===")
    
    all_results = []
    
    for supplement in supplements:
        try:
            result = analyze_supplement(supplement['name'], supplement['terms'])
            all_results.append(result)
        except Exception as e:
            print(f"Ошибка с {supplement['name']}: {e}")
    
    # Сохраняем результаты
    with open('full_pubmed_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # Анализ и рейтинги
    print("\n" + "="*50)
    print("📊 РЕЙТИНГИ ПО РЕАЛЬНЫМ ДАННЫМ PubMed")
    print("="*50)
    
    # Топ по количеству исследований
    print("\n🏆 ТОП-10 по количеству исследований:")
    sorted_by_total = sorted(all_results, key=lambda x: x['general']['count'], reverse=True)
    for i, item in enumerate(sorted_by_total[:10], 1):
        print(f"{i:2d}. {item['name']}: {item['general']['count']:,} публикаций")
    
    # Топ по проценту взаимодействий
    print("\n⚠️  ТОП-10 по проценту взаимодействий:")
    sorted_by_interactions = sorted(all_results, key=lambda x: x.get('interaction_percentage', 0), reverse=True)
    for i, item in enumerate(sorted_by_interactions[:10], 1):
        total = item['general']['count']
        interactions = item['interactions']['count']
        percent = item.get('interaction_percentage', 0)
        print(f"{i:2d}. {item['name']}: {percent}% ({interactions:,} из {total:,})")
    
    print(f"\n✅ Полные данные сохранены в full_pubmed_analysis.json")

if __name__ == "__main__":
    main()