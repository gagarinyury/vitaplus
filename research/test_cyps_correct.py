#!/usr/bin/env python3
"""
ПРАВИЛЬНОЕ ТЕСТИРОВАНИЕ SuperCYPsPred API
Используем параметры из оригинального скрипта
"""

import urllib.request
import urllib.parse
import json
import time

def test_api_correct_format():
    """Тест API с правильными параметрами из оригинального скрипта"""
    
    print("🔬 ПРАВИЛЬНОЕ ТЕСТИРОВАНИЕ SuperCYPsPred API")
    print("Используем параметры из оригинального Python скрипта")
    print("="*70)
    
    enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
    retrieve_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php"
    
    # ТЕСТ 1: Zinc через PubChem поиск (как в оригинальном скрипте)
    print("\n📤 ТЕСТ 1: Zinc через PubChem поиск")
    
    try:
        # Параметры как в оригинальном скрипте:
        # input_type: 'name' или 'smiles'
        # input: название или SMILES
        # requested_data: JSON массив моделей
        all_models = ["CYP1A2", "CYP2C9", "CYP2C19", "CYP2D6", "CYP3A4"]
        
        data = {
            'input_type': 'name',  # Как в оригинале
            'input': 'Zinc',
            'requested_data': json.dumps(all_models)  # JSON массив!
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
                return task_id, "Zinc"
            else:
                print("❌ Ошибка в ответе сервера")
                return None, None
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None

def test_aspirin_smiles():
    """Тест с SMILES аспирина"""
    
    print("\n📤 ТЕСТ 2: Аспирин через SMILES")
    
    enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
    
    try:
        aspirin_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        all_models = ["CYP1A2", "CYP2C9", "CYP2C19", "CYP2D6", "CYP3A4"]
        
        data = {
            'input_type': 'smiles',  # SMILES вместо name
            'input': aspirin_smiles,
            'requested_data': json.dumps(all_models)
        }
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(
            enqueue_url,
            data=encoded_data,
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        print(f"   SMILES: {aspirin_smiles}")
        print(f"   Параметры: input_type=smiles, requested_data={json.dumps(all_models)}")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            response_text = response.read().decode('utf-8')
            
            print(f"   Статус: {status_code}")
            print(f"   Ответ: {response_text}")
            
            if status_code == 200 and not 'ERROR' in response_text:
                task_id = response_text.strip()
                print(f"✅ Получен корректный ID для аспирина: {task_id}")
                return task_id, "Aspirin"
            else:
                print("❌ Ошибка в ответе сервера")
                return None, None
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None

def test_curcumin():
    """Тест с куркумином"""
    
    print("\n📤 ТЕСТ 3: Curcumin через PubChem")
    
    enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
    
    try:
        all_models = ["CYP1A2", "CYP2C9", "CYP2C19", "CYP2D6", "CYP3A4"]
        
        data = {
            'input_type': 'name',
            'input': 'Curcumin',
            'requested_data': json.dumps(all_models)
        }
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(
            enqueue_url,
            data=encoded_data,
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        print(f"   Соединение: Curcumin")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            response_text = response.read().decode('utf-8')
            
            print(f"   Статус: {status_code}")
            print(f"   Ответ: {response_text}")
            
            if status_code == 200 and not 'ERROR' in response_text:
                task_id = response_text.strip()
                print(f"✅ Получен корректный ID для куркумина: {task_id}")
                return task_id, "Curcumin"
            else:
                print("❌ Ошибка в ответе сервера")
                return None, None
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None

def retrieve_results(task_id, compound_name):
    """Получение результатов по ID задачи (используя параметр 'id' как в оригинале)"""
    
    print(f"\n⏳ Ожидание результатов для {compound_name} (ID: {task_id})")
    
    retrieve_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php"
    max_attempts = 20  # 10 минут максимум
    
    for attempt in range(1, max_attempts + 1):
        print(f"🔄 Попытка {attempt}/{max_attempts}")
        
        try:
            # В оригинальном скрипте используется параметр 'id', а не 'task_id'!
            data = {'id': task_id}  # ВАЖНО: 'id', а не 'task_id'
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
                    if response_text == "":
                        print("   ⚠️ Пустой ответ")
                    else:
                        # Результаты готовы!
                        print(f"✅ Результаты готовы!")
                        
                        # Скачиваем CSV файл напрямую
                        csv_url = f"http://insilico-cyp.charite.de/SuperCYPsPred/csv/{task_id}_result.csv"
                        print(f"📊 Скачивание CSV: {csv_url}")
                        
                        try:
                            with urllib.request.urlopen(csv_url, timeout=30) as csv_response:
                                csv_content = csv_response.read().decode('utf-8')
                                
                                print(f"✅ CSV скачан для {compound_name}")
                                print(f"   Размер: {len(csv_content)} символов")
                                
                                # Анализ и сохранение
                                analyze_cyp_results(compound_name, csv_content)
                                
                                filename = f"{compound_name.lower()}_cyp_results.csv"
                                with open(filename, 'w') as f:
                                    f.write(csv_content)
                                print(f"💾 Сохранено в: {filename}")
                                
                                return csv_content
                                
                        except Exception as e:
                            print(f"❌ Ошибка скачивания CSV: {e}")
                            
                elif status_code == 404:
                    print("   ⏳ Вычисления не завершены...")
                    
                else:
                    print(f"   ❌ Неожиданный статус: {status_code}")
                    print(f"   Ответ: {response_text[:200]}")
            
            # Ждем 30 секунд как в оригинальном скрипте
            if attempt < max_attempts:
                time.sleep(30)
                
        except Exception as e:
            print(f"❌ Ошибка получения результатов: {e}")
            if attempt < max_attempts:
                time.sleep(30)
    
    print(f"⏰ Превышено время ожидания для {compound_name}")
    return None

def analyze_cyp_results(compound_name, csv_content):
    """Детальный анализ CYP результатов"""
    
    print(f"\n📊 ДЕТАЛЬНЫЙ АНАЛИЗ ДЛЯ {compound_name.upper()}:")
    print("=" * 60)
    
    try:
        lines = csv_content.strip().split('\\n')  # Учитываем экранированные символы
        if len(lines) < 2:
            lines = csv_content.strip().split('\n')  # Обычные переводы строк
        
        if len(lines) < 2:
            print("❌ Недостаточно данных в CSV")
            print(f"Сырой CSV (первые 300 символов):")
            print(csv_content[:300])
            return
        
        # Парсинг заголовков и данных
        headers = [h.strip() for h in lines[0].split(',')]
        data_line = [d.strip() for d in lines[1].split(',')]
        
        print(f"📋 Структура данных:")
        print(f"   Заголовки ({len(headers)}): {', '.join(headers)}")
        print(f"   Данные ({len(data_line)}): {', '.join(data_line[:5])}{'...' if len(data_line) > 5 else ''}")
        
        # Поиск CYP предсказаний
        print(f"\n🧬 CYP ПРОФИЛЬ ИНГИБИРОВАНИЯ:")
        print("-" * 50)
        
        cyp_data = {}
        cyp_found = False
        
        for i, header in enumerate(headers):
            if i < len(data_line) and 'CYP' in header.upper():
                try:
                    value = float(data_line[i])
                    cyp_data[header] = value
                    cyp_found = True
                    
                    # Детальная интерпретация
                    if value >= 0.8:
                        risk = "🔴 ОЧЕНЬ ВЫСОКИЙ"
                        desc = "Почти наверняка блокирует фермент"
                    elif value >= 0.6:
                        risk = "🟠 ВЫСОКИЙ"
                        desc = "Вероятно значительное ингибирование"
                    elif value >= 0.4:
                        risk = "🟡 СРЕДНИЙ"
                        desc = "Умеренное ингибирование возможно"
                    elif value >= 0.2:
                        risk = "🟢 НИЗКИЙ"
                        desc = "Слабое ингибирование"
                    else:
                        risk = "⚪ МИНИМАЛЬНЫЙ"
                        desc = "Почти нет ингибирования"
                    
                    print(f"   {header:8} | {value:6.3f} | {risk:15} | {desc}")
                    
                except (ValueError, IndexError):
                    print(f"   {header:8} | ERROR  | Неверные данные")
        
        if not cyp_found:
            print("❌ CYP данные не найдены в CSV")
            return
        
        # Общая оценка рисков
        print(f"\n🎯 ОБЩАЯ ОЦЕНКА БЕЗОПАСНОСТИ:")
        print("-" * 50)
        
        if cyp_data:
            max_value = max(cyp_data.values())
            max_cyp = max(cyp_data, key=cyp_data.get)
            avg_value = sum(cyp_data.values()) / len(cyp_data)
            
            high_risk_cyps = [cyp for cyp, val in cyp_data.items() if val >= 0.6]
            medium_risk_cyps = [cyp for cyp, val in cyp_data.items() if 0.4 <= val < 0.6]
            
            print(f"📈 Максимальное ингибирование: {max_value:.3f} ({max_cyp})")
            print(f"📊 Среднее ингибирование: {avg_value:.3f}")
            print(f"⚠️ Высокий риск: {len(high_risk_cyps)} ферментов")
            print(f"⚠️ Средний риск: {len(medium_risk_cyps)} ферментов")
            
            # Клинические рекомендации
            print(f"\n💊 КЛИНИЧЕСКИЕ РЕКОМЕНДАЦИИ:")
            print("-" * 50)
            
            if max_value >= 0.8:
                print(f"🚨 ВНИМАНИЕ: {compound_name} может серьезно влиять на {max_cyp}")
                print(f"   Высокий риск взаимодействий с лекарствами")
                print(f"   Рекомендуется консультация врача")
            elif max_value >= 0.6:
                print(f"⚠️ ОСТОРОЖНО: {compound_name} может влиять на {max_cyp}")
                print(f"   Возможны взаимодействия с некоторыми лекарствами")
                print(f"   Рекомендуется мониторинг")
            elif max_value >= 0.4:
                print(f"ℹ️ УМЕРЕННО: {compound_name} может слабо влиять на {max_cyp}")
                print(f"   Минимальный риск взаимодействий")
            else:
                print(f"✅ БЕЗОПАСНО: {compound_name} вероятно не влияет на CYP ферменты")
                print(f"   Низкий риск лекарственных взаимодействий")
            
            # Конкретные ферменты
            if high_risk_cyps:
                print(f"\n🎯 ФЕРМЕНТЫ ВЫСОКОГО РИСКА:")
                for cyp in high_risk_cyps:
                    print(f"   • {cyp}: {cyp_data[cyp]:.3f}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        print(f"Сырые данные (первые 500 символов):")
        print(csv_content[:500])

def main():
    """Основная функция - полное тестирование 3 соединений"""
    
    print("🔬 ПОЛНОЕ ТЕСТИРОВАНИЕ SuperCYPsPred API")
    print("Тестируем 3 разных соединения с правильными параметрами")
    print("="*80)
    
    results = {}
    
    # Список тестов
    tests = [
        ("Тест 1: Zinc", test_api_correct_format),
        ("Тест 2: Aspirin", test_aspirin_smiles),
        ("Тест 3: Curcumin", test_curcumin)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"🧪 {test_name}")
        print(f"{'='*80}")
        
        # Отправка запроса
        task_id, compound_name = test_func()
        
        if task_id and compound_name:
            # Получение результатов
            result = retrieve_results(task_id, compound_name)
            if result:
                results[compound_name] = result
        
        # Пауза между тестами
        if test_func != tests[-1][1]:  # Не для последнего теста
            print(f"\n⏸️ Пауза 60 секунд перед следующим тестом...")
            time.sleep(60)
    
    # Финальный отчет
    print(f"\n{'='*80}")
    print("📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print(f"{'='*80}")
    
    print(f"✅ Успешно протестировано: {len(results)} из 3 соединений")
    
    for compound in results.keys():
        print(f"   • {compound}: ✅ CYP профиль получен и проанализирован")
    
    failed_count = 3 - len(results)
    if failed_count > 0:
        print(f"❌ Неудачных тестов: {failed_count}")
    
    if results:
        print(f"\n📁 Созданные файлы:")
        for compound in results.keys():
            filename = f"{compound.lower()}_cyp_results.csv"
            print(f"   • {filename}")
    
    print(f"\n🎯 Тестирование SuperCYPsPred API завершено!")
    print(f"📊 База данных показала возможности предсказания CYP взаимодействий")
    
    return results

if __name__ == "__main__":
    main()