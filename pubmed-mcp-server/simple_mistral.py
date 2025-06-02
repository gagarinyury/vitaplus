#!/usr/bin/env python3
"""
Простой Mistral без MCP - для тестирования
"""

from mlx_lm import load, generate
import sys

def ask_mistral(prompt, max_tokens=500):
    """Простой запрос к Mistral"""
    print("🚀 Загружаем Mistral...")
    model, tokenizer = load('mlx-community/Mistral-7B-Instruct-v0.2-4bit')
    print("✅ Mistral готов!")
    
    formatted_prompt = f"[INST] {prompt} [/INST]"
    
    print("🧠 Генерируем ответ...")
    response = generate(
        model,
        tokenizer,
        prompt=formatted_prompt,
        max_tokens=max_tokens,
        verbose=False
    )
    
    return response

def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("🔍 Введите ваш вопрос: ")
    
    print(f"\n🔍 Вопрос: {query}")
    print("="*50)
    
    answer = ask_mistral(query)
    
    print("🧠 Ответ Mistral:")
    print(answer)

if __name__ == "__main__":
    main()