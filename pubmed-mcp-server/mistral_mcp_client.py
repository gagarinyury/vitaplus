#!/usr/bin/env python3
"""
Mistral + MCP Server Integration Client
Позволяет Mistral использовать PubMed MCP сервер для поиска медицинских данных
"""

import subprocess
import json
import sys
from pathlib import Path
from mlx_lm import load, generate

class MistralMCPClient:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.mcp_server_path = Path(__file__).parent / "dist" / "index.js"
        
    def load_model(self):
        """Загружает модель Mistral"""
        print("🚀 Загружаем Mistral...")
        self.model, self.tokenizer = load('mlx-community/Mistral-7B-Instruct-v0.2-4bit')
        print("✅ Mistral готов!")
        
    def call_mcp_tool(self, tool_name, params=None):
        """Вызывает инструмент MCP сервера"""
        if params is None:
            params = {}
            
        # Создаем JSON-RPC запрос
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        
        try:
            # Запускаем MCP сервер и отправляем запрос
            cmd = ["/opt/homebrew/bin/node", str(self.mcp_server_path)]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={
                    "PUBMED_API_KEY": "c3dec23f21707809b6c685a2b708fc75ab08",
                    "PUBMED_API_BASE_URL": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
                    "PUBMED_RATE_LIMIT_RPM": "600",
                    "PUBMED_TIMEOUT_MS": "30000",
                    "LOG_LEVEL": "info"
                }
            )
            
            stdout, stderr = process.communicate(json.dumps(request))
            
            if process.returncode == 0:
                return json.loads(stdout)
            else:
                return {"error": f"MCP Server error: {stderr}"}
                
        except Exception as e:
            return {"error": f"Failed to call MCP tool: {str(e)}"}
    
    def ask_mistral(self, prompt, max_tokens=500):
        """Спрашивает Mistral"""
        if not self.model:
            self.load_model()
            
        formatted_prompt = f"[INST] {prompt} [/INST]"
        
        response = generate(
            self.model,
            self.tokenizer,
            prompt=formatted_prompt,
            max_tokens=max_tokens,
            verbose=False
        )
        
        return response
    
    def search_and_analyze(self, query):
        """Поиск в PubMed + анализ через Mistral"""
        print(f"🔍 Ищем: {query}")
        
        # 1. Поиск в PubMed через MCP
        search_result = self.call_mcp_tool("search_pubmed", {
            "query": query,
            "max_results": 5
        })
        
        if "error" in search_result:
            return f"Ошибка поиска: {search_result['error']}"
        
        # 2. Анализ результатов через Mistral
        articles_data = json.dumps(search_result, ensure_ascii=False, indent=2)
        
        analysis_prompt = f"""
Проанализируй следующие медицинские статьи из PubMed и дай краткое резюме:

{articles_data}

Ответь на русском языке, выдели:
1. Основные выводы
2. Безопасность 
3. Рекомендации

Ответ должен быть кратким и понятным для обычного человека.
"""
        
        print("🧠 Анализируем через Mistral...")
        analysis = self.ask_mistral(analysis_prompt)
        
        return {
            "query": query,
            "pubmed_results": search_result,
            "mistral_analysis": analysis
        }

def main():
    client = MistralMCPClient()
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("🔍 Введите запрос для поиска: ")
    
    result = client.search_and_analyze(query)
    
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТ АНАЛИЗА")
    print("="*50)
    
    if isinstance(result, dict):
        print(f"\n🔍 Запрос: {result['query']}")
        print(f"\n📚 Найдено статей: {len(result.get('pubmed_results', {}).get('articles', []))}")
        print(f"\n🧠 Анализ Mistral:")
        print(result['mistral_analysis'])
    else:
        print(result)

if __name__ == "__main__":
    main()