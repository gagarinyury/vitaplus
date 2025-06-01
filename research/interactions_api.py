#!/usr/bin/env python3
"""
Простой API для проверки взаимодействий БАДов
Для интеграции с приложением VitaPlus
"""

import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import List, Dict

app = Flask(__name__)
CORS(app)  # Разрешить CORS для React Native

class InteractionsAPI:
    def __init__(self, database_file: str):
        """Загрузка базы данных взаимодействий"""
        with open(database_file, 'r', encoding='utf-8') as f:
            self.interactions = json.load(f)
        
        # Создание индекса для быстрого поиска
        self.supplement_index = {}
        for interaction in self.interactions:
            supplement = interaction['supplement'].lower()
            if supplement not in self.supplement_index:
                self.supplement_index[supplement] = []
            self.supplement_index[supplement].append(interaction)
    
    def check_interactions(self, supplements: List[str]) -> Dict:
        """Проверка взаимодействий между списком БАДов"""
        found_interactions = []
        warnings = []
        
        for supplement in supplements:
            supplement_lower = supplement.lower()
            
            # Поиск точного совпадения или частичного
            matching_keys = [key for key in self.supplement_index.keys() 
                           if supplement_lower in key or key in supplement_lower]
            
            for key in matching_keys:
                for interaction in self.supplement_index[key]:
                    # Проверка взаимодействий с другими БАДами из списка
                    for other_supplement in supplements:
                        if (other_supplement.lower() in interaction['interacts_with'].lower() or
                            interaction['severity'] == 'high'):
                            found_interactions.append(interaction)
                    
                    # Добавление предупреждений для негативных взаимодействий
                    if interaction['interaction_type'] == 'negative':
                        warnings.append({
                            'supplement': interaction['supplement'],
                            'warning': interaction['effect'][:100] + "...",
                            'severity': interaction['severity']
                        })
        
        return {
            'interactions_found': len(found_interactions),
            'interactions': found_interactions[:10],  # Первые 10
            'warnings': warnings[:5],  # Первые 5 предупреждений
            'high_severity_count': sum(1 for i in found_interactions if i['severity'] == 'high')
        }
    
    def get_supplement_info(self, supplement_name: str) -> Dict:
        """Получение информации о конкретном БАДе"""
        supplement_lower = supplement_name.lower()
        matching_interactions = []
        
        for key, interactions in self.supplement_index.items():
            if supplement_lower in key or key in supplement_lower:
                matching_interactions.extend(interactions)
        
        if not matching_interactions:
            return {'found': False, 'message': 'БАД не найден в базе данных'}
        
        total = len(matching_interactions)
        negative = sum(1 for i in matching_interactions if i['interaction_type'] == 'negative')
        positive = sum(1 for i in matching_interactions if i['interaction_type'] == 'positive')
        high_severity = sum(1 for i in matching_interactions if i['severity'] == 'high')
        
        return {
            'found': True,
            'supplement': supplement_name,
            'total_interactions': total,
            'negative_interactions': negative,
            'positive_interactions': positive,
            'high_severity_interactions': high_severity,
            'sample_interactions': matching_interactions[:5]
        }

# Глобальный экземпляр API
api = InteractionsAPI('/Users/yurygagarin/Code/1/vitaplus/research/interactions_database.json')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({
        'status': 'ok',
        'total_interactions': len(api.interactions),
        'total_supplements': len(api.supplement_index)
    })

@app.route('/api/check-interactions', methods=['POST'])
def check_interactions():
    """Проверка взаимодействий между БАДами"""
    data = request.get_json()
    
    if not data or 'supplements' not in data:
        return jsonify({'error': 'Укажите список БАДов в поле supplements'}), 400
    
    supplements = data['supplements']
    if not isinstance(supplements, list) or len(supplements) == 0:
        return jsonify({'error': 'supplements должен быть непустым списком'}), 400
    
    result = api.check_interactions(supplements)
    return jsonify(result)

@app.route('/api/supplement/<supplement_name>', methods=['GET'])
def get_supplement_info(supplement_name: str):
    """Получение информации о БАДе"""
    result = api.get_supplement_info(supplement_name)
    return jsonify(result)

@app.route('/api/search', methods=['GET'])
def search_supplements():
    """Поиск БАДов по названию"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({'error': 'Укажите параметр поиска q'}), 400
    
    matching_supplements = []
    for supplement_name in api.supplement_index.keys():
        if query in supplement_name:
            matching_supplements.append(supplement_name.title())
    
    return jsonify({
        'query': query,
        'matches': list(set(matching_supplements))[:20]  # Уникальные, первые 20
    })

@app.route('/api/supplements', methods=['GET'])
def list_all_supplements():
    """Список всех БАДов в базе"""
    supplements = list(set(api.supplement_index.keys()))
    supplements = [s.title() for s in sorted(supplements)]
    
    return jsonify({
        'total_count': len(supplements),
        'supplements': supplements
    })

if __name__ == '__main__':
    print("🚀 Запуск API сервера взаимодействий БАДов...")
    print("📍 API будет доступен по адресу: http://localhost:5000")
    print("\n📋 Доступные эндпоинты:")
    print("GET  /api/health - проверка работоспособности")
    print("POST /api/check-interactions - проверка взаимодействий")
    print("GET  /api/supplement/<name> - информация о БАДе")
    print("GET  /api/search?q=<query> - поиск БАДов")
    print("GET  /api/supplements - список всех БАДов")
    print("\nПример использования:")
    print("curl -X POST http://localhost:5000/api/check-interactions \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"supplements": ["Zinc", "Calcium", "Iron"]}\'')
    
    app.run(debug=True, host='0.0.0.0', port=5000)