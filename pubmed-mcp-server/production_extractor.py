#!/usr/bin/env python3
"""
Продакшн-версия медицинского экстрактора
Оптимизирован для реального использования с PubMed данными
"""

import torch
from transformers import AutoTokenizer, AutoModel, pipeline
import re
import json
import numpy as np
from typing import Dict, List, Any, Optional

class ProductionMedicalExtractor:
    def __init__(self):
        self.model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
        self.tokenizer = None
        self.model = None
        self.loaded = False
        
        # Предопределенные медицинские сущности
        self.supplements = [
            "curcumin", "turmeric", "magnesium", "vitamin d", "omega-3", 
            "green tea", "ginkgo", "st john's wort", "echinacea", "garlic",
            "ginseng", "milk thistle", "saw palmetto", "ashwagandha"
        ]
        
        self.enzymes = [
            "cyp3a4", "cyp2d6", "cyp2c9", "cyp2c19", "cyp1a2", 
            "ugt1a1", "ugt2b7", "p-glycoprotein", "cyp2b6"
        ]
        
        self.drugs = [
            "warfarin", "digoxin", "phenytoin", "cyclosporine", "tacrolimus",
            "simvastatin", "atorvastatin", "midazolam", "alprazolam"
        ]
    
    def load_model(self):
        """Загружает модель один раз"""
        if self.loaded:
            return
            
        print("🚀 Загружаем PubMedBERT для продакшн использования...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.loaded = True
            print("✅ PubMedBERT загружен!")
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
    
    def analyze_pubmed_abstract(self, abstract: str, supplement_name: str = None) -> Dict[str, Any]:
        """
        Анализирует абстракт PubMed статьи
        
        Args:
            abstract: Текст абстракта
            supplement_name: Название добавки для фокусированного поиска
        
        Returns:
            Структурированная информация о взаимодействиях
        """
        if not self.loaded:
            self.load_model()
        
        # Нормализуем текст
        text = self._normalize_text(abstract)
        
        # Основной анализ
        result = {
            "supplement": supplement_name or self._find_primary_supplement(text),
            "interactions": self._extract_interactions(text),
            "safety_signals": self._extract_safety_signals(text),
            "dosage_info": self._extract_dosage_info(text),
            "clinical_evidence": self._assess_evidence_level(text),
            "recommendations": self._extract_recommendations(text),
            "confidence": self._calculate_overall_confidence(text)
        }
        
        return result
    
    def _normalize_text(self, text: str) -> str:
        """Нормализует медицинский текст"""
        # Убираем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Стандартизируем названия ферментов
        text = re.sub(r'CYP\s*3A4', 'CYP3A4', text, flags=re.IGNORECASE)
        text = re.sub(r'CYP\s*2D6', 'CYP2D6', text, flags=re.IGNORECASE)
        text = re.sub(r'CYP\s*2C9', 'CYP2C9', text, flags=re.IGNORECASE)
        
        return text
    
    def _find_primary_supplement(self, text: str) -> Optional[str]:
        """Находит основную добавку в тексте"""
        text_lower = text.lower()
        
        for supplement in self.supplements:
            if supplement.lower() in text_lower:
                return supplement
        
        return None
    
    def _extract_interactions(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает информацию о взаимодействиях"""
        interactions = []
        
        # Улучшенные паттерны для взаимодействий
        patterns = {
            "inhibition": [
                r'(\w+(?:\s+\w+)?)\s+(?:significantly|moderately|strongly|potently)?\s*inhibits?\s+(\w+)',
                r'(\w+(?:\s+\w+)?)\s+(?:blocks?|reduces?|decreases?)\s+(\w+)(?:\s+activity)?',
                r'inhibition\s+of\s+(\w+)\s+by\s+(\w+)'
            ],
            "induction": [
                r'(\w+(?:\s+\w+)?)\s+(?:significantly|moderately|strongly)?\s*induces?\s+(\w+)',
                r'(\w+(?:\s+\w+)?)\s+(?:increases?|upregulates?)\s+(\w+)(?:\s+expression)?'
            ],
            "substrate": [
                r'(\w+(?:\s+\w+)?)\s+is\s+(?:a\s+)?substrate\s+(?:of\s+)?(\w+)',
                r'(\w+)\s+metabolizes?\s+(\w+)',
                r'(\w+(?:\s+\w+)?)\s+is\s+metabolized\s+by\s+(\w+)'
            ]
        }
        
        for interaction_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    subject = match.group(1).strip()
                    target = match.group(2).strip()
                    
                    # Проверяем что это реальные медицинские сущности
                    if self._is_medical_entity(subject) and self._is_medical_entity(target):
                        interaction = {
                            "type": interaction_type,
                            "subject": subject,
                            "target": target,
                            "evidence_text": match.group(0),
                            "strength": self._assess_interaction_strength(match.group(0)),
                            "position": match.span()
                        }
                        interactions.append(interaction)
        
        return interactions
    
    def _extract_safety_signals(self, text: str) -> Dict[str, List[str]]:
        """Извлекает сигналы безопасности"""
        safety_signals = {
            "warnings": [],
            "adverse_effects": [],
            "contraindications": [],
            "monitoring_required": []
        }
        
        # Паттерны для разных типов предупреждений
        patterns = {
            "warnings": [
                r'(?:caution|warning|careful|avoid|risk)[^.]{0,100}',
                r'should\s+(?:be\s+)?(?:avoided|monitored|used\s+carefully)[^.]{0,100}',
                r'may\s+(?:increase|cause|lead\s+to)[^.]{0,100}(?:risk|toxicity|bleeding)'
            ],
            "adverse_effects": [
                r'(?:side\s+effects?|adverse\s+(?:effects?|reactions?)|toxicity)[^.]{0,100}',
                r'(?:nausea|headache|dizziness|bleeding|liver\s+damage)[^.]{0,100}'
            ],
            "contraindications": [
                r'contraindicated[^.]{0,100}',
                r'should\s+not\s+be\s+used[^.]{0,100}',
                r'avoid\s+in\s+patients[^.]{0,100}'
            ],
            "monitoring_required": [
                r'(?:monitor|monitoring|surveillance)[^.]{0,100}',
                r'regular\s+(?:blood\s+tests?|laboratory\s+tests?)[^.]{0,100}'
            ]
        }
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    safety_signals[category].append(match.group(0).strip())
        
        return safety_signals
    
    def _extract_dosage_info(self, text: str) -> List[Dict[str, str]]:
        """Извлекает информацию о дозировках"""
        dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(mg|g|mcg|iu|units?)\s*(?:daily|per\s+day|twice\s+daily)',
            r'therapeutic\s+dose[^.]{0,50}?(\d+(?:\.\d+)?)\s*(mg|g|mcg)',
            r'(?:at\s+)?dose[s]?\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(mg|g|mcg)'
        ]
        
        dosages = []
        for pattern in dosage_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                # Безопасно извлекаем информацию
                dosage_info = {
                    "amount": groups[0] if len(groups) > 0 else "unknown",
                    "unit": groups[-1] if len(groups) > 1 else "unknown",
                    "context": match.group(0),
                    "range": groups[1] if len(groups) > 2 and groups[1] else None
                }
                dosages.append(dosage_info)
        
        return dosages
    
    def _assess_evidence_level(self, text: str) -> str:
        """Оценивает уровень доказательности"""
        high_evidence = ["randomized controlled trial", "meta-analysis", "systematic review", "clinical trial"]
        moderate_evidence = ["cohort study", "case-control", "clinical study", "human study"]
        low_evidence = ["case report", "in vitro", "animal study", "preliminary"]
        
        text_lower = text.lower()
        
        if any(term in text_lower for term in high_evidence):
            return "high"
        elif any(term in text_lower for term in moderate_evidence):
            return "moderate"
        elif any(term in text_lower for term in low_evidence):
            return "low"
        else:
            return "unknown"
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Извлекает клинические рекомендации"""
        recommendation_patterns = [
            r'(?:recommend|suggestion|should|advise)[^.]{0,100}',
            r'clinical\s+(?:monitoring|surveillance|management)[^.]{0,100}',
            r'patients\s+should[^.]{0,100}'
        ]
        
        recommendations = []
        for pattern in recommendation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                recommendations.append(match.group(0).strip())
        
        return recommendations
    
    def _is_medical_entity(self, entity: str) -> bool:
        """Проверяет является ли сущность медицинской"""
        entity_lower = entity.lower()
        
        all_entities = self.supplements + self.enzymes + self.drugs
        
        return any(med_entity.lower() in entity_lower or entity_lower in med_entity.lower() 
                  for med_entity in all_entities)
    
    def _assess_interaction_strength(self, evidence: str) -> str:
        """Оценивает силу взаимодействия на основе контекста"""
        evidence_lower = evidence.lower()
        
        if any(term in evidence_lower for term in ["significantly", "markedly", "strongly", "potently", "major"]):
            return "strong"
        elif any(term in evidence_lower for term in ["moderately", "modestly", "moderate"]):
            return "moderate"
        elif any(term in evidence_lower for term in ["slightly", "minimally", "weak", "minor"]):
            return "weak"
        else:
            return "moderate"
    
    def _calculate_overall_confidence(self, text: str) -> float:
        """Рассчитывает общую уверенность в анализе"""
        factors = []
        
        # Длина текста
        text_length_score = min(len(text) / 1000, 1.0)
        factors.append(text_length_score)
        
        # Наличие медицинских терминов
        medical_terms = ["metabolism", "enzyme", "cytochrome", "inhibition", "interaction", "pharmacokinetic"]
        term_score = sum(1 for term in medical_terms if term in text.lower()) / len(medical_terms)
        factors.append(term_score)
        
        # Наличие конкретных данных
        has_dosage = bool(re.search(r'\d+\s*(?:mg|g|mcg)', text))
        has_enzyme = any(enzyme in text.lower() for enzyme in self.enzymes)
        has_supplement = any(supplement in text.lower() for supplement in self.supplements)
        
        specificity_score = sum([has_dosage, has_enzyme, has_supplement]) / 3
        factors.append(specificity_score)
        
        return sum(factors) / len(factors)

def test_production_extractor():
    """Тестирует продакшн экстрактор"""
    
    extractor = ProductionMedicalExtractor()
    
    # Реальный пример абстракта
    test_abstract = """
    Background: Curcumin, the active component of turmeric, has been shown to interact 
    with cytochrome P450 enzymes. This study investigated the effects of curcumin 
    supplementation on CYP3A4 activity in healthy volunteers.
    
    Methods: Twenty healthy adults received curcumin 500 mg twice daily for 14 days. 
    CYP3A4 activity was assessed using midazolam as a probe substrate.
    
    Results: Curcumin significantly inhibited CYP3A4 activity by 45% (p<0.01). 
    The inhibition was dose-dependent and reversible. Patients taking warfarin 
    should exercise caution when using curcumin supplements due to increased 
    bleeding risk. Clinical monitoring of INR is recommended.
    
    Conclusion: Curcumin moderately inhibits CYP3A4 and may affect the metabolism 
    of CYP3A4 substrates. Healthcare providers should be aware of potential 
    drug-supplement interactions.
    """
    
    print("🧪 Тестируем продакшн экстрактор...")
    print("="*70)
    
    result = extractor.analyze_pubmed_abstract(test_abstract, "curcumin")
    
    print("📊 РЕЗУЛЬТАТ АНАЛИЗА:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_production_extractor()