#!/usr/bin/env python3
"""
Парсер взаимодействий БАДов из ODS факт-листов
Автоматически извлекает все взаимодействия из скачанных XML файлов
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import html

@dataclass
class Interaction:
    supplement: str  # Название БАДа
    interacts_with: str  # С чем взаимодействует
    interaction_type: str  # positive/negative/neutral
    effect: str  # Описание эффекта
    mechanism: str  # Механизм действия
    dosage_info: str  # Информация о дозировке
    severity: str  # low/medium/high
    source_file: str  # Исходный файл
    
class InteractionParser:
    def __init__(self, ods_directory: str):
        self.ods_dir = Path(ods_directory)
        self.interactions = []
        
        # Ключевые слова для поиска взаимодействий
        self.interaction_keywords = [
            'interact', 'interaction', 'interfere', 'interference',
            'affect', 'reduce', 'increase', 'enhance', 'inhibit',
            'block', 'prevent', 'improve', 'decrease', 'absorption',
            'bioavailability', 'compete', 'antagonist', 'synergy'
        ]
        
        # Ключевые слова для типа взаимодействия
        self.negative_keywords = [
            'reduce', 'decrease', 'inhibit', 'block', 'prevent', 
            'interfere', 'compete', 'antagonist', 'toxic', 'harmful',
            'too much', 'too little', 'low blood', 'unsafe'
        ]
        
        self.positive_keywords = [
            'enhance', 'increase', 'improve', 'helps', 'promotes',
            'beneficial', 'synergy', 'boost', 'facilitate'
        ]

    def parse_all_files(self):
        """Парсинг всех XML файлов в директории"""
        xml_files = list(self.ods_dir.rglob("*.xml"))
        print(f"Найдено {len(xml_files)} XML файлов для парсинга...")
        
        for xml_file in xml_files:
            try:
                self.parse_file(xml_file)
            except Exception as e:
                print(f"Ошибка парсинга {xml_file.name}: {e}")
        
        print(f"Извлечено {len(self.interactions)} взаимодействий")
        return self.interactions

    def parse_file(self, xml_file: Path):
        """Парсинг одного XML файла"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Извлечение основной информации
            namespace = {'ns': 'http://tempuri.org/factsheet.xsd'}
            title_elem = root.find('.//ns:Title', namespace)
            content_elem = root.find('.//ns:Content', namespace)
            
            if title_elem is None or content_elem is None:
                return
                
            supplement_name = title_elem.text.strip()
            content = html.unescape(content_elem.text or "")
            
            # Поиск секций о взаимодействиях
            interactions_found = self.extract_interactions(content, supplement_name, xml_file.name)
            self.interactions.extend(interactions_found)
            
        except ET.ParseError as e:
            print(f"XML ошибка в {xml_file.name}: {e}")

    def extract_interactions(self, content: str, supplement_name: str, source_file: str) -> List[Interaction]:
        """Извлечение взаимодействий из текста"""
        interactions = []
        
        # Удаление HTML тегов для анализа текста
        clean_text = re.sub(r'<[^>]+>', ' ', content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Поиск секций о взаимодействиях
        interaction_sections = self.find_interaction_sections(clean_text)
        
        for section in interaction_sections:
            # Разбивка на предложения
            sentences = re.split(r'[.!?]+', section)
            
            for sentence in sentences:
                if self.contains_interaction_keywords(sentence):
                    interaction = self.parse_interaction_sentence(
                        sentence, supplement_name, source_file
                    )
                    if interaction:
                        interactions.append(interaction)
        
        return interactions

    def find_interaction_sections(self, text: str) -> List[str]:
        """Поиск секций с взаимодействиями"""
        sections = []
        
        # Поиск заголовков о взаимодействиях
        interaction_patterns = [
            r'interact with medications.*?(?=h2|$)',
            r'interact with.*?supplements.*?(?=h2|$)', 
            r'Does.*?interact.*?(?=h2|$)',
            r'interact or interfere.*?(?=h2|$)',
            r'taking.*?together.*?(?=h2|$)'
        ]
        
        for pattern in interaction_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                sections.append(match.group())
        
        # Если не найдены специальные секции, ищем в общем тексте
        if not sections:
            sections = [text]
            
        return sections

    def contains_interaction_keywords(self, sentence: str) -> bool:
        """Проверка наличия ключевых слов взаимодействия"""
        sentence_lower = sentence.lower()
        return any(keyword in sentence_lower for keyword in self.interaction_keywords)

    def parse_interaction_sentence(self, sentence: str, supplement_name: str, source_file: str) -> Optional[Interaction]:
        """Парсинг конкретного предложения с взаимодействием"""
        sentence = sentence.strip()
        if len(sentence) < 10:  # Слишком короткое предложение
            return None
            
        # Извлечение информации о взаимодействии
        interacts_with = self.extract_interacting_substance(sentence)
        if not interacts_with:
            return None
            
        interaction_type = self.determine_interaction_type(sentence)
        effect = self.extract_effect(sentence)
        mechanism = self.extract_mechanism(sentence)
        dosage_info = self.extract_dosage_info(sentence)
        severity = self.determine_severity(sentence)
        
        return Interaction(
            supplement=supplement_name,
            interacts_with=interacts_with,
            interaction_type=interaction_type,
            effect=effect,
            mechanism=mechanism,
            dosage_info=dosage_info,
            severity=severity,
            source_file=source_file
        )

    def extract_interacting_substance(self, sentence: str) -> str:
        """Извлечение вещества, с которым происходит взаимодействие"""
        # Паттерны для поиска веществ
        patterns = [
            r'with ([A-Z][a-z]+(?:\s+[a-z]+)*)',  # with Substance
            r'and ([A-Z][a-z]+(?:\s+[a-z]+)*)',   # and Substance  
            r'taking ([A-Z][a-z]+(?:\s+[a-z]+)*)', # taking Substance
            r'([A-Z][a-z]+(?:\s+[a-z]+)*) with',   # Substance with
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sentence)
            if match:
                substance = match.group(1).strip()
                if len(substance) > 2 and substance not in ['Taking', 'With', 'And']:
                    return substance
                    
        return "unknown"

    def determine_interaction_type(self, sentence: str) -> str:
        """Определение типа взаимодействия"""
        sentence_lower = sentence.lower()
        
        if any(keyword in sentence_lower for keyword in self.negative_keywords):
            return "negative"
        elif any(keyword in sentence_lower for keyword in self.positive_keywords):
            return "positive"
        else:
            return "neutral"

    def extract_effect(self, sentence: str) -> str:
        """Извлечение описания эффекта"""
        # Поиск конкретных эффектов
        effects = [
            r'cause ([^.]+)',
            r'might ([^.]+)', 
            r'could ([^.]+)',
            r'may ([^.]+)',
            r'can ([^.]+)'
        ]
        
        for pattern in effects:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return sentence[:100] + "..." if len(sentence) > 100 else sentence

    def extract_mechanism(self, sentence: str) -> str:
        """Извлечение механизма действия"""
        mechanisms = [
            'absorption', 'bioavailability', 'metabolism', 'excretion',
            'competition', 'binding', 'transport', 'synthesis'
        ]
        
        sentence_lower = sentence.lower()
        found_mechanisms = [m for m in mechanisms if m in sentence_lower]
        
        return ", ".join(found_mechanisms) if found_mechanisms else "unknown"

    def extract_dosage_info(self, sentence: str) -> str:
        """Извлечение информации о дозировке"""
        dosage_patterns = [
            r'(\d+\s*(?:mg|mcg|g|ug))',
            r'high dose[s]?',
            r'large amount[s]?',
            r'excessive'
        ]
        
        for pattern in dosage_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group()
                
        return "not specified"

    def determine_severity(self, sentence: str) -> str:
        """Определение серьезности взаимодействия"""
        sentence_lower = sentence.lower()
        
        high_severity = ['toxic', 'dangerous', 'harmful', 'serious', 'severe', 'unsafe']
        medium_severity = ['reduce', 'decrease', 'interfere', 'affect']
        
        if any(word in sentence_lower for word in high_severity):
            return "high"
        elif any(word in sentence_lower for word in medium_severity):
            return "medium"
        else:
            return "low"

    def save_to_json(self, filename: str):
        """Сохранение в JSON"""
        interactions_dict = [asdict(interaction) for interaction in self.interactions]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(interactions_dict, f, ensure_ascii=False, indent=2)
        
        print(f"Взаимодействия сохранены в {filename}")

    def save_to_xml(self, filename: str):
        """Сохранение в XML"""
        root = ET.Element("interactions_database")
        root.set("total_interactions", str(len(self.interactions)))
        root.set("generated_from", "NIH ODS Fact Sheets")
        
        for interaction in self.interactions:
            interaction_elem = ET.SubElement(root, "interaction")
            
            for field, value in asdict(interaction).items():
                elem = ET.SubElement(interaction_elem, field)
                elem.text = str(value)
        
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        
        print(f"Взаимодействия сохранены в {filename}")

    def generate_summary(self):
        """Генерация сводки по взаимодействиям"""
        if not self.interactions:
            return "Взаимодействия не найдены"
            
        total = len(self.interactions)
        by_type = {}
        by_severity = {}
        by_supplement = {}
        
        for interaction in self.interactions:
            # По типу
            by_type[interaction.interaction_type] = by_type.get(interaction.interaction_type, 0) + 1
            
            # По серьезности
            by_severity[interaction.severity] = by_severity.get(interaction.severity, 0) + 1
            
            # По БАДу
            by_supplement[interaction.supplement] = by_supplement.get(interaction.supplement, 0) + 1
        
        summary = f"""
=== СВОДКА ПО ВЗАИМОДЕЙСТВИЯМ ===

Всего найдено: {total} взаимодействий

По типам:
{chr(10).join([f"- {k}: {v}" for k, v in by_type.items()])}

По серьезности:
{chr(10).join([f"- {k}: {v}" for k, v in by_severity.items()])}

Топ БАДов с взаимодействиями:
{chr(10).join([f"- {k}: {v}" for k, v in sorted(by_supplement.items(), key=lambda x: x[1], reverse=True)[:10]])}
"""
        return summary

def main():
    """Основная функция"""
    ods_directory = "/Users/yurygagarin/Code/1/vitaplus/research/ods_fact_sheets"
    
    print("🔍 Запуск парсера взаимодействий БАДов...")
    
    parser = InteractionParser(ods_directory)
    parser.parse_all_files()
    
    if parser.interactions:
        # Сохранение результатов
        parser.save_to_json("/Users/yurygagarin/Code/1/vitaplus/research/interactions_database.json")
        parser.save_to_xml("/Users/yurygagarin/Code/1/vitaplus/research/interactions_database.xml")
        
        # Вывод сводки
        print(parser.generate_summary())
    else:
        print("❌ Взаимодействия не найдены")

if __name__ == "__main__":
    main()