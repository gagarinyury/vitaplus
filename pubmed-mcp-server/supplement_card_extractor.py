#!/usr/bin/env python3
"""
Экстрактор полных карточек добавок для VitaPlus
Извлекает ВСЕ данные для создания полноценных карточек добавок
"""

import torch
from transformers import AutoTokenizer, AutoModel
import re
import json
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

class SupplementCardExtractor:
    def __init__(self):
        self.model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
        self.tokenizer = None
        self.model = None
        self.loaded = False
        
        # Базы знаний для экстракции
        self.cyp_enzymes = {
            "CYP3A4": ["CYP3A4", "3A4", "cytochrome p450 3a4"],
            "CYP2D6": ["CYP2D6", "2D6", "cytochrome p450 2d6"],
            "CYP2C9": ["CYP2C9", "2C9", "cytochrome p450 2c9"],
            "CYP2C19": ["CYP2C19", "2C19", "cytochrome p450 2c19"],
            "CYP1A2": ["CYP1A2", "1A2", "cytochrome p450 1a2"],
            "CYP2B6": ["CYP2B6", "2B6", "cytochrome p450 2b6"],
            "CYP2E1": ["CYP2E1", "2E1", "cytochrome p450 2e1"]
        }
        
        self.transporters = {
            "P-glycoprotein": ["P-glycoprotein", "P-gp", "MDR1", "ABCB1"],
            "OATP": ["OATP", "OATP1B1", "OATP1B3", "organic anion transporting polypeptide"],
            "BCRP": ["BCRP", "breast cancer resistance protein", "ABCG2"],
            "OAT": ["OAT", "OAT1", "OAT3", "organic anion transporter"],
            "OCT": ["OCT", "OCT1", "OCT2", "organic cation transporter"]
        }
        
        self.drug_classes = [
            "warfarin", "statins", "beta-blockers", "ACE inhibitors", "calcium channel blockers",
            "digoxin", "phenytoin", "cyclosporine", "tacrolimus", "midazolam", "alprazolam",
            "omeprazole", "clopidogrel", "SSRIs", "tricyclic antidepressants"
        ]
        
    def load_model(self):
        """Загружает PubMedBERT"""
        if self.loaded:
            return
            
        print("🚀 Загружаем PubMedBERT для создания карточек добавок...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.loaded = True
        print("✅ PubMedBERT готов для создания карточек!")
    
    def create_supplement_card(self, 
                             abstract: str, 
                             pmid: str = None,
                             title: str = None,
                             authors: str = None,
                             journal: str = None,
                             year: str = None,
                             supplement_name: str = None) -> Dict[str, Any]:
        """
        Создаёт полную карточку добавки из PubMed статьи
        
        Args:
            abstract: Текст абстракта статьи
            pmid: PubMed ID
            title: Заголовок статьи
            authors: Авторы
            journal: Журнал
            year: Год публикации
            supplement_name: Название добавки
        
        Returns:
            Полная карточка добавки в формате JSON
        """
        if not self.loaded:
            self.load_model()
        
        # Нормализуем текст
        text = self._normalize_text(abstract)
        
        # Создаём полную карточку
        card = {
            # 1. Метаданные статьи
            "article_metadata": {
                "pmid": pmid or self._extract_pmid(text),
                "title": title or self._extract_title(text),
                "authors": authors or self._extract_authors(text),
                "journal": journal or self._extract_journal(text),
                "year": year or self._extract_year(text),
                "study_type": self._classify_study_type(text),
                "sample_size": self._extract_sample_size(text)
            },
            
            # 2. Идентификация добавки
            "supplement": {
                "name": supplement_name or self._identify_supplement(text),
                "alternative_names": self._extract_alternative_names(text),
                "active_compounds": self._extract_active_compounds(text)
            },
            
            # 3. CYP450 профиль
            "cyp450_profile": self._extract_cyp450_profile(text),
            
            # 4. Транспортёры
            "transporters": self._extract_transporter_profile(text),
            
            # 5. Фармакокинетика
            "pharmacokinetics": {
                "bioavailability": self._extract_bioavailability(text),
                "tmax": self._extract_tmax(text),
                "half_life": self._extract_half_life(text),
                "food_effects": self._extract_food_effects(text),
                "metabolism": self._extract_metabolism_info(text)
            },
            
            # 6. Дозировка
            "dosage": {
                "doses": self._extract_doses(text),
                "frequency": self._extract_frequency(text),
                "duration": self._extract_duration(text),
                "route": self._extract_route(text)
            },
            
            # 7. Время приёма
            "administration_timing": {
                "time_of_day": self._extract_time_of_day(text),
                "food_relationship": self._extract_food_relationship(text),
                "drug_spacing": self._extract_drug_spacing(text)
            },
            
            # 8. Безопасность
            "safety": {
                "adverse_effects": self._extract_adverse_effects(text),
                "contraindications": self._extract_contraindications(text),
                "warnings": self._extract_warnings(text),
                "special_populations": self._extract_special_populations(text)
            },
            
            # 9. Взаимодействия
            "interactions": {
                "drug_interactions": self._extract_drug_interactions(text),
                "supplement_interactions": self._extract_supplement_interactions(text),
                "mechanisms": self._extract_interaction_mechanisms(text),
                "clinical_significance": self._assess_interaction_significance(text)
            },
            
            # 10. Физиологические эффекты
            "physiological_effects": {
                "endocrine": self._extract_endocrine_effects(text),
                "nervous_system": self._extract_nervous_system_effects(text),
                "gastrointestinal": self._extract_gi_effects(text),
                "cardiovascular": self._extract_cv_effects(text)
            },
            
            # 11. Рекомендации
            "recommendations": {
                "monitoring": self._extract_monitoring_requirements(text),
                "special_instructions": self._extract_special_instructions(text),
                "combinations": self._extract_combination_recommendations(text)
            },
            
            # 12. Качество данных
            "data_quality": {
                "evidence_level": self._assess_evidence_level(text),
                "extraction_confidence": self._calculate_confidence(text),
                "extraction_date": datetime.now().isoformat(),
                "source": "PubMedBERT analysis"
            }
        }
        
        return card
    
    def _normalize_text(self, text: str) -> str:
        """Нормализует медицинский текст"""
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Стандартизируем медицинские термины
        text = re.sub(r'cytochrome\s+p450\s*(\w+)', r'CYP\1', text, flags=re.IGNORECASE)
        text = re.sub(r'cyp\s*(\w+)', r'CYP\1', text, flags=re.IGNORECASE)
        text = re.sub(r'p-glycoprotein', 'P-glycoprotein', text, flags=re.IGNORECASE)
        
        return text
    
    def _extract_pmid(self, text: str) -> Optional[str]:
        """Извлекает PMID из текста"""
        patterns = [
            r'PMID:\s*(\d+)',
            r'PubMed\s+ID:\s*(\d+)',
            r'pmid\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Извлекает заголовок (если есть в тексте)"""
        # Простая эвристика - первое предложение может быть заголовком
        sentences = text.split('.')
        if sentences and len(sentences[0]) < 200:
            return sentences[0].strip()
        return None
    
    def _extract_authors(self, text: str) -> List[str]:
        """Извлекает авторов"""
        # Паттерны для авторов
        patterns = [
            r'([A-Z][a-z]+\s+[A-Z][A-Z]?),',
            r'([A-Z][a-z]+\s+et\s+al\.)',
        ]
        
        authors = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                authors.append(match.group(1))
        
        return authors[:5]  # Ограничиваем количество
    
    def _extract_journal(self, text: str) -> Optional[str]:
        """Извлекает название журнала"""
        # Ищем типичные названия медицинских журналов
        journal_patterns = [
            r'(Journal of [A-Za-z\s]+)',
            r'([A-Za-z\s]+ Journal)',
            r'(Nature|Science|NEJM|Lancet|JAMA)'
        ]
        
        for pattern in journal_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Извлекает год публикации"""
        # Ищем годы в диапазоне 1990-2025
        pattern = r'\b(19[9]\d|20[0-2]\d)\b'
        matches = re.findall(pattern, text)
        
        if matches:
            # Берём последний год (скорее всего год публикации)
            return int(matches[-1])
        
        return None
    
    def _classify_study_type(self, text: str) -> str:
        """Классифицирует тип исследования"""
        text_lower = text.lower()
        
        study_types = {
            "randomized_controlled_trial": ["randomized controlled trial", "rct", "randomized", "placebo-controlled"],
            "meta_analysis": ["meta-analysis", "systematic review", "meta analysis"],
            "clinical_trial": ["clinical trial", "phase i", "phase ii", "phase iii"],
            "cohort_study": ["cohort study", "prospective study", "longitudinal"],
            "case_control": ["case-control", "case control"],
            "cross_sectional": ["cross-sectional", "cross sectional"],
            "case_report": ["case report", "case series"],
            "in_vitro": ["in vitro", "cell culture", "cell line"],
            "animal_study": ["animal study", "mice", "rats", "in vivo"],
            "review": ["review", "overview", "narrative review"]
        }
        
        for study_type, keywords in study_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return study_type
        
        return "unknown"
    
    def _extract_sample_size(self, text: str) -> Optional[int]:
        """Извлекает размер выборки"""
        patterns = [
            r'n\s*=\s*(\d+)',
            r'(\d+)\s+(?:subjects?|participants?|patients?|volunteers?)',
            r'sample\s+size[^0-9]*(\d+)',
            r'enrolled\s+(\d+)',
            r'(\d+)\s+(?:healthy\s+)?(?:adults?|individuals?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _identify_supplement(self, text: str) -> Optional[str]:
        """Определяет название добавки"""
        supplements = [
            "curcumin", "turmeric", "magnesium", "vitamin d", "vitamin d3",
            "omega-3", "fish oil", "green tea", "egcg", "caffeine",
            "quercetin", "resveratrol", "ginkgo", "ginkgo biloba",
            "st john's wort", "echinacea", "garlic", "ginseng",
            "milk thistle", "saw palmetto", "ashwagandha", "rhodiola",
            "coenzyme q10", "coq10", "alpha-lipoic acid", "melatonin",
            "probiotics", "prebiotics", "zinc", "iron", "calcium",
            "b-complex", "vitamin b12", "folic acid", "biotin"
        ]
        
        text_lower = text.lower()
        for supplement in supplements:
            if supplement in text_lower:
                return supplement
        
        return None
    
    def _extract_alternative_names(self, text: str) -> List[str]:
        """Извлекает альтернативные названия"""
        # Ищем паттерны типа "также известный как", "или"
        patterns = [
            r'also\s+known\s+as\s+([^,\.]+)',
            r'(?:also\s+called|aka)\s+([^,\.]+)',
            r'\(([^)]+)\)'  # Названия в скобках
        ]
        
        alternatives = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if len(name) < 50:  # Фильтруем слишком длинные
                    alternatives.append(name)
        
        return alternatives
    
    def _extract_active_compounds(self, text: str) -> List[str]:
        """Извлекает активные соединения"""
        # Химические названия часто содержат определённые паттерны
        patterns = [
            r'([a-z]+(?:-\d+)*acid)',  # кислоты
            r'([a-z]+(?:ine|ol|ate|ide))',  # химические суффиксы
            r'active\s+compound[s]?\s+([^,\.]+)',
            r'contains?\s+([^,\.]+)'
        ]
        
        compounds = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                compound = match.group(1).strip()
                if 3 < len(compound) < 30:  # Разумная длина
                    compounds.append(compound)
        
        return list(set(compounds))  # Убираем дубликаты
    
    def _extract_cyp450_profile(self, text: str) -> Dict[str, Any]:
        """Извлекает полный CYP450 профиль"""
        cyp_profile = {}
        
        for enzyme, variants in self.cyp_enzymes.items():
            enzyme_data = {
                "interactions": [],
                "kinetic_values": {},
                "clinical_significance": "unknown"
            }
            
            for variant in variants:
                # Ингибирование
                inhibition_patterns = [
                    rf'(\w+(?:\s+\w+)?)\s+(?:significantly|moderately|strongly|potently)?\s*inhibits?\s+{re.escape(variant)}',
                    rf'{re.escape(variant)}\s+(?:is\s+)?inhibited\s+by\s+(\w+(?:\s+\w+)?)',
                    rf'inhibition\s+of\s+{re.escape(variant)}\s+(?:by\s+)?(\w+(?:\s+\w+)?)'
                ]
                
                for pattern in inhibition_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        interaction = {
                            "type": "inhibition",
                            "enzyme": enzyme,
                            "strength": self._extract_strength(match.group(0)),
                            "percentage_change": self._extract_percentage(match.group(0)),
                            "evidence": match.group(0)
                        }
                        enzyme_data["interactions"].append(interaction)
                
                # Индукция
                induction_patterns = [
                    rf'(\w+(?:\s+\w+)?)\s+(?:significantly|moderately|strongly)?\s*induces?\s+{re.escape(variant)}',
                    rf'{re.escape(variant)}\s+(?:is\s+)?induced\s+by\s+(\w+(?:\s+\w+)?)'
                ]
                
                for pattern in induction_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        interaction = {
                            "type": "induction",
                            "enzyme": enzyme,
                            "strength": self._extract_strength(match.group(0)),
                            "fold_change": self._extract_fold_change(match.group(0)),
                            "evidence": match.group(0)
                        }
                        enzyme_data["interactions"].append(interaction)
                
                # Кинетические параметры
                kinetic_patterns = {
                    "ic50": rf'ic50[^0-9]*(\d+(?:\.\d+)?)\s*(nm|μm|mm|ng\/ml|μg\/ml)',
                    "ki": rf'ki[^0-9]*(\d+(?:\.\d+)?)\s*(nm|μm|mm|ng\/ml|μg\/ml)',
                    "km": rf'km[^0-9]*(\d+(?:\.\d+)?)\s*(nm|μm|mm|ng\/ml|μg\/ml)'
                }
                
                for param_type, pattern in kinetic_patterns.items():
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        # Проверяем что это относится к нашему ферменту
                        context = text[max(0, match.start()-200):match.end()+200]
                        if any(v.lower() in context.lower() for v in variants):
                            enzyme_data["kinetic_values"][param_type] = {
                                "value": float(match.group(1)),
                                "unit": match.group(2),
                                "context": match.group(0)
                            }
            
            if enzyme_data["interactions"] or enzyme_data["kinetic_values"]:
                cyp_profile[enzyme] = enzyme_data
        
        return cyp_profile
    
    def _extract_transporter_profile(self, text: str) -> Dict[str, Any]:
        """Извлекает профиль транспортёров"""
        transporter_profile = {}
        
        for transporter, variants in self.transporters.items():
            transporter_data = {
                "substrate": False,
                "inhibitor": False,
                "inducer": False,
                "interactions": [],
                "kinetic_values": {}
            }
            
            for variant in variants:
                # Субстрат
                substrate_patterns = [
                    rf'(\w+(?:\s+\w+)?)\s+(?:is\s+)?(?:a\s+)?substrate\s+(?:of\s+)?{re.escape(variant)}',
                    rf'{re.escape(variant)}\s+substrate',
                    rf'transported\s+by\s+{re.escape(variant)}'
                ]
                
                for pattern in substrate_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        transporter_data["substrate"] = True
                        transporter_data["interactions"].append({
                            "type": "substrate",
                            "transporter": transporter,
                            "evidence": re.search(pattern, text, re.IGNORECASE).group(0)
                        })
                        break
                
                # Ингибитор
                inhibitor_patterns = [
                    rf'(\w+(?:\s+\w+)?)\s+inhibits?\s+{re.escape(variant)}',
                    rf'{re.escape(variant)}\s+(?:is\s+)?inhibited\s+by\s+(\w+(?:\s+\w+)?)'
                ]
                
                for pattern in inhibitor_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        transporter_data["inhibitor"] = True
                        transporter_data["interactions"].append({
                            "type": "inhibition",
                            "transporter": transporter,
                            "strength": self._extract_strength(re.search(pattern, text, re.IGNORECASE).group(0)),
                            "evidence": re.search(pattern, text, re.IGNORECASE).group(0)
                        })
                        break
            
            if any([transporter_data["substrate"], transporter_data["inhibitor"], transporter_data["inducer"]]):
                transporter_profile[transporter] = transporter_data
        
        return transporter_profile
    
    def _extract_bioavailability(self, text: str) -> Optional[Dict[str, Any]]:
        """Извлекает биодоступность"""
        patterns = [
            r'bioavailability[^0-9]*(\d+(?:\.\d+)?)\s*%',
            r'oral\s+bioavailability[^0-9]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s+bioavailable'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "value": float(match.group(1)),
                    "unit": "percent",
                    "context": match.group(0)
                }
        
        return None
    
    def _extract_tmax(self, text: str) -> Optional[Dict[str, Any]]:
        """Извлекает время до максимальной концентрации"""
        patterns = [
            r'tmax[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|minutes?|min)',
            r'peak\s+(?:concentration|plasma\s+level)[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|minutes?|min)',
            r'maximum\s+concentration[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|minutes?|min)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "value": float(match.group(1)),
                    "unit": match.group(2),
                    "context": match.group(0)
                }
        
        return None
    
    def _extract_half_life(self, text: str) -> Optional[Dict[str, Any]]:
        """Извлекает период полувыведения"""
        patterns = [
            r'half[- ]?life[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|days?|d)',
            r't1/2[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|days?|d)',
            r'elimination\s+half[- ]?life[^0-9]*(\d+(?:\.\d+)?)\s*(hours?|h|days?|d)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "value": float(match.group(1)),
                    "unit": match.group(2),
                    "context": match.group(0)
                }
        
        return None
    
    def _extract_metabolism_info(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает информацию о метаболизме"""
        metabolism_info = []
        
        # Паттерны для метаболизма
        patterns = [
            r'metabolized\s+by\s+(\w+)',
            r'metabolism\s+(?:via|through|by)\s+(\w+)',
            r'hepatic\s+metabolism',
            r'first[- ]pass\s+metabolism',
            r'clearance[^0-9]*(\d+(?:\.\d+)?)\s*(ml\/min|l\/h)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                metabolism_info.append({
                    "pathway": match.group(1) if len(match.groups()) > 0 else "hepatic",
                    "context": match.group(0)
                })
        
        return metabolism_info
    
    def _extract_food_effects(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает влияние еды на всасывание"""
        effects = []
        
        patterns = [
            r'food\s+(?:increases|decreases|affects|enhances|reduces)\s+(?:absorption|bioavailability)[^.]{0,100}',
            r'(?:with|without)\s+food[^.]{0,100}(?:absorption|bioavailability)',
            r'(?:high-fat|low-fat)\s+meal[^.]{0,100}',
            r'fasting\s+(?:vs|versus)\s+fed[^.]{0,100}'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                effect_text = match.group(0)
                effect_type = "increase" if any(word in effect_text.lower() for word in ["increases", "enhances", "higher"]) else \
                             "decrease" if any(word in effect_text.lower() for word in ["decreases", "reduces", "lower"]) else \
                             "unknown"
                
                effects.append({
                    "effect_type": effect_type,
                    "description": effect_text.strip(),
                    "magnitude": self._extract_percentage(effect_text)
                })
        
        return effects
    
    def _extract_doses(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает информацию о дозах"""
        doses = []
        
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(mg|g|mcg|iu|units?)\s*(?:daily|per\s+day|bid|tid|qid)',
            r'dose[s]?\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(mg|g|mcg|iu|units?)',
            r'(\d+(?:\.\d+)?)\s*(mg|g|mcg|iu|units?)\s+(?:once|twice|three\s+times?)\s+daily'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                dose_info = {
                    "amount": float(groups[0]),
                    "unit": groups[-1],
                    "range_max": float(groups[1]) if len(groups) > 2 and groups[1] else None,
                    "context": match.group(0),
                    "frequency": self._extract_frequency_from_context(match.group(0))
                }
                doses.append(dose_info)
        
        return doses
    
    def _extract_frequency(self, text: str) -> List[str]:
        """Извлекает частоту приёма"""
        frequencies = []
        
        patterns = [
            r'(?:once|twice|three\s+times?|four\s+times?)\s+(?:daily|per\s+day)',
            r'(?:bid|tid|qid|qd)',
            r'(?:every|q)\s*(\d+)\s*(?:hours?|h)',
            r'(\d+)\s*times?\s+(?:daily|per\s+day)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                freq = self._standardize_frequency(match.group(0))
                if freq not in frequencies:
                    frequencies.append(freq)
        
        return frequencies
    
    def _extract_duration(self, text: str) -> Optional[Dict[str, Any]]:
        """Извлекает длительность курса"""
        patterns = [
            r'(?:for|during)\s+(\d+)\s*(days?|weeks?|months?)',
            r'(\d+)[- ](?:day|week|month)\s+(?:course|treatment|period)',
            r'treatment\s+(?:for|lasting)\s+(\d+)\s*(days?|weeks?|months?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "value": int(match.group(1)),
                    "unit": match.group(2),
                    "context": match.group(0)
                }
        
        return None
    
    def _extract_route(self, text: str) -> str:
        """Извлекает путь введения"""
        routes = ["oral", "intravenous", "topical", "sublingual", "rectal"]
        
        for route in routes:
            if route in text.lower():
                return route
        
        # По умолчанию для добавок
        return "oral"
    
    def _extract_time_of_day(self, text: str) -> List[str]:
        """Извлекает время приёма в течение дня"""
        times = []
        
        time_patterns = {
            "morning": ["morning", "am", "breakfast"],
            "afternoon": ["afternoon", "lunch", "midday"],
            "evening": ["evening", "pm", "dinner"],
            "bedtime": ["bedtime", "before bed", "night"]
        }
        
        for time_name, keywords in time_patterns.items():
            if any(keyword in text.lower() for keyword in keywords):
                times.append(time_name)
        
        return times
    
    def _extract_food_relationship(self, text: str) -> str:
        """Извлекает отношение к приёму пищи"""
        if any(phrase in text.lower() for phrase in ["with food", "with meal", "after eating"]):
            return "with_food"
        elif any(phrase in text.lower() for phrase in ["without food", "empty stomach", "fasting"]):
            return "without_food"
        elif any(phrase in text.lower() for phrase in ["before meal", "before eating"]):
            return "before_food"
        else:
            return "unspecified"
    
    def _extract_drug_spacing(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает информацию о разносе по времени с другими препаратами"""
        spacing_info = []
        
        patterns = [
            r'(?:separate|space)\s+(?:by\s+)?(\d+)\s*(hours?|h|minutes?|min)',
            r'(?:avoid|do not take)\s+(?:within\s+)?(\d+)\s*(hours?|h)\s+of',
            r'take\s+(\d+)\s*(hours?|h)\s+(?:before|after)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                spacing_info.append({
                    "duration": int(match.group(1)),
                    "unit": match.group(2),
                    "context": match.group(0)
                })
        
        return spacing_info
    
    def _extract_adverse_effects(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает побочные эффекты"""
        effects = []
        
        # Общие паттерны для побочных эффектов
        ae_patterns = [
            r'(?:side\s+effects?|adverse\s+(?:effects?|events?|reactions?))[^.]{0,200}',
            r'(?:nausea|headache|dizziness|fatigue|insomnia|diarrhea|constipation|vomiting)[^.]{0,100}',
            r'(?:hepatotoxicity|nephrotoxicity|cardiotoxicity|neurotoxicity)[^.]{0,100}',
            r'(?:rash|allergic\s+reaction|hypersensitivity)[^.]{0,100}'
        ]
        
        for pattern in ae_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                effect_text = match.group(0)
                
                effect = {
                    "effect": self._classify_adverse_effect(effect_text),
                    "severity": self._extract_severity(effect_text),
                    "frequency": self._extract_ae_frequency(effect_text),
                    "context": effect_text.strip()
                }
                effects.append(effect)
        
        return effects
    
    def _extract_contraindications(self, text: str) -> List[str]:
        """Извлекает противопоказания"""
        contraindications = []
        
        patterns = [
            r'contraindicated[^.]{0,150}',
            r'should\s+not\s+be\s+used[^.]{0,150}',
            r'avoid\s+in\s+patients[^.]{0,150}',
            r'do\s+not\s+use[^.]{0,150}'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                contraindications.append(match.group(0).strip())
        
        return contraindications
    
    def _extract_warnings(self, text: str) -> List[str]:
        """Извлекает предупреждения"""
        warnings = []
        
        patterns = [
            r'(?:caution|warning|careful|monitor)[^.]{0,150}',
            r'may\s+(?:increase|cause|lead\s+to)[^.]{0,150}(?:risk|bleeding|toxicity)',
            r'use\s+with\s+caution[^.]{0,150}'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                warnings.append(match.group(0).strip())
        
        return warnings
    
    def _extract_special_populations(self, text: str) -> Dict[str, List[str]]:
        """Извлекает информацию об особых группах населения"""
        populations = {
            "pregnancy": [],
            "lactation": [],
            "elderly": [],
            "pediatric": [],
            "hepatic_impairment": [],
            "renal_impairment": []
        }
        
        population_keywords = {
            "pregnancy": ["pregnancy", "pregnant", "gestation"],
            "lactation": ["lactation", "breastfeeding", "nursing"],
            "elderly": ["elderly", "geriatric", "older adults"],
            "pediatric": ["pediatric", "children", "adolescent"],
            "hepatic_impairment": ["hepatic impairment", "liver disease", "cirrhosis"],
            "renal_impairment": ["renal impairment", "kidney disease", "chronic kidney"]
        }
        
        for category, keywords in population_keywords.items():
            for keyword in keywords:
                pattern = rf'{re.escape(keyword)}[^.]{0,200}'
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    populations[category].append(match.group(0).strip())
        
        return {k: v for k, v in populations.items() if v}  # Убираем пустые
    
    def _extract_drug_interactions(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает лекарственные взаимодействия"""
        interactions = []
        
        for drug_class in self.drug_classes:
            pattern = rf'(?:with|and)\s+{re.escape(drug_class)}[^.]{0,100}'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                interaction_text = match.group(0)
                
                interaction = {
                    "drug": drug_class,
                    "interaction_type": self._classify_interaction_type(interaction_text),
                    "clinical_significance": self._assess_clinical_significance(interaction_text),
                    "mechanism": self._extract_mechanism(interaction_text),
                    "context": interaction_text.strip()
                }
                interactions.append(interaction)
        
        return interactions
    
    def _extract_supplement_interactions(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает взаимодействия с другими добавками"""
        interactions = []
        
        supplement_names = [
            "vitamin c", "vitamin e", "iron", "calcium", "zinc",
            "magnesium", "fish oil", "omega-3", "probiotics"
        ]
        
        for supplement in supplement_names:
            pattern = rf'(?:with|and)\s+{re.escape(supplement)}[^.]{0,100}'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                interaction_text = match.group(0)
                
                interaction = {
                    "supplement": supplement,
                    "interaction_type": self._classify_interaction_type(interaction_text),
                    "recommendation": self._extract_interaction_recommendation(interaction_text),
                    "context": interaction_text.strip()
                }
                interactions.append(interaction)
        
        return interactions
    
    def _extract_endocrine_effects(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает эндокринные эффекты"""
        effects = []
        
        endocrine_keywords = [
            "cortisol", "insulin", "glucose", "thyroid", "testosterone",
            "estrogen", "growth hormone", "adrenaline", "melatonin"
        ]
        
        for keyword in endocrine_keywords:
            pattern = rf'{re.escape(keyword)}[^.]{0,150}'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                effect_text = match.group(0)
                
                effect = {
                    "hormone": keyword,
                    "effect_type": self._classify_endocrine_effect(effect_text),
                    "magnitude": self._extract_percentage(effect_text),
                    "context": effect_text.strip()
                }
                effects.append(effect)
        
        return effects
    
    def _extract_nervous_system_effects(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает эффекты на нервную систему"""
        effects = []
        
        ns_keywords = [
            "sleep", "sedative", "stimulating", "alertness", "energy",
            "anxiety", "depression", "mood", "cognitive", "memory"
        ]
        
        for keyword in ns_keywords:
            if keyword in text.lower():
                context = self._extract_context_around_keyword(text, keyword)
                
                effect = {
                    "effect_type": keyword,
                    "direction": self._classify_effect_direction(context),
                    "context": context
                }
                effects.append(effect)
        
        return effects
    
    def _extract_gi_effects(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает эффекты на ЖКТ"""
        effects = []
        
        gi_keywords = [
            "nausea", "vomiting", "diarrhea", "constipation", "bloating",
            "stomach", "gastric", "intestinal", "absorption"
        ]
        
        for keyword in gi_keywords:
            if keyword in text.lower():
                context = self._extract_context_around_keyword(text, keyword)
                
                effect = {
                    "effect_type": keyword,
                    "severity": self._extract_severity(context),
                    "frequency": self._extract_ae_frequency(context),
                    "context": context
                }
                effects.append(effect)
        
        return effects
    
    def _extract_cv_effects(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает сердечно-сосудистые эффекты"""
        effects = []
        
        cv_keywords = [
            "blood pressure", "heart rate", "cardiac", "vascular",
            "circulation", "hypertension", "hypotension", "arrhythmia"
        ]
        
        for keyword in cv_keywords:
            if keyword in text.lower():
                context = self._extract_context_around_keyword(text, keyword)
                
                effect = {
                    "effect_type": keyword,
                    "direction": self._classify_effect_direction(context),
                    "clinical_significance": self._assess_clinical_significance(context),
                    "context": context
                }
                effects.append(effect)
        
        return effects
    
    def _extract_monitoring_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает требования к мониторингу"""
        monitoring = []
        
        monitoring_keywords = [
            "monitor", "blood test", "laboratory", "liver function",
            "kidney function", "INR", "glucose", "blood pressure"
        ]
        
        for keyword in monitoring_keywords:
            if keyword in text.lower():
                context = self._extract_context_around_keyword(text, keyword)
                
                monitor_item = {
                    "parameter": keyword,
                    "frequency": self._extract_monitoring_frequency(context),
                    "reason": self._extract_monitoring_reason(context),
                    "context": context
                }
                monitoring.append(monitor_item)
        
        return monitoring
    
    def _extract_special_instructions(self, text: str) -> List[str]:
        """Извлекает особые указания"""
        instructions = []
        
        instruction_patterns = [
            r'(?:recommend|advise|suggest)[^.]{0,150}',
            r'patients\s+should[^.]{0,150}',
            r'important[^.]{0,150}',
            r'note[^.]{0,150}'
        ]
        
        for pattern in instruction_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                instructions.append(match.group(0).strip())
        
        return instructions
    
    def _extract_combination_recommendations(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает рекомендации по комбинациям"""
        combinations = []
        
        combination_patterns = [
            r'(?:combine|combination)\s+with[^.]{0,150}',
            r'(?:avoid|do not)\s+combine[^.]{0,150}',
            r'synergistic\s+(?:with|effect)[^.]{0,150}'
        ]
        
        for pattern in combination_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                combo_text = match.group(0)
                
                combination = {
                    "recommendation_type": "positive" if any(word in combo_text.lower() for word in ["combine", "synergistic"]) else "negative",
                    "substances": self._extract_substances_from_text(combo_text),
                    "rationale": self._extract_combination_rationale(combo_text),
                    "context": combo_text.strip()
                }
                combinations.append(combination)
        
        return combinations
    
    # Вспомогательные методы для классификации и извлечения
    
    def _extract_strength(self, text: str) -> str:
        """Извлекает силу эффекта"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["strong", "significant", "marked", "potent", "major"]):
            return "strong"
        elif any(word in text_lower for word in ["moderate", "modest"]):
            return "moderate"
        elif any(word in text_lower for word in ["weak", "slight", "minor", "minimal"]):
            return "weak"
        else:
            return "moderate"
    
    def _extract_percentage(self, text: str) -> Optional[float]:
        """Извлекает процентное изменение"""
        pattern = r'(\d+(?:\.\d+)?)\s*%'
        match = re.search(pattern, text)
        
        if match:
            return float(match.group(1))
        
        return None
    
    def _extract_fold_change(self, text: str) -> Optional[float]:
        """Извлекает кратность изменения"""
        pattern = r'(\d+(?:\.\d+)?)[- ]fold'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return float(match.group(1))
        
        return None
    
    def _extract_frequency_from_context(self, context: str) -> str:
        """Извлекает частоту из контекста"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ["once", "qd", "daily"]):
            return "once_daily"
        elif any(word in context_lower for word in ["twice", "bid"]):
            return "twice_daily"
        elif any(word in context_lower for word in ["three", "tid"]):
            return "three_times_daily"
        elif any(word in context_lower for word in ["four", "qid"]):
            return "four_times_daily"
        else:
            return "unspecified"
    
    def _standardize_frequency(self, frequency_text: str) -> str:
        """Стандартизирует частоту приёма"""
        freq_lower = frequency_text.lower()
        
        if any(word in freq_lower for word in ["once", "qd"]):
            return "once_daily"
        elif any(word in freq_lower for word in ["twice", "bid"]):
            return "twice_daily"
        elif any(word in freq_lower for word in ["three", "tid"]):
            return "three_times_daily"
        elif any(word in freq_lower for word in ["four", "qid"]):
            return "four_times_daily"
        else:
            return frequency_text
    
    def _classify_adverse_effect(self, text: str) -> str:
        """Классифицирует побочный эффект"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["nausea", "vomiting", "diarrhea", "constipation"]):
            return "gastrointestinal"
        elif any(word in text_lower for word in ["headache", "dizziness", "fatigue"]):
            return "neurological"
        elif any(word in text_lower for word in ["rash", "allergic", "hypersensitivity"]):
            return "allergic"
        elif any(word in text_lower for word in ["hepato", "liver"]):
            return "hepatic"
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
    
    def _extract_ae_frequency(self, text: str) -> Optional[str]:
        """Извлекает частоту побочных эффектов"""
        pattern = r'(\d+(?:\.\d+)?)\s*%\s+(?:of\s+)?(?:patients|subjects)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            percentage = float(match.group(1))
            if percentage < 1:
                return "rare"
            elif percentage < 10:
                return "uncommon"
            elif percentage < 30:
                return "common"
            else:
                return "very_common"
        
        return None
    
    def _classify_interaction_type(self, text: str) -> str:
        """Классифицирует тип взаимодействия"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["increase", "enhance", "potentiate"]):
            return "synergistic"
        elif any(word in text_lower for word in ["decrease", "reduce", "inhibit"]):
            return "antagonistic"
        elif any(word in text_lower for word in ["avoid", "contraindicated"]):
            return "contraindicated"
        else:
            return "unknown"
    
    def _assess_clinical_significance(self, text: str) -> str:
        """Оценивает клиническую значимость"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["clinically significant", "major", "serious"]):
            return "high"
        elif any(word in text_lower for word in ["moderate", "monitor", "caution"]):
            return "moderate"
        elif any(word in text_lower for word in ["minor", "unlikely", "minimal"]):
            return "low"
        else:
            return "unknown"
    
    def _extract_mechanism(self, text: str) -> Optional[str]:
        """Извлекает механизм взаимодействия"""
        mechanisms = [
            "cyp450 inhibition", "cyp450 induction", "p-glycoprotein",
            "protein binding", "renal clearance", "hepatic metabolism"
        ]
        
        text_lower = text.lower()
        for mechanism in mechanisms:
            if mechanism in text_lower:
                return mechanism
        
        return None
    
    def _extract_interaction_recommendation(self, text: str) -> str:
        """Извлекает рекомендацию по взаимодействию"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["avoid", "contraindicated"]):
            return "avoid"
        elif any(word in text_lower for word in ["monitor", "caution"]):
            return "monitor"
        elif any(word in text_lower for word in ["safe", "no interaction"]):
            return "safe"
        else:
            return "unknown"
    
    def _classify_endocrine_effect(self, text: str) -> str:
        """Классифицирует эндокринный эффект"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["increase", "elevate", "raise"]):
            return "increase"
        elif any(word in text_lower for word in ["decrease", "reduce", "lower"]):
            return "decrease"
        elif any(word in text_lower for word in ["modulate", "regulate"]):
            return "modulate"
        else:
            return "unknown"
    
    def _classify_effect_direction(self, text: str) -> str:
        """Классифицирует направление эффекта"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["improve", "enhance", "increase", "stimulate"]):
            return "positive"
        elif any(word in text_lower for word in ["worsen", "decrease", "inhibit", "reduce"]):
            return "negative"
        else:
            return "neutral"
    
    def _extract_context_around_keyword(self, text: str, keyword: str, window: int = 100) -> str:
        """Извлекает контекст вокруг ключевого слова"""
        pattern = rf'.{{0,{window}}}{re.escape(keyword)}.{{0,{window}}}'
        match = re.search(pattern, text, re.IGNORECASE)
        
        return match.group(0) if match else ""
    
    def _extract_monitoring_frequency(self, text: str) -> Optional[str]:
        """Извлекает частоту мониторинга"""
        frequencies = ["weekly", "monthly", "quarterly", "annually", "daily"]
        
        text_lower = text.lower()
        for frequency in frequencies:
            if frequency in text_lower:
                return frequency
        
        return None
    
    def _extract_monitoring_reason(self, text: str) -> Optional[str]:
        """Извлекает причину мониторинга"""
        reasons = ["toxicity", "efficacy", "safety", "interaction", "side effects"]
        
        text_lower = text.lower()
        for reason in reasons:
            if reason in text_lower:
                return reason
        
        return None
    
    def _extract_substances_from_text(self, text: str) -> List[str]:
        """Извлекает названия веществ из текста"""
        substances = []
        
        # Простой список известных веществ
        known_substances = [
            "vitamin c", "vitamin d", "calcium", "magnesium", "iron", "zinc",
            "omega-3", "fish oil", "curcumin", "green tea"
        ]
        
        text_lower = text.lower()
        for substance in known_substances:
            if substance in text_lower:
                substances.append(substance)
        
        return substances
    
    def _extract_combination_rationale(self, text: str) -> Optional[str]:
        """Извлекает обоснование комбинации"""
        rationales = [
            "synergistic effect", "enhanced absorption", "reduced side effects",
            "complementary action", "antagonistic effect"
        ]
        
        text_lower = text.lower()
        for rationale in rationales:
            if rationale in text_lower:
                return rationale
        
        return None
    
    def _assess_evidence_level(self, text: str) -> str:
        """Оценивает уровень доказательности"""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["randomized controlled trial", "meta-analysis", "systematic review"]):
            return "high"
        elif any(term in text_lower for term in ["clinical trial", "cohort study", "case-control"]):
            return "moderate"
        elif any(term in text_lower for term in ["case report", "in vitro", "animal study"]):
            return "low"
        else:
            return "unknown"
    
    def _calculate_confidence(self, text: str) -> float:
        """Рассчитывает уверенность в извлечении данных"""
        factors = []
        
        # Длина текста
        text_length_score = min(len(text) / 3000, 1.0)
        factors.append(text_length_score)
        
        # Наличие медицинских терминов
        medical_terms = [
            "metabolism", "pharmacokinetic", "bioavailability", "half-life",
            "clearance", "cyp450", "interaction", "adverse", "contraindicated"
        ]
        term_score = sum(1 for term in medical_terms if term in text.lower()) / len(medical_terms)
        factors.append(term_score)
        
        # Наличие числовых данных
        numbers_found = len(re.findall(r'\d+(?:\.\d+)?', text))
        number_score = min(numbers_found / 15, 1.0)
        factors.append(number_score)
        
        # Наличие специфических паттернов
        specific_patterns = [
            r'ic50', r'ki', r'tmax', r'bioavailability', r'half[- ]?life',
            r'pmid', r'n\s*=', r'p\s*<', r'%'
        ]
        pattern_score = sum(1 for pattern in specific_patterns if re.search(pattern, text, re.IGNORECASE)) / len(specific_patterns)
        factors.append(pattern_score)
        
        return sum(factors) / len(factors)
    
    def _extract_interaction_mechanisms(self, text: str) -> List[str]:
        """Извлекает механизмы взаимодействий"""
        mechanisms = []
        
        mechanism_patterns = [
            r'cyp450\s+inhibition',
            r'cyp450\s+induction', 
            r'p-glycoprotein\s+inhibition',
            r'protein\s+binding\s+displacement',
            r'renal\s+clearance',
            r'hepatic\s+metabolism',
            r'absorption\s+interference'
        ]
        
        for pattern in mechanism_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                mechanisms.append(pattern.replace('\\s+', ' '))
        
        return mechanisms
    
    def _assess_interaction_significance(self, text: str) -> str:
        """Оценивает общую значимость взаимодействий"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["clinically significant", "major interaction", "contraindicated"]):
            return "high"
        elif any(word in text_lower for word in ["moderate", "monitor", "caution"]):
            return "moderate"
        elif any(word in text_lower for word in ["minor", "unlikely", "no significant"]):
            return "low"
        else:
            return "unknown"

def test_supplement_card_extractor():
    """Тестирует экстрактор карточек добавок"""
    
    extractor = SupplementCardExtractor()
    
    # Комплексный тестовый абстракт
    test_abstract = """
    PMID: 12345678
    Title: Effects of curcumin supplementation on cytochrome P450 enzymes and drug interactions
    Authors: Smith J, Johnson A, Brown K, et al.
    Journal: Clinical Pharmacology & Therapeutics
    Year: 2023
    
    Background: Curcumin, the principal bioactive compound in turmeric (Curcuma longa), 
    has gained popularity as a dietary supplement. However, its potential for drug 
    interactions through cytochrome P450 enzyme modulation remains unclear.
    
    Methods: This randomized, double-blind, placebo-controlled trial enrolled 120 healthy 
    volunteers (aged 18-65 years) who received curcumin 500 mg twice daily with food or 
    placebo for 28 days. CYP3A4 activity was assessed using midazolam as a probe substrate. 
    P-glycoprotein activity was evaluated using digoxin. Safety assessments included liver 
    function tests and adverse event monitoring.
    
    Results: Curcumin significantly inhibited CYP3A4 activity (IC50 = 8.2 μM) by 35% 
    compared to placebo (p<0.001). The Tmax of curcumin was 2.1 ± 0.5 hours, with an 
    elimination half-life of 6.8 ± 1.2 hours. Oral bioavailability was 45% and increased 
    by 60% when taken with high-fat meals. Curcumin also inhibited P-glycoprotein transport, 
    increasing digoxin AUC by 28% (p<0.01).
    
    Safety: Mild gastrointestinal adverse effects (nausea 12%, diarrhea 8%) were reported. 
    No serious adverse events occurred. Liver function tests remained within normal limits. 
    Patients taking warfarin showed increased INR values, requiring dose adjustment in 3 cases.
    
    Drug Interactions: Significant interactions were observed with CYP3A4 substrates including 
    simvastatin (40% increase in AUC), midazolam (50% increase), and cyclosporine (25% increase). 
    Clinical monitoring is recommended when curcumin is co-administered with these medications.
    
    Special Populations: Curcumin is contraindicated in pregnancy due to potential uterine 
    stimulation. Use with caution in patients with hepatic impairment. Elderly patients 
    (>75 years) showed 30% higher plasma concentrations.
    
    Physiological Effects: Curcumin reduced cortisol levels by 15% (p<0.05) and improved 
    sleep quality scores. No effects on blood pressure or heart rate were observed. 
    Morning administration was associated with better tolerability.
    
    Recommendations: Curcumin should be taken in the morning with food to optimize absorption. 
    Separate administration from CYP3A4 substrates by at least 2 hours. Monthly liver function 
    monitoring is recommended for long-term use (>3 months). Avoid combination with anticoagulants 
    unless under medical supervision.
    
    Conclusion: Curcumin 500 mg twice daily moderately inhibits CYP3A4 and P-glycoprotein, 
    leading to clinically significant drug interactions. Healthcare providers should be 
    aware of these interactions and implement appropriate monitoring strategies.
    """
    
    print("🧪 Тестируем экстрактор полных карточек добавок...")
    print("="*90)
    
    card = extractor.create_supplement_card(
        abstract=test_abstract,
        pmid="12345678",
        supplement_name="curcumin"
    )
    
    print("📊 ПОЛНАЯ КАРТОЧКА ДОБАВКИ:")
    print(json.dumps(card, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_supplement_card_extractor()