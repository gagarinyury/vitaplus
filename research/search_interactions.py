#!/usr/bin/env python3
"""
Инструмент поиска взаимодействий БАДов
Простой API для поиска взаимодействий в созданной базе данных
"""

import json
from typing import List, Dict, Optional

class InteractionSearcher:
    def __init__(self, database_file: str):
        """Загрузка базы данных взаимодействий"""
        with open(database_file, 'r', encoding='utf-8') as f:
            self.interactions = json.load(f)
        print(f"Загружено {len(self.interactions)} взаимодействий")

    def search_by_supplement(self, supplement_name: str) -> List[Dict]:
        """Поиск взаимодействий для конкретного БАДа"""
        results = []
        supplement_lower = supplement_name.lower()
        
        for interaction in self.interactions:
            if supplement_lower in interaction['supplement'].lower():
                results.append(interaction)
        
        return results

    def search_high_severity(self) -> List[Dict]:
        """Поиск взаимодействий высокой серьезности"""
        return [i for i in self.interactions if i['severity'] == 'high']

    def search_negative_interactions(self) -> List[Dict]:
        """Поиск негативных взаимодействий"""
        return [i for i in self.interactions if i['interaction_type'] == 'negative']

    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """Поиск по ключевому слову в эффекте"""
        results = []
        keyword_lower = keyword.lower()
        
        for interaction in self.interactions:
            if (keyword_lower in interaction['effect'].lower() or 
                keyword_lower in interaction['interacts_with'].lower()):
                results.append(interaction)
        
        return results

    def get_supplement_stats(self) -> Dict:
        """Статистика по БАДам"""
        stats = {}
        for interaction in self.interactions:
            supplement = interaction['supplement']
            if supplement not in stats:
                stats[supplement] = {
                    'total': 0,
                    'negative': 0,
                    'positive': 0,
                    'neutral': 0,
                    'high_severity': 0
                }
            
            stats[supplement]['total'] += 1
            interaction_type = interaction['interaction_type']
            if interaction_type in stats[supplement]:
                stats[supplement][interaction_type] += 1
            if interaction['severity'] == 'high':
                stats[supplement]['high_severity'] += 1
        
        return stats

    def format_interaction(self, interaction: Dict) -> str:
        """Форматирование взаимодействия для вывода"""
        return f"""
📋 {interaction['supplement']} ⚡ {interaction['interacts_with']}
   Тип: {interaction['interaction_type']} | Серьезность: {interaction['severity']}
   Эффект: {interaction['effect'][:100]}...
   Механизм: {interaction['mechanism']}
   Дозировка: {interaction['dosage_info']}
   Источник: {interaction['source_file']}
   {"="*60}"""

    def display_results(self, results: List[Dict], title: str):
        """Отображение результатов поиска"""
        print(f"\n🔍 {title}")
        print(f"Найдено: {len(results)} взаимодействий\n")
        
        for i, interaction in enumerate(results[:10]):  # Показать первые 10
            print(f"{i+1}. {self.format_interaction(interaction)}")
        
        if len(results) > 10:
            print(f"\n... и еще {len(results) - 10} взаимодействий")

def main():
    """Демонстрация поиска"""
    searcher = InteractionSearcher("/Users/yurygagarin/Code/1/vitaplus/research/interactions_database.json")
    
    # Поиск по цинку
    zinc_interactions = searcher.search_by_supplement("Zinc")
    searcher.display_results(zinc_interactions, "Взаимодействия цинка")
    
    # Поиск высокой серьезности
    high_severity = searcher.search_high_severity()
    searcher.display_results(high_severity, "Взаимодействия высокой серьезности")
    
    # Статистика
    stats = searcher.get_supplement_stats()
    print("\n📊 ТОП-10 БАДов по количеству взаимодействий:")
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
    
    for supplement, data in sorted_stats:
        print(f"{supplement}: {data['total']} всего ({data['negative']} негативных, {data['high_severity']} высокой серьезности)")

if __name__ == "__main__":
    main()