#!/usr/bin/env python3
"""
Комплексный медицинский экстрактор
Извлекает все ключевые параметры для анализа добавок и лекарств
"""

import torch
from transformers import AutoTokenizer, AutoModel
import re
import json
import numpy as np
from typing import Dict, List, Any, Optional

class ComprehensiveMedicalExtractor:
    def __init__(self):
        self.model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
        self.tokenizer = None
        self.model = None
        self.loaded = False
        
        # Медицинские базы знаний
        self.cyp_enzymes = {
            "cyp3a4": ["CYP3A4", "3A4", "cytochrome p450 3a4"],
            "cyp2d6": ["CYP2D6", "2D6", "cytochrome p450 2d6"],
            "cyp2c9": ["CYP2C9", "2C9", "cytochrome p450 2c9"],
            "cyp2c19": ["CYP2C19", "2C19", "cytochrome p450 2c19"],
            "cyp1a2": ["CYP1A2", "1A2", "cytochrome p450 1a2"],
            "cyp2b6": ["CYP2B6", "2B6", "cytochrome p450 2b6"]
        }
        
        self.transporters = {
            "p_glycoprotein": ["P-glycoprotein", "P-gp", "MDR1", "ABCB1"],
            "oatp": ["OATP", "organic anion transporting polypeptide"],
            "bcrp": ["BCRP", "breast cancer resistance protein", "ABCG2"],
            "oat": ["OAT", "organic anion transporter"],
            "oct": ["OCT", "organic cation transporter"]
        }
        
        self.special_populations = [
            "pregnancy", "pregnant", "lactation", "breastfeeding",
            "elderly", "geriatric", "pediatric", "children",
            "hepatic impairment", "liver disease", "renal impairment", "kidney disease"
        ]
    
    def load_model(self):
        """Загружает PubMedBERT"""
        if self.loaded:
            return
            
        print("🚀 Загружаем PubMedBERT для комплексного анализа...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.loaded = True
        print("✅ PubMedBERT готов для комплексного анализа!")
    
    def extract_comprehensive_data(self, text: str, substance_name: str = None) -> Dict[str, Any]:
        """
        Извлекает все медицинские параметры из текста
        """
        if not self.loaded:
            self.load_model()
        
        # Нормализуем текст
        normalized_text = self._normalize_medical_text(text)
        
        # Комплексный анализ
        result = {
            "substance": substance_name or self._identify_substance(normalized_text),
            "cyp450_interactions": self._extract_cyp450_data(normalized_text),
            "transporters": self._extract_transporter_data(normalized_text),
            "timing_administration": self._extract_timing_data(normalized_text),
            "pharmacokinetics": self._extract_pharmacokinetic_data(normalized_text),
            "safety_profile": self._extract_safety_profile(normalized_text),
            "clinical_data": self._extract_clinical_data(normalized_text),
            "special_populations": self._extract_special_populations_data(normalized_text),
            "evidence_quality": self._assess_evidence_quality(normalized_text),
            "extraction_confidence": self._calculate_extraction_confidence(normalized_text)
        }
        
        return result
    
    def _normalize_medical_text(self, text: str) -> str:
        """Нормализует медицинский текст"""
        # Стандартизируем медицинские термины
        text = re.sub(r'cytochrome\s+p450\s*(\w+)', r'CYP\1', text, flags=re.IGNORECASE)
        text = re.sub(r'cyp\s*(\w+)', r'CYP\1', text, flags=re.IGNORECASE)
        text = re.sub(r'p-glycoprotein', 'P-glycoprotein', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def _extract_cyp450_data(self, text: str) -> Dict[str, Any]:
        """Извлекает данные о CYP450 взаимодействиях"""
        cyp_data = {}
        
        for enzyme_key, enzyme_variants in self.cyp_enzymes.items():
            enzyme_info = {
                "interactions": [],
                "kinetic_values": {},
                "clinical_significance": "unknown"
            }
            
            # Ищем взаимодействия для каждого фермента
            for variant in enzyme_variants:
                # Паттерны для разных типов взаимодействий
                inhibition_patterns = [
                    rf'(\w+(?:\s+\w+)?)\s+(?:significantly|moderately|strongly|potently)?\s*inhibits?\s+{re.escape(variant)}',
                    rf'{re.escape(variant)}\s+(?:is\s+)?inhibited\s+by\s+(\w+(?:\s+\w+)?)',
                    rf'inhibition\s+of\s+{re.escape(variant)}\s+by\s+(\w+(?:\s+\w+)?)'
                ]
                
                induction_patterns = [
                    rf'(\w+(?:\s+\w+)?)\s+(?:significantly|moderately|strongly)?\s*induces?\s+{re.escape(variant)}',
                    rf'{re.escape(variant)}\s+(?:is\s+)?induced\s+by\s+(\w+(?:\s+\w+)?)'
                ]
                
                substrate_patterns = [
                    rf'(\w+(?:\s+\w+)?)\s+is\s+(?:a\s+)?substrate\s+(?:of\s+)?{re.escape(variant)}',
                    rf'{re.escape(variant)}\s+metabolizes?\s+(\w+(?:\s+\w+)?)'
                ]
                
                # Извлекаем взаимодействия
                for pattern_type, patterns in [
                    ("inhibition", inhibition_patterns),
                    ("induction", induction_patterns),
                    ("substrate", substrate_patterns)
                ]:
                    for pattern in patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            interaction = {
                                "type": pattern_type,
                                "enzyme": variant,
                                "substance": match.group(1).strip(),
                                "strength": self._extract_interaction_strength(match.group(0)),
                                "evidence": match.group(0)
                            }
                            enzyme_info["interactions"].append(interaction)
                
                # Извлекаем кинетические значения (IC50, Ki, etc.)
                kinetic_patterns = {
                    "ic50": rf'ic50[^0-9]*(\d+(?:\.\d+)?)\s*(nm|μm|mm|ng/ml|μg/ml)',
                    "ki": rf'ki[^0-9]*(\d+(?:\.\d+)?)\s*(nm|μm|mm|ng/ml|μg/ml)',
                    "km": rf'km[^0-9]*(\d+(?:\.\d+)?)\s*(nm|μm|mm|ng/ml|μg/ml)'
                }
                
                for kinetic_type, pattern in kinetic_patterns.items():
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if variant.lower() in text[max(0, match.start()-100):match.end()+100].lower():
                            enzyme_info["kinetic_values"][kinetic_type] = {
                                "value": float(match.group(1)),
                                "unit": match.group(2),
                                "context": match.group(0)
                            }
            
            # Оценка клинической значимости
            enzyme_info["clinical_significance"] = self._assess_clinical_significance(
                text, enzyme_variants
            )
            
            if enzyme_info["interactions"] or enzyme_info["kinetic_values"]:
                cyp_data[enzyme_key] = enzyme_info
        
        return cyp_data
    
    def _extract_transporter_data(self, text: str) -> Dict[str, Any]:
        """Извлекает данные о транспортёрах"""
        transporter_data = {}
        
        for transporter_key, transporter_variants in self.transporters.items():
            transporter_info = {
                "interactions": [],
                "clinical_relevance": "unknown"
            }
            
            for variant in transporter_variants:
                # Паттерны для транспортёров
                patterns = [
                    rf'(\w+(?:\s+\w+)?)\s+(?:is\s+)?(?:a\s+)?substrate\s+(?:of\s+)?{re.escape(variant)}',
                    rf'(\w+(?:\s+\w+)?)\s+inhibits?\s+{re.escape(variant)}',
                    rf'{re.escape(variant)}\s+(?:is\s+)?(?:inhibited|blocked)\s+by\s+(\w+(?:\s+\w+)?)',
                    rf'(\w+(?:\s+\w+)?)\s+(?:affects|modulates)\s+{re.escape(variant)}'
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        interaction_type = "substrate" if "substrate" in match.group(0).lower() else "inhibitor"
                        
                        interaction = {
                            "type": interaction_type,
                            "transporter": variant,
                            "substance": match.group(1).strip(),
                            "evidence": match.group(0),
                            "strength": self._extract_interaction_strength(match.group(0))
                        }
                        transporter_info["interactions"].append(interaction)
            
            if transporter_info["interactions"]:
                transporter_data[transporter_key] = transporter_info
        
        return transporter_data
    
    def _extract_timing_data(self, text: str) -> Dict[str, Any]:
        """Извлекает данные о времени приёма"""
        timing_info = {
            "time_of_day": [],
            "food_relationship": [],
            "frequency": [],
            "sleep_energy_effects": []
        }
        
        # Время дня
        time_patterns = [
            r'(?:take|administer|given)\s+(?:in\s+the\s+)?(?:morning|am)',
            r'(?:take|administer|given)\s+(?:in\s+the\s+)?(?:evening|pm)',
            r'(?:take|administer|given)\s+(?:at\s+)?(?:bedtime|before\s+bed)',
            r'(?:morning|evening|bedtime)\s+(?:dose|administration|dosing)'
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                timing_info["time_of_day"].append({
                    "timing": self._extract_time_from_match(match.group(0)),
                    "context": match.group(0)
                })
        
        # Отношение к еде
        food_patterns = [
            r'(?:with|after)\s+(?:food|meal|eating)',
            r'(?:without\s+food|on\s+empty\s+stomach|fasting)',
            r'(?:before|after)\s+(?:breakfast|lunch|dinner)',
            r'food\s+(?:increases|decreases|affects)\s+(?:absorption|bioavailability)'
        ]
        
        for pattern in food_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                timing_info["food_relationship"].append({
                    "relationship": self._extract_food_relationship(match.group(0)),
                    "context": match.group(0)
                })
        
        # Частота приёма
        frequency_patterns = [
            r'(?:once|twice|three\s+times?)\s+(?:daily|per\s+day)',
            r'(?:every|q)\s*(\d+)\s*(?:hours?|h)',
            r'(\d+)\s*times?\s+(?:daily|per\s+day)',
            r'(?:bid|tid|qid|qd)'
        ]
        
        for pattern in frequency_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                timing_info["frequency"].append({
                    "frequency": self._standardize_frequency(match.group(0)),
                    "context": match.group(0)
                })
        
        return timing_info
    
    def _extract_pharmacokinetic_data(self, text: str) -> Dict[str, Any]:
        """Извлекает фармакокинетические данные"""
        pk_data = {
            "tmax": {},
            "half_life": {},
            "bioavailability": {},
            "food_effects": []
        }
        
        # Tmax (время до пика)
        tmax_patterns = [
            r'tmax[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|minutes?|min)',
            r'peak\s+(?:concentration|plasma\s+level)[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|minutes?|min)',
            r'maximum\s+concentration[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|minutes?|min)'
        ]
        
        for pattern in tmax_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pk_data["tmax"] = {
                    "value": float(match.group(1)),
                    "unit": match.group(2),
                    "context": match.group(0)
                }
                break  # Берём первое найденное значение
        
        # Период полувыведения
        half_life_patterns = [
            r'half[- ]?life[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|days?|d)',
            r't1/2[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|days?|d)'
        ]
        
        for pattern in half_life_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pk_data["half_life"] = {
                    "value": float(match.group(1)),
                    "unit": match.group(2),
                    "context": match.group(0)
                }
                break
        
        # Биодоступность
        bioavailability_patterns = [
            r'bioavailability[^0-9]*(\d+(?:\.\d+)?)\s*%',
            r'oral\s+bioavailability[^0-9]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s+bioavailable'
        ]
        
        for pattern in bioavailability_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pk_data["bioavailability"] = {
                    "value": float(match.group(1)),
                    "unit": "percent",
                    "context": match.group(0)
                }
                break
        
        return pk_data
    
    def _extract_safety_profile(self, text: str) -> Dict[str, Any]:
        """Извлекает профиль безопасности"""
        safety_data = {
            "adverse_effects": [],
            "contraindications": [],
            "warnings": [],
            "monitoring_requirements": [],
            "drug_interactions": []
        }
        
        # Побочные эффекты
        ae_patterns = [
            r'(?:side\s+effects?|adverse\s+(?:effects?|events?|reactions?))[^.]{0,200}',
            r'(?:nausea|headache|dizziness|fatigue|insomnia|diarrhea|constipation)[^.]{0,100}',
            r'(?:hepatotoxicity|nephrotoxicity|cardiotoxicity)[^.]{0,100}'
        ]
        
        for pattern in ae_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                safety_data["adverse_effects"].append({
                    "effect": self._extract_adverse_effect_type(match.group(0)),
                    "severity": self._extract_severity(match.group(0)),
                    "context": match.group(0).strip()
                })
        
        # Противопоказания
        contraindication_patterns = [
            r'contraindicated[^.]{0,150}',
            r'should\s+not\s+be\s+used[^.]{0,150}',
            r'avoid\s+in\s+patients[^.]{0,150}'
        ]
        
        for pattern in contraindication_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                safety_data["contraindications"].append(match.group(0).strip())
        
        return safety_data
    
    def _extract_clinical_data(self, text: str) -> Dict[str, Any]:
        """Извлекает клинические данные"""
        clinical_data = {
            "dosages": [],
            "study_duration": [],
            "participant_count": [],
            "efficacy_measures": []
        }
        
        # Дозировки
        dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(mg|g|mcg|iu|units?)\s*(?:daily|per\s+day|bid|tid)',
            r'dose[s]?\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(mg|g|mcg|iu|units?)',
            r'(\d+(?:\.\d+)?)\s*(mg|g|mcg|iu|units?)\s+(?:once|twice|three\s+times?)\s+daily'
        ]
        
        for pattern in dosage_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                dosage = {
                    "amount": float(groups[0]),
                    "unit": groups[-1],
                    "context": match.group(0),
                    "range_max": float(groups[1]) if len(groups) > 2 and groups[1] else None
                }
                clinical_data["dosages"].append(dosage)
        
        # Количество участников
        participant_patterns = [
            r'(\d+)\s+(?:subjects?|participants?|patients?|volunteers?)',
            r'(?:n\s*=\s*|sample\s+size[^0-9]*)(\d+)',
            r'(\d+)\s+(?:healthy\s+)?(?:adults?|individuals?)'
        ]
        
        for pattern in participant_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                clinical_data["participant_count"].append({
                    "count": int(match.group(1)),
                    "context": match.group(0)
                })
        
        return clinical_data
    
    def _extract_special_populations_data(self, text: str) -> Dict[str, Any]:
        """Извлекает данные об особых группах населения"""
        populations_data = {}
        
        population_categories = {
            "pregnancy": ["pregnancy", "pregnant", "gestation"],
            "lactation": ["lactation", "breastfeeding", "nursing"],
            "elderly": ["elderly", "geriatric", "older adults"],
            "pediatric": ["pediatric", "children", "adolescent"],
            "hepatic_impairment": ["hepatic impairment", "liver disease", "cirrhosis"],
            "renal_impairment": ["renal impairment", "kidney disease", "chronic kidney"]
        }
        
        for category, keywords in population_categories.items():
            findings = []
            for keyword in keywords:
                pattern = rf'{re.escape(keyword)}[^.{{0,200}}.'
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        "recommendation": self._extract_population_recommendation(match.group(0)),
                        "context": match.group(0).strip()
                    })
            
            if findings:
                populations_data[category] = findings
        
        return populations_data
    
    # Вспомогательные методы
    def _identify_substance(self, text: str) -> Optional[str]:
        """Определяет основное вещество в тексте"""
        # Упрощённая версия - можно расширить
        common_substances = [
            "curcumin", "turmeric", "magnesium", "vitamin d", "omega-3",
            "green tea", "caffeine", "quercetin", "resveratrol"
        ]
        
        text_lower = text.lower()
        for substance in common_substances:
            if substance in text_lower:
                return substance
        
        return None
    
    def _extract_interaction_strength(self, evidence: str) -> str:
        """Извлекает силу взаимодействия"""
        evidence_lower = evidence.lower()
        
        if any(word in evidence_lower for word in ["strong", "significant", "marked", "potent", "major"]):
            return "strong"
        elif any(word in evidence_lower for word in ["moderate", "modest"]):
            return "moderate"
        elif any(word in evidence_lower for word in ["weak", "slight", "minor", "minimal"]):
            return "weak"
        else:
            return "moderate"
    
    def _assess_clinical_significance(self, text: str, enzyme_variants: List[str]) -> str:
        """Оценивает клиническую значимость взаимодействия"""
        # Упрощённая логика
        if any(word in text.lower() for word in ["clinically significant", "clinical relevance", "dose adjustment"]):
            return "high"
        elif any(word in text.lower() for word in ["monitor", "caution", "potential"]):
            return "moderate"
        else:
            return "low"
    
    def _extract_time_from_match(self, match_text: str) -> str:
        """Извлекает время из текста"""
        if any(word in match_text.lower() for word in ["morning", "am"]):
            return "morning"
        elif any(word in match_text.lower() for word in ["evening", "pm"]):
            return "evening"
        elif any(word in match_text.lower() for word in ["bedtime", "bed"]):
            return "bedtime"
        else:
            return "unspecified"
    
    def _extract_food_relationship(self, match_text: str) -> str:
        """Извлекает отношение к еде"""
        if any(word in match_text.lower() for word in ["with", "after"]):
            return "with_food"
        elif any(word in match_text.lower() for word in ["without", "empty", "fasting"]):
            return "without_food"
        else:
            return "unspecified"
    
    def _standardize_frequency(self, frequency_text: str) -> str:
        """Стандартизирует частоту приёма"""
        freq_lower = frequency_text.lower()
        
        if any(word in freq_lower for word in ["once", "qd", "daily"]):
            return "once_daily"
        elif any(word in freq_lower for word in ["twice", "bid"]):
            return "twice_daily"
        elif any(word in freq_lower for word in ["three", "tid"]):
            return "three_times_daily"
        elif any(word in freq_lower for word in ["four", "qid"]):
            return "four_times_daily"
        else:
            return frequency_text
    
    def _extract_adverse_effect_type(self, text: str) -> str:
        """Классифицирует тип побочного эффекта"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["nausea", "vomiting", "gastro"]):
            return "gastrointestinal"
        elif any(word in text_lower for word in ["headache", "dizziness", "neuro"]):
            return "neurological"
        elif any(word in text_lower for word in ["hepato", "liver"]):
            return "hepatic"
        elif any(word in text_lower for word in ["cardio", "heart"]):
            return "cardiovascular"
        else:
            return "general"
    
    def _extract_severity(self, text: str) -> str:
        """Извлекает степень тяжести"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["severe", "serious", "major"]):
            return "severe"
        elif any(word in text_lower for word in ["moderate"]):
            return "moderate"
        elif any(word in text_lower for word in ["mild", "minor"]):
            return "mild"
        else:
            return "unspecified"
    
    def _extract_population_recommendation(self, text: str) -> str:
        """Извлекает рекомендацию для популяции"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["contraindicated", "avoid", "not recommended"]):
            return "contraindicated"
        elif any(word in text_lower for word in ["caution", "careful", "monitor"]):
            return "use_with_caution"
        elif any(word in text_lower for word in ["safe", "recommended"]):
            return "recommended"
        else:
            return "insufficient_data"
    
    def _assess_evidence_quality(self, text: str) -> str:
        """Оценивает качество доказательств"""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["randomized controlled trial", "meta-analysis", "systematic review"]):
            return "high"
        elif any(term in text_lower for term in ["clinical trial", "cohort study", "case-control"]):
            return "moderate"
        elif any(term in text_lower for term in ["case report", "in vitro", "animal study"]):
            return "low"
        else:
            return "unknown"
    
    def _calculate_extraction_confidence(self, text: str) -> float:
        """Рассчитывает уверенность в извлечении данных"""
        factors = []
        
        # Длина текста
        text_length_score = min(len(text) / 2000, 1.0)
        factors.append(text_length_score)
        
        # Наличие медицинских терминов
        medical_terms = ["metabolism", "pharmacokinetic", "bioavailability", "half-life", "clearance"]
        term_score = sum(1 for term in medical_terms if term in text.lower()) / len(medical_terms)
        factors.append(term_score)
        
        # Наличие числовых данных
        numbers_found = len(re.findall(r'\d+(?:\.\d+)?', text))
        number_score = min(numbers_found / 10, 1.0)
        factors.append(number_score)
        
        return sum(factors) / len(factors)

def test_comprehensive_extractor():
    """Тестирует комплексный экстрактор"""
    
    extractor = ComprehensiveMedicalExtractor()
    
    # Комплексный тестовый текст
    test_text = """
    Background: Curcumin, the active compound in turmeric, exhibits significant interactions 
    with cytochrome P450 enzymes and drug transporters.
    
    Methods: This randomized controlled trial enrolled 60 healthy volunteers who received 
    curcumin 500 mg twice daily with food for 14 days. CYP3A4 activity was assessed using 
    midazolam as a probe substrate. P-glycoprotein activity was evaluated using digoxin.
    
    Results: Curcumin significantly inhibited CYP3A4 activity (IC50 = 12.3 μM) by 45% (p<0.01). 
    The Tmax of curcumin was 1.5 hours, with a half-life of 6.2 hours. Bioavailability was 
    enhanced by 60% when taken with high-fat meals. Curcumin also inhibited P-glycoprotein 
    transport, increasing digoxin AUC by 25%.
    
    Safety: Mild gastrointestinal side effects (nausea, diarrhea) were reported in 15% of 
    participants. No serious adverse events occurred. Patients taking warfarin should exercise 
    caution due to increased bleeding risk. Clinical monitoring of INR is recommended.
    
    Special Populations: Curcumin is contraindicated in pregnancy due to potential uterine 
    stimulation. Use with caution in patients with hepatic impairment. Dose adjustment may 
    be required in elderly patients (>65 years).
    
    Conclusion: Curcumin moderately inhibits CYP3A4 and P-glycoprotein. Morning administration 
    with food is recommended to optimize bioavailability. Healthcare providers should monitor 
    for drug interactions, particularly with CYP3A4 substrates.
    """
    
    print("🧪 Тестируем комплексный медицинский экстрактор...")
    print("="*80)
    
    result = extractor.extract_comprehensive_data(test_text, "curcumin")
    
    print("📊 КОМПЛЕКСНЫЙ АНАЛИЗ:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_comprehensive_extractor()