#!/usr/bin/env python3
"""
ПРОСТОЕ ТЕСТИРОВАНИЕ SuperCYPsPred API
Используем только встроенные модули Python
"""

import urllib.request
import urllib.parse
import time
import json

def test_api_simple():
    """Простой тест API с curl-подобными запросами"""
    
    print("🔬 Тестирование SuperCYPsPred API")
    print("="*50)
    
    # URL эндпоинтов
    enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
    retrieve_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php"
    
    # Тест 1: Отправка запроса для Zinc
    print("\n📤 ТЕСТ 1: Отправка запроса для Zinc")
    
    try:
        # Подготовка данных
        data = {
            'input': 'Zinc',
            'input_type': 'name', 
            'models': 'ALL_MODELS'
        }
        
        # Кодирование данных для POST
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        # Создание запроса
        req = urllib.request.Request(
            enqueue_url,
            data=encoded_data,
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        print(f"   URL: {enqueue_url}")
        print(f"   Данные: {data}")
        
        # Отправка запроса
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            response_text = response.read().decode('utf-8')
            
            print(f"   Статус: {status_code}")
            print(f"   Ответ: {response_text}")
            
            if status_code == 200:
                task_id = response_text.strip()
                print(f"✅ Получен ID задачи: {task_id}")
                
                # Сохраним ID для дальнейшего использования
                return task_id
            else:
                print("❌ Неудачная отправка запроса")
                return None
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def check_task_status(task_id, retrieve_url):
    """Проверка статуса задачи"""
    print(f"\n📥 Проверка статуса задачи: {task_id}")
    
    try:
        # Подготовка данных для проверки
        data = {'task_id': task_id}
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        # Создание запроса
        req = urllib.request.Request(
            retrieve_url,
            data=encoded_data,
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        # Отправка запроса
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            response_text = response.read().decode('utf-8')
            
            print(f"   Статус: {status_code}")
            print(f"   Ответ: {response_text[:100]}...")
            
            return status_code, response_text
            
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return None, None

def download_csv(csv_url):
    """Скачивание CSV файла"""
    print(f"\n📊 Скачивание CSV: {csv_url}")
    
    try:
        with urllib.request.urlopen(csv_url, timeout=30) as response:
            csv_content = response.read().decode('utf-8')
            print(f"✅ CSV скачан, размер: {len(csv_content)} символов")
            return csv_content
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        return None

def main():
    """Основная функция тестирования"""
    
    retrieve_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php"
    
    # Тест 1: Отправка запроса
    task_id = test_api_simple()
    
    if not task_id:
        print("❌ Не удалось отправить запрос")
        return
    
    # Тест 2: Ожидание результатов
    print("\n⏳ Ожидание обработки (проверяем каждые 30 секунд)...")
    
    max_attempts = 10  # Максимум 5 минут ожидания
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Попытка {attempt}/{max_attempts}")
        
        status_code, response_text = check_task_status(task_id, retrieve_url)
        
        if status_code == 200:
            # Результаты готовы!
            csv_url = response_text.strip()
            print(f"✅ Результаты готовы: {csv_url}")
            
            # Скачиваем CSV
            csv_content = download_csv(csv_url)
            
            if csv_content:
                # Анализ результатов
                print("\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
                print("-" * 40)
                
                lines = csv_content.strip().split('\n')
                if len(lines) >= 2:
                    headers = lines[0].split(',')
                    data = lines[1].split(',')
                    
                    print(f"Заголовки: {', '.join(headers)}")
                    print(f"Данные: {', '.join(data)}")
                    
                    # Сохранение результатов
                    with open('zinc_cyp_results.csv', 'w') as f:
                        f.write(csv_content)
                    print("💾 Результаты сохранены в: zinc_cyp_results.csv")
                    
                    print("\n🎯 ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
                    return csv_content
                
        elif status_code == 404:
            # Еще обрабатывается
            print("⏳ Обработка продолжается...")
            
        else:
            print(f"❌ Неожиданный статус: {status_code}")
        
        # Ждем 30 секунд
        if attempt < max_attempts:
            print("⏸️ Ожидание 30 секунд...")
            time.sleep(30)
    
    print("⏰ Превышено время ожидания")
    return None

if __name__ == "__main__":
    main()