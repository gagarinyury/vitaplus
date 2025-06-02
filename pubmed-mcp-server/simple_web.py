#!/usr/bin/env python3
"""
Простой веб-интерфейс для Mistral
"""

from flask import Flask, render_template_string, request, jsonify
from mlx_lm import load, generate
import threading

app = Flask(__name__)

class SimpleMistral:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.loading = False
    
    def load_model(self):
        if self.model is None and not self.loading:
            self.loading = True
            print("🚀 Загружаем Mistral...")
            self.model, self.tokenizer = load('mlx-community/Mistral-7B-Instruct-v0.2-4bit')
            print("✅ Mistral готов!")
            self.loading = False
    
    def ask(self, prompt, max_tokens=500):
        if self.model is None:
            self.load_model()
        
        # Создаем промпт для медицинских вопросов
        medical_prompt = f"""[INST] Ты медицинский эксперт. Ответь на вопрос о добавках, витаминах или лекарствах на русском языке.

Вопрос: {prompt}

Дай краткий, понятный ответ, включая:
1. Основная информация
2. Польза/применение  
3. Возможные риски или побочные эффекты
4. Рекомендации по дозировке (если применимо)

Ответ должен быть медицински точным, но понятным для обычного человека. [/INST]"""
        
        response = generate(
            self.model,
            self.tokenizer,
            prompt=medical_prompt,
            max_tokens=max_tokens,
            verbose=False
        )
        
        return response

mistral = SimpleMistral()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 Mistral Medical Assistant</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1000px;
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
            font-size: 2.2em;
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
        .answer {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 15px;
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
        .status {
            text-align: center;
            padding: 15px;
            margin: 20px 0;
            background: #e6fffa;
            border: 1px solid #38b2ac;
            border-radius: 8px;
            color: #234e52;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Mistral Medical Assistant</h1>
        
        <div class="status">
            ✅ Mistral работает локально на вашем Mac • Медицинский эксперт по добавкам и витаминам
        </div>
        
        <div class="search-box">
            <input type="text" id="queryInput" placeholder="Спросите о добавках, витаминах или лекарствах..." onkeypress="handleKeyPress(event)">
            <button onclick="ask()" id="askBtn">🧠 Спросить</button>
        </div>
        
        <div class="examples">
            <h3>💡 Примеры вопросов:</h3>
            <div class="example-queries">
                <div class="example-query" onclick="setQuery('Безопасен ли магний для ежедневного приема?')">Магний безопасность</div>
                <div class="example-query" onclick="setQuery('Какая оптимальная дозировка витамина D?')">Витамин D дозировка</div>
                <div class="example-query" onclick="setQuery('Может ли куркума взаимодействовать с лекарствами?')">Куркума взаимодействия</div>
                <div class="example-query" onclick="setQuery('Омега-3 полезна для сердца?')">Омега-3 для сердца</div>
                <div class="example-query" onclick="setQuery('Побочные эффекты мелатонина')">Мелатонин эффекты</div>
                <div class="example-query" onclick="setQuery('Можно ли принимать цинк долго?')">Цинк длительный прием</div>
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
                ask();
            }
        }
        
        async function ask() {
            const query = document.getElementById('queryInput').value.trim();
            if (!query) return;
            
            const btn = document.getElementById('askBtn');
            const results = document.getElementById('results');
            
            btn.disabled = true;
            btn.textContent = '🧠 Думаю...';
            
            results.innerHTML = '<div class="loading">🧠 Mistral анализирует ваш вопрос...<br>⏱️ Это займет 10-30 секунд</div>';
            
            try {
                const response = await fetch('/ask', {
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
                    displayResult(data);
                }
            } catch (error) {
                results.innerHTML = `<div class="result"><h3>❌ Ошибка</h3><p>Не удалось получить ответ: ${error.message}</p></div>`;
            }
            
            btn.disabled = false;
            btn.textContent = '🧠 Спросить';
        }
        
        function displayResult(data) {
            const results = document.getElementById('results');
            
            let html = `<div class="result">`;
            html += `<h3>🔍 Вопрос: "${data.query}"</h3>`;
            html += `<div class="answer">${data.answer}</div>`;
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

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Пустой вопрос"})
        
        # Получаем ответ от Mistral
        answer = mistral.ask(query)
        
        return jsonify({
            "query": query,
            "answer": answer
        })
        
    except Exception as e:
        return jsonify({"error": f"Ошибка: {str(e)}"})

if __name__ == '__main__':
    # Предзагружаем модель в отдельном потоке
    threading.Thread(target=mistral.load_model, daemon=True).start()
    
    print("🚀 Запускаем Mistral Medical Assistant...")
    print("📍 Откройте браузер: http://localhost:5003")
    print("🧠 Mistral будет отвечать на медицинские вопросы!")
    print("⏹️  Ctrl+C для остановки")
    
    app.run(debug=True, host='0.0.0.0', port=5003)