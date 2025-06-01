#!/usr/bin/env python3
"""
РЕАЛЬНОЕ ТЕСТИРОВАНИЕ SuperCYPsPred API
Делаем 3 запроса к API и анализируем ответы
"""

import requests
import time
import json
import csv
from io import StringIO

class SuperCYPsTester:
    def __init__(self):
        self.enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
        self.retrieve_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php"
        self.max_wait_minutes = 10  # Максимум 10 минут ожидания
        
    def test_supplement(self, supplement_name, test_number):
        """Тестирование одного БАДа"""
        print(f"\n{'='*60}")
        print(f"🧪 ТЕСТ {test_number}: {supplement_name}")
        print(f"{'='*60}")
        
        try:
            # Шаг 1: Отправка запроса
            print(f"📤 Отправка запроса для: {supplement_name}")
            task_id = self.enqueue_request(supplement_name)
            
            if not task_id:
                print("❌ Не удалось получить ID задачи")
                return None
                
            print(f"✅ Получен ID задачи: {task_id}")
            
            # Шаг 2: Ожидание результатов
            print("⏳ Ожидание обработки...")
            csv_content = self.wait_for_results(task_id)
            
            if csv_content:
                print("✅ Результаты получены!")
                self.analyze_results(supplement_name, csv_content)
                return csv_content
            else:
                print("❌ Не удалось получить результаты")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка тестирования {supplement_name}: {e}")
            return None
    
    def enqueue_request(self, supplement_name):
        """Отправка запроса на обработку"""
        data = {
            'input': supplement_name,
            'input_type': 'name',
            'models': 'ALL_MODELS'
        }
        
        try:
            response = requests.post(self.enqueue_url, data=data, timeout=30)
            print(f"   Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                task_id = response.text.strip()
                return task_id
            elif response.status_code == 429:
                print("   ⚠️ Слишком много запросов")
                return None
            elif response.status_code == 403:
                print("   ❌ Превышена дневная квота")
                return None
            else:
                print(f"   ❌ Неожиданный код: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
            return None
    
    def wait_for_results(self, task_id):
        """Ожидание результатов с периодической проверкой"""
        max_attempts = self.max_wait_minutes * 6  # Проверка каждые 10 сек
        
        for attempt in range(1, max_attempts + 1):
            print(f"   🔄 Проверка {attempt}/{max_attempts} (прошло {attempt*10} сек)")
            
            try:
                data = {'task_id': task_id}
                response = requests.post(self.retrieve_url, data=data, timeout=30)
                
                if response.status_code == 200:
                    # Результаты готовы!
                    csv_url = response.text.strip()
                    print(f"   ✅ CSV готов: {csv_url}")
                    return self.download_csv(csv_url)
                    
                elif response.status_code == 404:
                    # Еще обрабатывается
                    if attempt % 6 == 0:  # Каждую минуту
                        print(f"   ⏳ Обработка продолжается ({attempt//6} мин)")
                    
                elif response.status_code == 429:
                    print("   ⚠️ Слишком много запросов, ждем...")
                    
                else:
                    print(f"   ❌ Неожиданный код: {response.status_code}")
                    print(f"   Ответ: {response.text[:200]}")
                
                # Ждем 10 секунд перед следующей проверкой
                time.sleep(10)
                
            except Exception as e:
                print(f"   ❌ Ошибка проверки: {e}")
                time.sleep(10)
        
        print(f"   ⏰ Превышено время ожидания ({self.max_wait_minutes} минут)")
        return None
    
    def download_csv(self, csv_url):
        """Скачивание CSV файла"""
        try:
            response = requests.get(csv_url, timeout=30)
            if response.status_code == 200:
                content = response.text
                print(f"   📊 CSV скачан, размер: {len(content)} символов")
                return content
            else:
                print(f"   ❌ Ошибка скачивания CSV: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Ошибка загрузки: {e}")
            return None
    
    def analyze_results(self, supplement_name, csv_content):
        """Анализ результатов CSV"""
        print(f"\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ ДЛЯ {supplement_name}:")
        print("-" * 50)
        
        try:
            # Парсинг CSV
            lines = csv_content.strip().split('\n')
            
            if len(lines) < 2:
                print("❌ Недостаточно данных в CSV")
                return
            
            # Заголовки
            headers = [h.strip() for h in lines[0].split(',')]
            print(f"📋 Заголовки: {', '.join(headers)}")
            
            # Данные
            data_line = [d.strip() for d in lines[1].split(',')]
            print(f"📊 Данные: {', '.join(data_line)}")
            
            # Анализ предсказаний
            print(f"\n🧬 CYP ПРЕДСКАЗАНИЯ:")
            
            cyp_enzymes = ['CYP1A2', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4']
            predictions = {}
            
            for i, header in enumerate(headers[1:], 1):  # Пропускаем первый столбец (название)
                if i < len(data_line) and header in cyp_enzymes:
                    try:
                        value = float(data_line[i])
                        predictions[header] = value
                        
                        # Интерпретация
                        if value >= 0.7:
                            risk = "🔴 ВЫСОКИЙ"
                        elif value >= 0.4:
                            risk = "🟡 СРЕДНИЙ"
                        else:
                            risk = "🟢 НИЗКИЙ"
                        
                        print(f"   {header}: {value:.3f} ({risk} риск)")
                        
                    except ValueError:
                        print(f"   {header}: {data_line[i]} (неверный формат)")
            
            # Общая оценка
            if predictions:
                max_value = max(predictions.values())
                max_cyp = max(predictions, key=predictions.get)
                
                print(f"\n🎯 ОБЩАЯ ОЦЕНКА:")
                print(f"   Максимальное ингибирование: {max_value:.3f} ({max_cyp})")
                
                if max_value >= 0.7:
                    print(f"   ⚠️ ВНИМАНИЕ: Высокий риск взаимодействий через {max_cyp}")
                elif max_value >= 0.4:
                    print(f"   ⚠️ Умеренный риск взаимодействий через {max_cyp}")
                else:
                    print(f"   ✅ Низкий риск CYP взаимодействий")
            
            # Сохранение результатов
            filename = f"cyp_results_{supplement_name.lower().replace(' ', '_')}.csv"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            print(f"\n💾 Результаты сохранены в: {filename}")
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            print(f"Сырые данные CSV:\n{csv_content[:500]}...")

def main():
    """Основная функция тестирования"""
    print("🔬 ТЕСТИРОВАНИЕ SuperCYPsPred API")
    print("Проверяем 3 разных БАДа на CYP взаимодействия")
    print("="*80)
    
    tester = SuperCYPsTester()
    
    # 3 тестовых БАДа
    test_supplements = [
        "Zinc",           # Минерал
        "Vitamin D",      # Витамин  
        "Curcumin"        # Растительный экстракт
    ]
    
    results = {}
    
    for i, supplement in enumerate(test_supplements, 1):
        result = tester.test_supplement(supplement, i)
        if result:
            results[supplement] = result
        
        # Пауза между запросами
        if i < len(test_supplements):
            print(f"\n⏸️ Пауза 30 секунд перед следующим тестом...")
            time.sleep(30)
    
    # Итоговый отчет
    print(f"\n{'='*80}")
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*80}")
    
    print(f"✅ Успешно протестировано: {len(results)} из {len(test_supplements)} БАДов")
    
    for supplement, result in results.items():
        print(f"   • {supplement}: ✅ Данные получены")
    
    failed = set(test_supplements) - set(results.keys())
    for supplement in failed:
        print(f"   • {supplement}: ❌ Неудача")
    
    if results:
        print(f"\n📁 Файлы результатов:")
        for supplement in results.keys():
            filename = f"cyp_results_{supplement.lower().replace(' ', '_')}.csv"
            print(f"   • {filename}")
    
    print(f"\n🎯 Тестирование завершено!")

if __name__ == "__main__":
    main()