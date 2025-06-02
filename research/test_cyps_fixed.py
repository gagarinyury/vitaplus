#!/usr/bin/env python3
"""
ИСПРАВЛЕННОЕ ТЕСТИРОВАНИЕ SuperCYPsPred API
Используем правильные параметры API
"""

import urllib.request
import urllib.parse
import time

def test_api_with_correct_params():
    """Тест API с исправленными параметрами"""
    
    print("🔬 ИСПРАВЛЕННОЕ ТЕСТИРОВАНИЕ SuperCYPsPred API")
    print("="*60)
    
    enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
    retrieve_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php"
    
    # ТЕСТ 1: Правильные параметры для Zinc
    print("\n📤 ТЕСТ 1: Zinc с правильными параметрами")
    
    try:
        # Исправленные параметры (из ошибки видим, что нужно compound_name)
        data = {
            'input': 'Zinc',
            'input_type': 'compound_name',  # Изменили с 'name' на 'compound_name'
            'models': 'ALL_MODELS'
        }
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(
            enqueue_url,
            data=encoded_data,
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        print(f"   URL: {enqueue_url}")
        print(f"   Параметры: {data}")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            response_text = response.read().decode('utf-8')
            
            print(f"   Статус: {status_code}")
            print(f"   Ответ: {response_text}")
            
            if status_code == 200 and not 'ERROR' in response_text:
                task_id = response_text.strip()
                print(f"✅ Получен корректный ID задачи: {task_id}")
                return task_id, retrieve_url
            else:
                print("❌ Ошибка в ответе сервера")
                return None, None
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None

def test_smiles_input():
    """Тест с SMILES строкой"""
    
    print("\n📤 ТЕСТ 2: Аспирин через SMILES")
    
    enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
    
    try:
        # SMILES строка аспирина
        aspirin_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        
        data = {
            'input': aspirin_smiles,
            'input_type': 'smiles_string',  # Используем smiles_string
            'models': 'ALL_MODELS'
        }
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(
            enqueue_url,
            data=encoded_data,
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        print(f"   SMILES: {aspirin_smiles}")
        print(f"   Параметры: {data}")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            response_text = response.read().decode('utf-8')
            
            print(f"   Статус: {status_code}")
            print(f"   Ответ: {response_text}")
            
            if status_code == 200 and not 'ERROR' in response_text:
                task_id = response_text.strip()
                print(f"✅ Получен корректный ID для аспирина: {task_id}")
                return task_id
            else:
                print("❌ Ошибка в ответе сервера")
                return None
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def check_and_download_results(task_id, retrieve_url, compound_name):
    """Проверка статуса и скачивание результатов"""
    
    print(f"\n⏳ Ожидание результатов для {compound_name} (ID: {task_id})")
    
    max_attempts = 20  # 10 минут ожидания
    
    for attempt in range(1, max_attempts + 1):
        print(f"🔄 Попытка {attempt}/{max_attempts}")
        
        try:
            data = {'task_id': task_id}
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            
            req = urllib.request.Request(
                retrieve_url,
                data=encoded_data,
                method='POST'
            )
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.getcode()
                response_text = response.read().decode('utf-8')
                
                print(f"   Статус: {status_code}")
                
                if status_code == 200:
                    # Результаты готовы!
                    csv_url = response_text.strip()
                    print(f"✅ CSV готов: {csv_url}")
                    
                    # Скачиваем CSV
                    try:
                        with urllib.request.urlopen(csv_url, timeout=30) as csv_response:
                            csv_content = csv_response.read().decode('utf-8')
                            
                            print(f"📊 CSV скачан для {compound_name}")
                            print(f"   Размер: {len(csv_content)} символов")
                            
                            # Анализ результатов
                            analyze_csv_results(compound_name, csv_content)
                            
                            # Сохранение
                            filename = f"{compound_name.lower().replace(' ', '_')}_cyp_results.csv"
                            with open(filename, 'w') as f:
                                f.write(csv_content)
                            print(f"💾 Сохранено в: {filename}")
                            
                            return csv_content
                            
                    except Exception as e:
                        print(f"❌ Ошибка скачивания CSV: {e}")
                        return None
                        
                elif status_code == 404:
                    print("   ⏳ Обработка продолжается...")
                    
                else:
                    print(f"   ❌ Неожиданный статус: {status_code}")
                    print(f"   Ответ: {response_text[:200]}")
            
            # Ждем 30 секунд
            if attempt < max_attempts:
                time.sleep(30)
                
        except Exception as e:
            print(f"❌ Ошибка проверки: {e}")
            if attempt < max_attempts:
                time.sleep(30)
    
    print(f"⏰ Превышено время ожидания для {compound_name}")
    return None

def analyze_csv_results(compound_name, csv_content):
    """Анализ CSV результатов"""
    
    print(f"\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ ДЛЯ {compound_name.upper()}:")
    print("-" * 50)
    
    try:
        lines = csv_content.strip().split('\n')
        
        if len(lines) < 2:
            print("❌ Недостаточно данных в CSV")
            return
        
        # Заголовки и данные
        headers = [h.strip() for h in lines[0].split(',')]
        data_line = [d.strip() for d in lines[1].split(',')]
        
        print(f"📋 Заголовки: {', '.join(headers)}")
        print(f"📊 Данные: {', '.join(data_line)}")
        
        # Анализ CYP предсказаний
        print(f"\n🧬 CYP ПРЕДСКАЗАНИЯ:")
        
        cyp_predictions = {}
        cyp_enzymes = ['CYP1A2', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4']
        
        for i, header in enumerate(headers):
            if header in cyp_enzymes and i < len(data_line):
                try:
                    value = float(data_line[i])
                    cyp_predictions[header] = value
                    
                    # Классификация риска
                    if value >= 0.7:
                        risk = "🔴 ВЫСОКИЙ"
                        risk_desc = "Серьезное ингибирование"
                    elif value >= 0.4:
                        risk = "🟡 СРЕДНИЙ"
                        risk_desc = "Умеренное ингибирование"
                    else:
                        risk = "🟢 НИЗКИЙ"
                        risk_desc = "Слабое ингибирование"
                    
                    print(f"   {header}: {value:.3f} ({risk}) - {risk_desc}")
                    
                except ValueError:
                    print(f"   {header}: {data_line[i]} (неверный формат)")
        
        # Общая оценка риска
        if cyp_predictions:
            max_value = max(cyp_predictions.values())
            max_cyp = max(cyp_predictions, key=cyp_predictions.get)
            avg_value = sum(cyp_predictions.values()) / len(cyp_predictions)
            
            print(f"\n🎯 ОБЩАЯ ОЦЕНКА:")
            print(f"   Максимальное ингибирование: {max_value:.3f} ({max_cyp})")
            print(f"   Среднее ингибирование: {avg_value:.3f}")
            
            # Общий риск
            if max_value >= 0.7:
                print(f"   ⚠️ ВЫСОКИЙ РИСК: {compound_name} может серьезно влиять на {max_cyp}")
                print(f"   💊 Возможны взаимодействия с лекарствами, метаболизируемыми {max_cyp}")
            elif max_value >= 0.4:
                print(f"   ⚠️ УМЕРЕННЫЙ РИСК: {compound_name} может влиять на {max_cyp}")
                print(f"   💊 Возможны слабые взаимодействия с некоторыми лекарствами")
            else:
                print(f"   ✅ НИЗКИЙ РИСК: {compound_name} вероятно безопасен в плане CYP взаимодействий")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        print(f"Сырые данные CSV (первые 500 символов):\n{csv_content[:500]}")

def main():
    """Основная функция тестирования"""
    
    print("🔬 ПОЛНОЕ ТЕСТИРОВАНИЕ SuperCYPsPred API")
    print("Тестируем 2 разных способа ввода")
    print("="*80)
    
    results = {}
    
    # Тест 1: Zinc через compound_name
    task_id, retrieve_url = test_api_with_correct_params()
    if task_id:
        result1 = check_and_download_results(task_id, retrieve_url, "Zinc")
        if result1:
            results["Zinc"] = result1
    
    print("\n" + "="*80)
    
    # Тест 2: Аспирин через SMILES
    aspirin_task_id = test_smiles_input()
    if aspirin_task_id:
        result2 = check_and_download_results(aspirin_task_id, retrieve_url, "Aspirin")
        if result2:
            results["Aspirin"] = result2
    
    # Итоговый отчет
    print("\n" + "="*80)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("="*80)
    
    print(f"✅ Успешно протестировано: {len(results)} соединений")
    
    for compound in results.keys():
        print(f"   • {compound}: ✅ CYP профиль получен")
    
    if not results:
        print("❌ Ни один тест не завершился успешно")
        print("   Возможные причины:")
        print("   • Проблемы с сетью")
        print("   • Изменения в API")
        print("   • Превышение лимитов сервера")
    
    print(f"\n🎯 Тестирование завершено!")
    return results

if __name__ == "__main__":
    main()