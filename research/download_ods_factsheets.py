#!/usr/bin/env python3
"""
ODS Fact Sheets Downloader
Скрипт для скачивания всех факт-листов от NIH Office of Dietary Supplements
"""

import os
import time
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class ODSFactSheetDownloader:
    def __init__(self, base_dir: str = "ods_fact_sheets"):
        self.base_url = "https://ods.od.nih.gov/api/"
        self.base_dir = Path(base_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Список известных ресурсов (расширим по мере тестирования)
        self.known_resources = [
            # Основные витамины
            "VitaminA", "VitaminC", "VitaminD", "VitaminE", "VitaminK",
            "VitaminB6", "VitaminB12", "Folate", "Niacin", "Riboflavin", 
            "Thiamin", "Biotin", "PantothenicAcid",
            
            # Минералы
            "Calcium", "Iron", "Magnesium", "Zinc", "Selenium", 
            "Chromium", "Copper", "Iodine", "Manganese", "Molybdenum",
            "Phosphorus", "Potassium", "Sodium",
            
            # Специальные добавки
            "Omega3FattyAcids", "Probiotics", "Ashwagandha", "Multivitamin",
            "CoQ10", "Glucosamine", "Chondroitin", "Ginkgo", "Ginseng",
            "Echinacea", "GarlicSupplements", "Turmeric", "Melatonin",
            
            # Аминокислоты и другие
            "Creatine", "BetaAlanine", "BCAA", "Carnitine", "Taurine",
            
            # Специальные темы
            "DietarySupplementsExercise", "DietarySupplementsOlderAdults",
            "DietarySupplementsPregnancy", "DietarySupplementsCOVID19",
            "WeightLossSupplements", "EnergyDrinks"
        ]
        
        self.reading_levels = ["Consumer", "HealthProfessional", "Spanish"]
        self.output_formats = ["XML", "HTML"]
        
        # Статистика
        self.stats = {
            "total_attempted": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "existing_files": 0
        }

    def setup_directories(self):
        """Создает структуру папок для организации факт-листов"""
        print("📁 Создание структуры папок...")
        
        for format_type in ["xml", "html", "json"]:
            for level in ["consumer", "health_professional", "spanish"]:
                dir_path = self.base_dir / format_type / level
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # Создаем папку для логов
        (self.base_dir / "logs").mkdir(exist_ok=True)
        
        print(f"✅ Структура папок создана в: {self.base_dir}")

    def test_resource_availability(self, resource: str) -> Dict[str, bool]:
        """Проверяет доступность ресурса для всех комбинаций уровней и форматов"""
        availability = {}
        
        for level in self.reading_levels:
            for format_type in self.output_formats:
                url = f"{self.base_url}?resourcename={resource}&readinglevel={level}&outputformat={format_type}"
                
                try:
                    response = self.session.get(url, timeout=10)
                    # Проверяем что это не ошибка или редирект на страницу ошибки
                    is_available = (
                        response.status_code == 200 and 
                        len(response.content) > 1000 and  # Минимальный размер контента
                        b"Error" not in response.content[:500] and
                        b"Not Found" not in response.content[:500]
                    )
                    availability[f"{level}_{format_type}"] = is_available
                    
                except Exception as e:
                    availability[f"{level}_{format_type}"] = False
                
                # Пауза между запросами
                time.sleep(0.5)
        
        return availability

    def download_fact_sheet(self, resource: str, level: str, format_type: str) -> Optional[Dict]:
        """Скачивает конкретный факт-лист"""
        url = f"{self.base_url}?resourcename={resource}&readinglevel={level}&outputformat={format_type}"
        
        # Определяем путь для сохранения
        level_dir = level.lower().replace("health", "health_")
        file_extension = format_type.lower()
        filename = f"{resource}_{level}_{format_type}.{file_extension}"
        filepath = self.base_dir / file_extension / level_dir / filename
        
        # Проверяем, существует ли файл
        if filepath.exists():
            self.stats["existing_files"] += 1
            return {"status": "exists", "path": str(filepath)}
        
        try:
            print(f"📥 Скачивание: {resource} ({level}, {format_type})")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200 and len(response.content) > 1000:
                # Сохраняем файл
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Пытаемся извлечь метаданные из XML
                metadata = None
                if format_type == "XML":
                    try:
                        metadata = self.extract_metadata_from_xml(response.content)
                    except Exception as e:
                        print(f"⚠️  Ошибка извлечения метаданных: {e}")
                
                self.stats["successful_downloads"] += 1
                return {
                    "status": "success", 
                    "path": str(filepath),
                    "size": len(response.content),
                    "metadata": metadata
                }
            else:
                self.stats["failed_downloads"] += 1
                return {"status": "failed", "reason": f"HTTP {response.status_code} or small content"}
                
        except Exception as e:
            self.stats["failed_downloads"] += 1
            return {"status": "error", "reason": str(e)}

    def extract_metadata_from_xml(self, xml_content: bytes) -> Dict:
        """Извлекает метаданные из XML-контента факт-листа"""
        try:
            root = ET.fromstring(xml_content.decode('utf-8'))
            
            # Убираем namespace для простоты поиска
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}')[1]
            
            metadata = {}
            
            # Извлекаем основные поля
            fields = ['FSID', 'Title', 'ShortTitle', 'LanguageCode', 'Reviewed', 'URL']
            for field in fields:
                elem = root.find(field)
                if elem is not None:
                    metadata[field.lower()] = elem.text
            
            # Пытаемся извлечь информацию о взаимодействиях из контента
            content_elem = root.find('Content')
            if content_elem is not None:
                content = content_elem.text or ""
                metadata['has_interactions'] = any(word in content.lower() for word in 
                    ['interact', 'enhance', 'reduce', 'absorb', 'interfere', 'affect'])
                metadata['content_length'] = len(content)
            
            return metadata
            
        except Exception as e:
            return {"error": f"Failed to parse XML: {e}"}

    def save_download_log(self, results: List[Dict]):
        """Сохраняет лог скачивания в JSON"""
        log_data = {
            "download_date": datetime.now().isoformat(),
            "stats": self.stats,
            "results": results
        }
        
        log_path = self.base_dir / "logs" / f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Лог сохранен: {log_path}")

    def create_summary_report(self, results: List[Dict]):
        """Создает сводный отчет о скачанных факт-листах"""
        successful_resources = set()
        available_combinations = {}
        metadata_summary = {}
        
        for result in results:
            if result.get("status") in ["success", "exists"]:
                resource = result["resource"]
                level = result["level"] 
                format_type = result["format"]
                
                successful_resources.add(resource)
                
                if resource not in available_combinations:
                    available_combinations[resource] = []
                available_combinations[resource].append(f"{level}_{format_type}")
                
                # Собираем метаданные
                if result.get("metadata"):
                    metadata_summary[f"{resource}_{level}_{format_type}"] = result["metadata"]
        
        # Создаем отчет
        report = {
            "summary": {
                "total_resources": len(successful_resources),
                "total_files": self.stats["successful_downloads"] + self.stats["existing_files"],
                "successful_downloads": self.stats["successful_downloads"],
                "existing_files": self.stats["existing_files"],
                "failed_downloads": self.stats["failed_downloads"]
            },
            "available_resources": sorted(list(successful_resources)),
            "resource_combinations": available_combinations,
            "metadata_summary": metadata_summary
        }
        
        # Сохраняем отчет
        report_path = self.base_dir / "summary_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Сводный отчет сохранен: {report_path}")
        return report

    def download_all_fact_sheets(self, max_resources: Optional[int] = None):
        """Скачивает все доступные факт-листы"""
        print("🚀 Начинаем скачивание факт-листов ODS...")
        print(f"📝 Будем проверять {len(self.known_resources)} ресурсов")
        
        self.setup_directories()
        
        all_results = []
        
        resources_to_process = self.known_resources[:max_resources] if max_resources else self.known_resources
        
        for i, resource in enumerate(resources_to_process, 1):
            print(f"\n📦 [{i}/{len(resources_to_process)}] Обрабатываем: {resource}")
            
            # Проверяем доступность
            availability = self.test_resource_availability(resource)
            available_count = sum(availability.values())
            
            if available_count == 0:
                print(f"❌ {resource}: Не найден")
                continue
            
            print(f"✅ {resource}: Найдено {available_count} вариантов")
            
            # Скачиваем все доступные варианты
            for level in self.reading_levels:
                for format_type in self.output_formats:
                    key = f"{level}_{format_type}"
                    if availability.get(key, False):
                        self.stats["total_attempted"] += 1
                        result = self.download_fact_sheet(resource, level, format_type)
                        
                        if result:
                            result.update({
                                "resource": resource,
                                "level": level,
                                "format": format_type
                            })
                            all_results.append(result)
                        
                        # Пауза между скачиваниями
                        time.sleep(1)
        
        # Сохраняем логи и создаем отчет
        self.save_download_log(all_results)
        report = self.create_summary_report(all_results)
        
        # Финальная статистика
        print(f"\n🎉 Скачивание завершено!")
        print(f"📊 Статистика:")
        print(f"   • Найдено ресурсов: {report['summary']['total_resources']}")
        print(f"   • Скачано файлов: {self.stats['successful_downloads']}")
        print(f"   • Уже существовало: {self.stats['existing_files']}")
        print(f"   • Не удалось скачать: {self.stats['failed_downloads']}")
        print(f"   • Общий размер: {sum(r.get('size', 0) for r in all_results) / 1024 / 1024:.2f} MB")
        
        return report

def main():
    """Основная функция для запуска скрипта"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Скачать факт-листы ODS")
    parser.add_argument("--limit", type=int, help="Ограничить количество ресурсов для тестирования")
    parser.add_argument("--output-dir", default="ods_fact_sheets", help="Папка для сохранения")
    
    args = parser.parse_args()
    
    downloader = ODSFactSheetDownloader(args.output_dir)
    report = downloader.download_all_fact_sheets(max_resources=args.limit)
    
    print(f"\n✅ Все файлы сохранены в папке: {downloader.base_dir}")
    print(f"📋 Сводный отчет: {downloader.base_dir}/summary_report.json")

if __name__ == "__main__":
    main()