#!/usr/bin/env python3
"""
Веб-интерфейс для Mistral + MCP Server
Запускает Flask сервер для удобного взаимодействия
"""

from flask import Flask, render_template_string, request, jsonify, stream_template
import json
import threading
import queue
from pathlib import Path
from mistral_mcp_client import MistralMCPClient

app = Flask(__name__)
client = MistralMCPClient()

# HTML шаблон
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mistral + PubMed MCP | VitaPlus</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #4a5568;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            opacity: 0.6;
            transform: none;
            cursor: not-allowed;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
            font-size: 18px;
        }
        .result {
            margin-top: 30px;
            padding: 25px;
            background: #f8fafc;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }
        .result h3 {
            color: #4a5568;
            margin-top: 0;
        }
        .pubmed-results {
            margin: 20px 0;
        }
        .article {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        .article-title {
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 5px;
        }
        .article-authors {
            color: #718096;
            font-size: 14px;
            margin-bottom: 5px;
        }
        .article-journal {
            color: #4a5568;
            font-size: 14px;
        }
        .analysis {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            white-space: pre-line;
            line-height: 1.6;
        }
        .examples {
            margin: 30px 0;
            padding: 20px;
            background: #f0f4f8;
            border-radius: 10px;
        }
        .example-queries {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .example-query {
            padding: 10px 15px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
        }
        .example-query:hover {
            background: #667eea;
            color: white;
            transform: translateY(-1px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Mistral + 📚 PubMed MCP</h1>
        
        <div class="search-box">
            <input type="text" id="queryInput" placeholder="Введите ваш вопрос о добавках или лекарствах..." onkeypress="handleKeyPress(event)">
            <button onclick="search()" id="searchBtn">🔍 Поиск</button>
        </div>
        
        <div class="examples">
            <h3>💡 Примеры запросов:</h3>
            <div class="example-queries">
                <div class="example-query" onclick="setQuery('магний безопасность')">Магний безопасность</div>
                <div class="example-query" onclick="setQuery('куркума взаимодействие с лекарствами')">Куркума + лекарства</div>
                <div class="example-query" onclick="setQuery('витамин D передозировка')">Витамин D передозировка</div>
                <div class="example-query" onclick="setQuery('зеленый чай побочные эффекты')">Зеленый чай эффекты</div>
                <div class="example-query" onclick="setQuery('омега-3 кардиология')">Омега-3 для сердца</div>
                <div class="example-query" onclick="setQuery('мелатонин дозировка')">Мелатонин дозировка</div>
            </div>
        </div>
        
        <div id="results"></div>
    </div>

    <script>
        function setQuery(query) {
            document.getElementById('queryInput').value = query;
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                search();
            }
        }
        
        async function search() {
            const query = document.getElementById('queryInput').value.trim();
            if (!query) return;
            
            const btn = document.getElementById('searchBtn');
            const results = document.getElementById('results');
            
            btn.disabled = true;
            btn.textContent = '⏳ Поиск...';
            
            results.innerHTML = '<div class="loading">🔍 Ищем в PubMed...<br>🧠 Анализируем через Mistral...<br>⏱️ Это может занять 30-60 секунд</div>';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    results.innerHTML = `<div class="result"><h3>❌ Ошибка</h3><p>${data.error}</p></div>`;
                } else {
                    displayResults(data);
                }
            } catch (error) {
                results.innerHTML = `<div class="result"><h3>❌ Ошибка</h3><p>Не удалось выполнить поиск: ${error.message}</p></div>`;
            }
            
            btn.disabled = false;
            btn.textContent = '🔍 Поиск';
        }
        
        function displayResults(data) {
            const results = document.getElementById('results');
            
            let html = `<div class="result">`;
            html += `<h3>🔍 Результаты для: "${data.query}"</h3>`;
            
            // PubMed результаты
            if (data.pubmed_results && data.pubmed_results.articles) {
                html += `<div class="pubmed-results">`;
                html += `<h4>📚 Найдено статей в PubMed: ${data.pubmed_results.articles.length}</h4>`;
                
                data.pubmed_results.articles.slice(0, 3).forEach(article => {
                    html += `<div class="article">`;
                    html += `<div class="article-title">${article.title}</div>`;
                    if (article.authors) {
                        html += `<div class="article-authors">👥 ${article.authors.slice(0, 3).join(', ')}</div>`;
                    }
                    if (article.journal) {
                        html += `<div class="article-journal">📖 ${article.journal} (${article.pub_date || 'N/A'})</div>`;
                    }
                    html += `</div>`;
                });
                html += `</div>`;
            }
            
            // Анализ Mistral
            if (data.mistral_analysis) {
                html += `<div class="analysis">`;
                html += `<h4>🧠 Анализ Mistral:</h4>`;
                html += `${data.mistral_analysis}`;
                html += `</div>`;
            }
            
            html += `</div>`;
            results.innerHTML = html;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Пустой запрос"})
        
        # Выполняем поиск и анализ
        result = client.search_and_analyze(query)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Ошибка сервера: {str(e)}"})

if __name__ == '__main__':
    print("🚀 Запускаем веб-интерфейс...")
    print("📍 Откройте браузер: http://localhost:5001")
    print("🔍 Можете искать информацию о добавках и лекарствах!")
    print("⏹️  Ctrl+C для остановки")
    
    app.run(debug=True, host='0.0.0.0', port=5001)