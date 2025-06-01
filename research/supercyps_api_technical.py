#!/usr/bin/env python3
"""
ПОДРОБНЫЙ ТЕХНИЧЕСКИЙ АНАЛИЗ SuperCYPsPred API
Детальное изучение Python скрипта с комментариями
"""

import requests
import time
import json
import argparse
import sys

class SuperCYPsPredAPI:
    """
    Детальная реализация SuperCYPsPred API с техническими комментариями
    """
    
    def __init__(self):
        # ЭНДПОИНТЫ API
        self.enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
        self.retrieve_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php"
        
        # ПАРАМЕТРЫ ЗАПРОСА
        self.available_models = ['CYP1A2', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4', 'ALL_MODELS']
        self.input_types = ['name', 'smiles']
        
        # НАСТРОЙКИ ОЖИДАНИЯ
        self.default_wait_time = 10  # секунд
        self.max_retries = 60  # максимум попыток
        
    def enqueue_request(self, input_data, input_type='name', models='ALL_MODELS'):
        """
        ШАГ 1: Отправка запроса на обработку
        
        Параметры HTTP POST запроса:
        - input: Название БАДа или SMILES строка
        - input_type: 'name' или 'smiles'
        - models: Список CYP моделей или 'ALL_MODELS'
        """
        
        # ПОДГОТОВКА ДАННЫХ POST ЗАПРОСА
        post_data = {
            'input': input_data,
            'input_type': input_type,
            'models': models
        }
        
        print(f"📤 Отправка POST запроса:")
        print(f"   URL: {self.enqueue_url}")
        print(f"   Данные: {post_data}")
        
        try:
            # HTTP POST ЗАПРОС
            response = requests.post(
                self.enqueue_url, 
                data=post_data,
                timeout=30  # Тайм-аут 30 секунд
            )
            
            print(f"📨 Ответ сервера:")
            print(f"   Статус код: {response.status_code}")
            print(f"   Заголовки: {dict(response.headers)}")
            
            # ОБРАБОТКА СТАТУС КОДОВ
            if response.status_code == 200:
                # Успешная отправка
                result = response.text.strip()
                print(f"   Содержимое: {result}")
                
                # Возвращается ID задачи для получения результатов
                return result
                
            elif response.status_code == 429:
                # Слишком много запросов
                print("⚠️ Слишком много запросов (429)")
                retry_after = response.headers.get('Retry-After', self.default_wait_time)
                print(f"   Повтор через: {retry_after} секунд")
                return None
                
            elif response.status_code == 403:
                # Превышена дневная квота
                print("❌ Превышена дневная квота (403)")
                return None
                
            else:
                print(f"❌ Неожиданный статус код: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка HTTP запроса: {e}")
            return None
    
    def retrieve_results(self, task_id):
        """
        ШАГ 2: Получение результатов по ID задачи
        
        Система очередей:
        - Задачи обрабатываются асинхронно
        - Нужно периодически проверять готовность
        - Результат возвращается как URL к CSV файлу
        """
        
        print(f"📥 Получение результатов для задачи: {task_id}")
        
        for attempt in range(self.max_retries):
            try:
                # POST запрос для проверки статуса
                post_data = {'task_id': task_id}
                
                print(f"🔄 Попытка {attempt + 1}/{self.max_retries}")
                
                response = requests.post(
                    self.retrieve_url,
                    data=post_data,
                    timeout=30
                )
                
                print(f"   Статус код: {response.status_code}")
                
                # АНАЛИЗ ОТВЕТОВ
                if response.status_code == 200:
                    # Результаты готовы!
                    csv_url = response.text.strip()
                    print(f"✅ Результаты готовы: {csv_url}")
                    
                    # Скачивание CSV файла
                    return self.download_csv_results(csv_url)
                    
                elif response.status_code == 404:
                    # Вычисления еще не завершены
                    print("⏳ Вычисления не завершены (404)")
                    
                    # Определение времени ожидания
                    retry_after = int(response.headers.get('Retry-After', self.default_wait_time))
                    print(f"   Ожидание: {retry_after} секунд")
                    
                    time.sleep(retry_after)
                    continue
                    
                elif response.status_code == 429:
                    # Слишком много запросов
                    print("⚠️ Слишком много запросов (429)")
                    retry_after = int(response.headers.get('Retry-After', self.default_wait_time))
                    time.sleep(retry_after)
                    continue
                    
                else:
                    print(f"❌ Неожиданный статус код: {response.status_code}")
                    print(f"   Ответ: {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Ошибка при получении результатов: {e}")
                time.sleep(self.default_wait_time)
                continue
        
        print("❌ Превышено максимальное количество попыток")
        return None
    
    def download_csv_results(self, csv_url):
        """
        ШАГ 3: Скачивание CSV файла с результатами
        
        Формат CSV:
        - Первая строка: заголовки
        - Данные: предсказания для каждого CYP фермента
        - Значения: 0-1 (вероятность ингибирования)
        """
        
        print(f"📊 Скачивание CSV: {csv_url}")
        
        try:
            response = requests.get(csv_url, timeout=30)
            
            if response.status_code == 200:
                csv_content = response.text
                print("✅ CSV файл успешно скачан")
                print(f"   Размер: {len(csv_content)} символов")
                
                # Парсинг CSV для анализа
                lines = csv_content.strip().split('\n')
                print(f"   Строк данных: {len(lines)}")
                
                if len(lines) > 0:
                    print(f"   Заголовки: {lines[0]}")
                    if len(lines) > 1:
                        print(f"   Первая строка данных: {lines[1]}")
                
                return csv_content
                
            else:
                print(f"❌ Ошибка скачивания CSV: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка скачивания: {e}")
            return None
    
    def predict_cyp_profile(self, compound, input_type='name', models='ALL_MODELS'):
        """
        ПОЛНЫЙ ЦИКЛ: Предсказание CYP профиля для соединения
        """
        
        print(f"🧬 Начало предсказания CYP профиля")
        print(f"   Соединение: {compound}")
        print(f"   Тип входа: {input_type}")
        print(f"   Модели: {models}")
        print("=" * 60)
        
        # Шаг 1: Отправка запроса
        task_id = self.enqueue_request(compound, input_type, models)
        if not task_id:
            return None
        
        print("=" * 60)
        
        # Шаг 2: Получение результатов
        csv_results = self.retrieve_results(task_id)
        if not csv_results:
            return None
        
        print("=" * 60)
        print("🎯 Предсказание завершено!")
        
        return csv_results

def test_api():
    """
    ТЕСТИРОВАНИЕ API с различными входными данными
    """
    
    api = SuperCYPsPredAPI()
    
    # Тест 1: Поиск по названию БАДа
    print("🧪 ТЕСТ 1: Поиск по названию")
    result1 = api.predict_cyp_profile("Zinc", input_type='name')
    
    if result1:
        print("✅ Тест 1 успешен")
        print("CSV результат (первые 500 символов):")
        print(result1[:500])
    else:
        print("❌ Тест 1 неудачен")
    
    print("\n" + "="*80 + "\n")
    
    # Тест 2: SMILES строка (аспирин)
    print("🧪 ТЕСТ 2: SMILES строка аспирина")
    aspirin_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
    result2 = api.predict_cyp_profile(aspirin_smiles, input_type='smiles')
    
    if result2:
        print("✅ Тест 2 успешен")
        print("CSV результат (первые 500 символов):")
        print(result2[:500])
    else:
        print("❌ Тест 2 неудачен")

def analyze_api_structure():
    """
    АНАЛИЗ СТРУКТУРЫ API ДЛЯ АДАПТАЦИИ
    """
    
    print("🔍 ТЕХНИЧЕСКИЙ АНАЛИЗ SuperCYPsPred API")
    print("=" * 60)
    
    print("📋 КЛЮЧЕВЫЕ КОМПОНЕНТЫ:")
    print("1. HTTP POST запросы к 2 эндпоинтам")
    print("2. Система очередей с асинхронной обработкой")
    print("3. Механизм ожидания с Retry-After заголовками")
    print("4. CSV формат результатов")
    print("5. Обработка различных статус кодов")
    
    print("\n📡 СЕТЕВЫЕ ДЕТАЛИ:")
    print("- Протокол: HTTP (не HTTPS!)")
    print("- Метод: POST для всех запросов")
    print("- Тайм-ауты: 30 секунд на запрос")
    print("- Ретраи: До 60 попыток получения результата")
    
    print("\n🔄 ЛОГИКА ОЖИДАНИЯ:")
    print("- Отправка → Получение ID задачи")
    print("- Цикл проверки статуса каждые 10+ секунд")
    print("- HTTP 404 = еще обрабатывается")
    print("- HTTP 200 = результаты готовы")
    print("- HTTP 429 = слишком много запросов")
    
    print("\n💾 ФОРМАТ ДАННЫХ:")
    print("- Вход: Название БАДа или SMILES")
    print("- Выход: CSV файл с предсказаниями")
    print("- Значения: 0.0-1.0 для каждого CYP фермента")
    
    print("\n🌐 ВОЗМОЖНОСТИ АДАПТАЦИИ:")
    print("✅ Легко портировать на JavaScript/TypeScript")
    print("✅ Можно обернуть в REST API сервер")
    print("✅ Совместимо с React Native fetch()")
    print("⚠️ Требует обработки HTTP запросов")
    print("⚠️ Нужна логика ожидания и ретраев")

if __name__ == "__main__":
    print("🔬 SuperCYPsPred API - Технический анализ")
    print("=" * 60)
    
    # Структурный анализ
    analyze_api_structure()
    
    print("\n" + "="*80 + "\n")
    
    # Практическое тестирование (раскомментировать для реального теста)
    # test_api()
    
    print("📝 Анализ завершен. См. комментарии в коде для деталей.")