#!/usr/bin/env python3
"""
Создание HTML-интерфейса для просмотра базы взаимодействий БАДов
"""

import json
import html
from pathlib import Path

def create_html_viewer():
    """Создание HTML страницы для просмотра взаимодействий"""
    
    # Загрузка данных
    with open('/Users/yurygagarin/Code/1/vitaplus/research/interactions_database.json', 'r', encoding='utf-8') as f:
        interactions = json.load(f)
    
    # Группировка по БАДам
    by_supplement = {}
    for interaction in interactions:
        supplement = interaction['supplement']
        if supplement not in by_supplement:
            by_supplement[supplement] = []
        by_supplement[supplement].append(interaction)
    
    # Статистика
    total_interactions = len(interactions)
    total_supplements = len(by_supplement)
    negative_count = sum(1 for i in interactions if i['interaction_type'] == 'negative')
    high_severity_count = sum(1 for i in interactions if i['severity'] == 'high')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>База взаимодействий БАДов VitaPlus</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .search-bar {{
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #e9ecef;
        }}
        .search-input {{
            width: 100%;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        .search-input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        .supplements-grid {{
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        .supplement-card {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .supplement-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}
        .supplement-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            font-weight: bold;
            font-size: 1.1em;
        }}
        .supplement-stats {{
            padding: 15px;
            background: #f8f9fa;
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
        }}
        .interactions-list {{
            max-height: 300px;
            overflow-y: auto;
        }}
        .interaction-item {{
            padding: 10px 15px;
            border-bottom: 1px solid #f1f3f4;
        }}
        .interaction-item:last-child {{
            border-bottom: none;
        }}
        .interaction-type {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 8px;
        }}
        .negative {{ background: #fee; color: #d32f2f; }}
        .positive {{ background: #e8f5e8; color: #2e7d32; }}
        .neutral {{ background: #f3f4f6; color: #6b7280; }}
        .severity {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .high {{ background: #ffebee; color: #c62828; }}
        .medium {{ background: #fff3e0; color: #ef6c00; }}
        .low {{ background: #f1f8e9; color: #558b2f; }}
        .interaction-effect {{
            margin-top: 5px;
            font-size: 0.9em;
            color: #6c757d;
        }}
        .hidden {{ display: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 База взаимодействий БАДов</h1>
            <p>VitaPlus Research Database</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_interactions}</div>
                <div class="stat-label">Всего взаимодействий</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_supplements}</div>
                <div class="stat-label">БАДов и витаминов</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{negative_count}</div>
                <div class="stat-label">Негативных взаимодействий</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{high_severity_count}</div>
                <div class="stat-label">Высокой серьезности</div>
            </div>
        </div>
        
        <div class="search-bar">
            <input type="text" class="search-input" placeholder="🔍 Поиск по названию БАДа или взаимодействию..." id="searchInput">
        </div>
        
        <div class="supplements-grid" id="supplementsGrid">
"""
    
    # Генерация карточек БАДов
    for supplement, supplement_interactions in sorted(by_supplement.items()):
        total = len(supplement_interactions)
        negative = sum(1 for i in supplement_interactions if i['interaction_type'] == 'negative')
        positive = sum(1 for i in supplement_interactions if i['interaction_type'] == 'positive')
        high_severity = sum(1 for i in supplement_interactions if i['severity'] == 'high')
        
        html_content += f"""
            <div class="supplement-card" data-supplement="{html.escape(supplement.lower())}">
                <div class="supplement-header">{html.escape(supplement)}</div>
                <div class="supplement-stats">
                    <span>Всего: {total}</span>
                    <span>Негативных: {negative}</span>
                    <span>Позитивных: {positive}</span>
                    <span>Серьезных: {high_severity}</span>
                </div>
                <div class="interactions-list">
        """
        
        # Показать первые 5 взаимодействий
        for interaction in supplement_interactions[:5]:
            effect_short = interaction['effect'][:80] + "..." if len(interaction['effect']) > 80 else interaction['effect']
            
            html_content += f"""
                    <div class="interaction-item">
                        <div>
                            <span class="interaction-type {interaction['interaction_type']}">{interaction['interaction_type']}</span>
                            <span class="severity {interaction['severity']}">{interaction['severity']}</span>
                        </div>
                        <div class="interaction-effect">{html.escape(effect_short)}</div>
                    </div>
            """
        
        if len(supplement_interactions) > 5:
            html_content += f'<div class="interaction-item">... и еще {len(supplement_interactions) - 5} взаимодействий</div>'
        
        html_content += """
                </div>
            </div>
        """
    
    html_content += """
        </div>
    </div>
    
    <script>
        // Поиск
        document.getElementById('searchInput').addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.supplement-card');
            
            cards.forEach(card => {
                const supplementName = card.dataset.supplement;
                const text = card.textContent.toLowerCase();
                
                if (supplementName.includes(query) || text.includes(query)) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            });
        });
    </script>
</body>
</html>
    """
    
    return html_content

def main():
    """Создание HTML файла"""
    html_content = create_html_viewer()
    
    with open('/Users/yurygagarin/Code/1/vitaplus/research/interactions_viewer.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML интерфейс создан: interactions_viewer.html")
    print("🌐 Откройте файл в браузере для просмотра базы взаимодействий")

if __name__ == "__main__":
    main()