#!/usr/bin/env python3
"""
Простой PubMed API тест без внешних зависимостей
Использует только встроенные модули Python
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time

# PubMed API endpoints
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

def search_pubmed_simple(query, retmax=10):
    """Простой поиск в PubMed без requests"""
    # Кодируем параметры
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': str(retmax),
        'retmode': 'xml'
    }
    
    # Создаем URL с параметрами
    url = ESEARCH_URL + '?' + urllib.parse.urlencode(params)
    
    try:
        # Делаем запрос
        with urllib.request.urlopen(url) as response:
            content = response.read()
        
        # Парсим XML
        root = ET.fromstring(content)
        
        # Получаем количество результатов
        count_elem = root.find('Count')
        total_count = int(count_elem.text) if count_elem is not None else 0
        
        # Получаем ID статей
        id_list = []
        id_list_elem = root.find('IdList')
        if id_list_elem is not None:
            for id_elem in id_list_elem.findall('Id'):
                id_list.append(id_elem.text)
        
        return {
            'total_count': total_count,
            'ids': id_list,
            'query': query
        }
        
    except Exception as e:
        print(f"Ошибка поиска '{query}': {e}")
        return {'total_count': 0, 'ids': [], 'query': query}

def test_supplements():
    """Тестируем поиск БАДов в PubMed"""
    
    supplements = [
        {"name": "Эхинацея", "query": 'echinacea AND humans[MeSH]'},
        {"name": "Гинкго", "query": 'ginkgo biloba AND humans[MeSH]'},
        {"name": "Зверобой", "query": '"st john\'s wort" AND humans[MeSH]'},
        {"name": "Женьшень", "query": 'ginseng AND humans[MeSH]'},
        {"name": "Чеснок", "query": 'garlic AND humans[MeSH]'},
    ]
    
    results = {}
    
    print("=== ТЕСТ PubMed API ===")
    print("Получаем РЕАЛЬНЫЕ данные из PubMed...\n")
    
    for supplement in supplements:
        print(f"Поиск: {supplement['name']}")
        
        # Общий поиск
        general_result = search_pubmed_simple(supplement['query'])
        general_count = general_result['total_count']
        
        # Поиск взаимодействий
        interaction_query = supplement['query'].replace('AND humans[MeSH]', '') + ' AND "drug interactions" AND humans[MeSH]'
        interaction_result = search_pubmed_simple(interaction_query)
        interaction_count = interaction_result['total_count']
        
        results[supplement['name']] = {
            'general': {
                'count': general_count,
                'query': supplement['query']
            },
            'interactions': {
                'count': interaction_count,
                'query': interaction_query
            }
        }
        
        print(f"  Общих публикаций: {general_count}")
        print(f"  О взаимодействиях: {interaction_count}")
        print()
        
        # Пауза между запросами
        time.sleep(0.5)
    
    return results

def main():
    """Основная функция"""
    results = test_supplements()
    
    # Сохраняем результаты
    with open('real_pubmed_data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("=== РЕАЛЬНЫЕ ДАННЫЕ ИЗ PubMed ===")
    print("Количество публикаций по БАДам:\n")
    
    # Сортируем по количеству публикаций
    sorted_supplements = sorted(
        results.items(), 
        key=lambda x: x[1]['general']['count'], 
        reverse=True
    )
    
    for name, data in sorted_supplements:
        general_count = data['general']['count']
        interaction_count = data['interactions']['count']
        interaction_percent = round(interaction_count/general_count*100, 1) if general_count > 0 else 0
        
        print(f"{name}:")
        print(f"  📊 Всего публикаций: {general_count:,}")
        print(f"  ⚠️  О взаимодействиях: {interaction_count:,} ({interaction_percent}%)")
        print()
    
    print("✅ Данные сохранены в real_pubmed_data.json")

if __name__ == "__main__":
    main()