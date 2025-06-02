#!/usr/bin/env python3
"""
Умное извлечение медицинских фактов с PubMedBERT
"""

import torch
from transformers import AutoTokenizer, AutoModel, pipeline
import re
import json
import numpy as np
from typing import Dict, List, Any

class MedicalFactExtractor:
    def __init__(self):
        self.model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
        self.tokenizer = None
        self.model = None
        self.ner_pipeline = None
        
    def load_model(self):
        """Загружает PubMedBERT и NER pipeline"""
        print("🚀 Загружаем PubMedBERT для извлечения фактов...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        
        # NER pipeline для медицинских сущностей
        self.ner_pipeline = pipeline(
            "token-classification",
            model="d4data/biomedical-ner-all",
            tokenizer="d4data/biomedical-ner-all",
            aggregation_strategy="simple"
        )
        
        print("✅ Модели загружены!")
    
    def extract_facts(self, text: str, entities: List[str]) -> Dict[str, Any]:
        """
        Извлекает структурированные медицинские факты
        
        Args:
            text: Медицинский текст (абстракт статьи)
            entities: Типы сущностей для поиска
        
        Returns:
            Структурированные данные о взаимодействиях
        """
        if not self.model:
            self.load_model()
        
        # 1. Находим медицинские сущности
        entities_found = self.ner_pipeline(text)
        
        # 2. Анализируем взаимодействия
        interactions = self._analyze_interactions(text, entities_found)
        
        # 3. Извлекаем дозировки и безопасность
        safety_info = self._extract_safety_info(text)
        
        # 4. Определяем клиническую значимость
        clinical_significance = self._assess_clinical_significance(text)
        
        # Конвертируем numpy типы в Python типы для JSON
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        result = {
            "entities": entities_found,
            "interactions": interactions,
            "safety": safety_info,
            "clinical_significance": clinical_significance,
            "confidence_score": self._calculate_confidence(text, entities_found)
        }
        
        return convert_numpy_types(result)
    
    def _analyze_interactions(self, text: str, entities: List[Dict]) -> List[Dict]:
        """Анализирует лекарственные взаимодействия"""
        interactions = []
        
        # Паттерны для взаимодействий
        interaction_patterns = {
            "inhibition": [
                r"(\w+)\s+inhibits?\s+(\w+)",
                r"(\w+)\s+blocks?\s+(\w+)",
                r"(\w+)\s+reduces?\s+(\w+)\s+activity"
            ],
            "induction": [
                r"(\w+)\s+induces?\s+(\w+)",
                r"(\w+)\s+increases?\s+(\w+)\s+expression",
                r"(\w+)\s+upregulates?\s+(\w+)"
            ],
            "substrate": [
                r"(\w+)\s+is\s+metabolized\s+by\s+(\w+)",
                r"(\w+)\s+substrate\s+of\s+(\w+)"
            ]
        }
        
        for interaction_type, patterns in interaction_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    interactions.append({
                        "type": interaction_type,
                        "subject": match.group(1),
                        "object": match.group(2),
                        "evidence": match.group(0),
                        "strength": self._assess_interaction_strength(match.group(0))
                    })
        
        return interactions
    
    def _extract_safety_info(self, text: str) -> Dict[str, Any]:
        """Извлекает информацию о безопасности"""
        safety_keywords = {
            "adverse_effects": ["side effect", "adverse", "toxicity", "harmful"],
            "contraindications": ["contraindicated", "avoid", "not recommended"],
            "warnings": ["caution", "warning", "monitor", "careful"],
            "dosage": ["mg", "dose", "dosage", "daily", "twice daily"]
        }
        
        safety_info = {}
        
        for category, keywords in safety_keywords.items():
            findings = []
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    # Извлекаем контекст вокруг ключевого слова
                    context = self._extract_context(text, keyword, window=50)
                    if context:
                        findings.append(context)
            
            safety_info[category] = findings
        
        return safety_info
    
    def _assess_clinical_significance(self, text: str) -> str:
        """Оценивает клиническую значимость"""
        high_significance = ["clinically significant", "major", "severe", "contraindicated"]
        moderate_significance = ["moderate", "monitor", "caution"]
        low_significance = ["minor", "unlikely", "minimal"]
        
        text_lower = text.lower()
        
        if any(term in text_lower for term in high_significance):
            return "high"
        elif any(term in text_lower for term in moderate_significance):
            return "moderate"
        elif any(term in text_lower for term in low_significance):
            return "low"
        else:
            return "unknown"
    
    def _assess_interaction_strength(self, evidence: str) -> str:
        """Оценивает силу взаимодействия"""
        strong_terms = ["strongly", "significantly", "markedly", "potent"]
        moderate_terms = ["moderately", "modestly", "partial"]
        weak_terms = ["slightly", "minimal", "weak", "minor"]
        
        evidence_lower = evidence.lower()
        
        if any(term in evidence_lower for term in strong_terms):
            return "strong"
        elif any(term in evidence_lower for term in moderate_terms):
            return "moderate"
        elif any(term in evidence_lower for term in weak_terms):
            return "weak"
        else:
            return "moderate"  # default
    
    def _extract_context(self, text: str, keyword: str, window: int = 50) -> str:
        """Извлекает контекст вокруг ключевого слова"""
        import re
        
        pattern = rf".{{0,{window}}}{re.escape(keyword)}.{{0,{window}}}"
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(0) if match else ""
    
    def _calculate_confidence(self, text: str, entities: List[Dict]) -> float:
        """Рассчитывает уверенность в извлеченных данных"""
        # Простая эвристика на основе количества найденных сущностей
        # и наличия ключевых медицинских терминов
        
        entity_score = min(len(entities) / 10, 1.0)  # Нормализуем к 1.0
        
        medical_terms = ["metabolism", "enzyme", "cytochrome", "inhibition", "interaction"]
        term_score = sum(1 for term in medical_terms if term in text.lower()) / len(medical_terms)
        
        return (entity_score + term_score) / 2

def test_smart_extraction():
    """Тестирует умное извлечение фактов"""
    
    extractor = MedicalFactExtractor()
    
    # Тестовый медицинский текст
    test_text = """
    Curcumin significantly inhibits CYP3A4 enzyme activity in a dose-dependent manner. 
    At therapeutic doses (500-1000 mg daily), curcumin moderately reduces the metabolism 
    of CYP3A4 substrates, potentially leading to increased drug concentrations. 
    Patients taking warfarin should exercise caution when using turmeric supplements, 
    as this interaction may increase bleeding risk. Clinical monitoring is recommended.
    """
    
    print("🧪 Тестируем умное извлечение фактов...")
    print(f"📄 Текст: {test_text[:100]}...")
    
    facts = extractor.extract_facts(
        text=test_text,
        entities=["supplement", "enzyme", "drug", "interaction"]
    )
    
    print("\n📊 ИЗВЛЕЧЕННЫЕ ФАКТЫ:")
    print(json.dumps(facts, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_smart_extraction()