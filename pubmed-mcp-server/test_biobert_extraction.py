#!/usr/bin/env python3
"""
Тестовый скрипт для BioBERT и PubMedBERT
Проверяем что они реально извлекают из медицинских текстов
"""

import torch
from transformers import AutoTokenizer, AutoModel, pipeline
import re
import json
from typing import Dict, List, Any

class BiomedicalExtractorTester:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.ner_pipelines = {}
        
        # Модели для тестирования
        self.model_configs = {
            "PubMedBERT": "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract",
            "BioBERT": "dmis-lab/biobert-base-cased-v1.2",
            "BlueBERT": "bionlp/bluebert_pubmed_mimic_uncased_L-12_H-768_A-12"
        }
        
    def load_models(self):
        """Загружает все модели для сравнения"""
        print("🚀 Загружаем модели для тестирования...")
        
        for model_name, model_path in self.model_configs.items():
            try:
                print(f"   📦 Загружаем {model_name}...")
                
                # Основная модель
                self.tokenizers[model_name] = AutoTokenizer.from_pretrained(model_path)
                self.models[model_name] = AutoModel.from_pretrained(model_path)
                
                # NER pipeline (если доступен)
                try:
                    self.ner_pipelines[model_name] = pipeline(
                        "token-classification",
                        model=model_path,
                        tokenizer=model_path,
                        aggregation_strategy="simple"
                    )
                    print(f"   ✅ {model_name} загружен с NER")
                except:
                    print(f"   ⚠️  {model_name} загружен без NER")
                    
            except Exception as e:
                print(f"   ❌ Ошибка загрузки {model_name}: {e}")
    
    def load_supplement_data(self, json_path: str) -> List[Dict]:
        """Загружает данные из supplement_data_avocado.json"""
        try:
            print(f"📂 Загружаем данные из: {json_path}")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Собираем все абстракты из всех категорий
            all_abstracts = []
            
            # Проходим по всем секциям данных
            for section_name, section_data in data.items():
                if isinstance(section_data, dict):
                    # Проверяем структуру: может быть 'results' или 'articles'
                    articles_dict = None
                    if 'results' in section_data:
                        articles_dict = section_data['results']
                    elif 'articles' in section_data:
                        articles_dict = section_data['articles']
                    elif section_name in ['meta_analysis', 'rct_mesh', 'rct_tiab', 'clinical_trials', 'human_studies', 
                                        'safety_adverse', 'safety_case_reports', 'interactions', 'pharmacology', 
                                        'mechanisms', 'bioavailability', 'body_systems']:
                        # Если это основная секция, ищем articles внутри
                        articles_dict = section_data.get('articles', {})
                    
                    if articles_dict:
                        print(f"   📊 Секция {section_name}: {len(articles_dict)} исследований")
                        
                        for pmid, study_data in articles_dict.items():
                            if isinstance(study_data, dict) and 'abstract' in study_data:
                                abstract_text = study_data['abstract']
                                if abstract_text and len(abstract_text.strip()) > 50:  # Минимальная длина
                                    all_abstracts.append({
                                        'pmid': pmid,
                                        'section': section_name,
                                        'title': study_data.get('title', ''),
                                        'abstract': abstract_text,
                                        'journal': study_data.get('journal', ''),
                                        'authors': study_data.get('authors', [])
                                    })
            
            print(f"✅ Загружено {len(all_abstracts)} абстрактов для анализа")
            return all_abstracts
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return []

    def test_real_pubmed_abstracts(self, supplement_data_path: str = None):
        """Тестирует на реальных медицинских абстрактах"""
        
        if supplement_data_path:
            # Тестируем на реальных данных авокадо
            print("\n" + "="*80)
            print("🥑 АНАЛИЗ РЕАЛЬНЫХ ДАННЫХ АВОКАДО ИЗ PUBMED")
            print("="*80)
            
            abstracts_data = self.load_supplement_data(supplement_data_path)
            if not abstracts_data:
                print("❌ Не удалось загрузить данные, используем тестовые примеры")
                self.test_sample_abstracts()
                return
            
            # Берем первые 20 абстрактов для тестирования (чтобы не перегружать)
            sample_abstracts = abstracts_data[:20]
            
            print(f"\n📊 Анализируем {len(sample_abstracts)} абстрактов из {len(abstracts_data)} загруженных")
            
            # Статистика по моделям
            model_stats = {model: {'total_entities': 0, 'processed': 0} for model in self.models.keys()}
            all_extracted_data = []
            
            for i, abstract_data in enumerate(sample_abstracts):
                print(f"\n📄 АБСТРАКТ {i+1}/{len(sample_abstracts)}")
                print(f"   PMID: {abstract_data['pmid']}")
                print(f"   Секция: {abstract_data['section']}")
                print(f"   Заголовок: {abstract_data['title'][:100]}...")
                print("-" * 60)
                
                abstract_text = abstract_data['abstract']
                
                # Анализируем каждой моделью
                abstract_results = {
                    'pmid': abstract_data['pmid'],
                    'section': abstract_data['section'],
                    'title': abstract_data['title'],
                    'models': {}
                }
                
                for model_name in self.models.keys():
                    print(f"\n🤖 {model_name}:")
                    
                    # NER извлечение
                    entities = self.extract_entities(abstract_text, model_name)
                    model_stats[model_name]['total_entities'] += len(entities)
                    model_stats[model_name]['processed'] += 1
                    
                    # Специфические медицинские данные
                    specific_data = self.extract_specific_medical_data(abstract_text)
                    
                    print(f"   📊 NER сущности: {len(entities)}")
                    print(f"   🎯 CYP450: {len(specific_data['cyp450'])}")
                    print(f"   🎯 Дозировки: {len(specific_data['dosages'])}")
                    print(f"   🎯 Побочные эффекты: {len(specific_data['adverse_effects'])}")
                    print(f"   🎯 Кинетические значения: {len(specific_data['kinetic_values'])}")
                    print(f"   🎯 Участники: {len(specific_data['study_participants'])}")
                    print(f"   🎯 Биодоступность: {len(specific_data['bioavailability'])}")
                    
                    # Сохраняем результаты
                    abstract_results['models'][model_name] = {
                        'entities_count': len(entities),
                        'entities': entities[:5],  # Первые 5 для примера
                        'extracted_data': specific_data
                    }
                
                all_extracted_data.append(abstract_results)
            
            # Итоговая статистика
            print("\n" + "="*80)
            print("📈 ИТОГОВАЯ СТАТИСТИКА ПО МОДЕЛЯМ")
            print("="*80)
            
            for model_name, stats in model_stats.items():
                avg_entities = stats['total_entities'] / stats['processed'] if stats['processed'] > 0 else 0
                print(f"\n🤖 {model_name}:")
                print(f"   📊 Обработано абстрактов: {stats['processed']}")
                print(f"   📊 Всего сущностей: {stats['total_entities']}")
                print(f"   📊 В среднем на абстракт: {avg_entities:.1f}")
            
            # Сохраняем подробные результаты
            output_file = '/Users/yurygagarin/Code/1/vitaplus/pubmed-mcp-server/avocado_analysis_results.json'
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Подробные результаты сохранены в: {output_file}")
            except Exception as e:
                print(f"⚠️ Не удалось сохранить результаты: {e}")
        else:
            self.test_sample_abstracts()
    
    def test_sample_abstracts(self):
        """Тестирует на примерах абстрактов (fallback)"""
        
        # Реальные примеры абстрактов
        test_abstracts = {
            "curcumin_cyp": """
            Background: Curcumin significantly inhibits cytochrome P450 3A4 (CYP3A4) enzyme activity 
            in human liver microsomes with an IC50 value of 8.2 μM. This study investigated the clinical 
            significance of curcumin-drug interactions.
            
            Methods: Healthy volunteers (n=24) received curcumin 500 mg twice daily for 14 days. 
            CYP3A4 activity was assessed using midazolam 2 mg as a probe substrate.
            
            Results: Curcumin decreased midazolam clearance by 35% (p<0.01), increasing AUC from 
            12.3 ± 2.1 to 18.7 ± 3.4 ng·h/mL. Tmax increased from 0.8 to 1.2 hours. Two subjects 
            experienced mild nausea. No serious adverse events occurred.
            
            Conclusion: Curcumin moderately inhibits CYP3A4 and may cause clinically significant 
            interactions with CYP3A4 substrates like statins and calcium channel blockers.
            """,
            
            "magnesium_safety": """
            Background: Magnesium supplementation is generally well-tolerated, but high doses 
            may cause gastrointestinal side effects.
            
            Methods: A systematic review of 15 randomized controlled trials (n=1,847) evaluated 
            magnesium safety at doses ranging from 200-800 mg daily.
            
            Results: Diarrhea occurred in 23% of subjects taking >400 mg daily vs 8% with placebo 
            (p<0.001). Nausea was reported in 12% vs 4% (p<0.05). No cases of hypermagnesemia 
            were observed in subjects with normal kidney function. Bioavailability was 45% for 
            magnesium oxide and 68% for magnesium glycinate.
            
            Contraindications: Avoid in severe renal impairment (GFR <30 mL/min). Use caution 
            with digoxin and aminoglycosides.
            """,
            
            "no_data_supplement": """
            Background: Lion's Mane mushroom (Hericium erinaceus) contains hericenones and 
            erinacines that may support cognitive function.
            
            Methods: This preliminary study examined the neuroprotective effects in cell culture.
            
            Results: Beta-glucans showed antioxidant activity in vitro. No human pharmacokinetic 
            data is available. Drug interactions have not been studied.
            
            Conclusion: More research is needed to determine safety and efficacy in humans.
            """
        }
        
        print("\n" + "="*80)
        print("🧪 ТЕСТИРОВАНИЕ ИЗВЛЕЧЕНИЯ ДАННЫХ ИЗ РЕАЛЬНЫХ АБСТРАКТОВ")
        print("="*80)
        
        for abstract_name, abstract_text in test_abstracts.items():
            print(f"\n📄 АБСТРАКТ: {abstract_name.upper()}")
            print("-" * 60)
            
            # Тестируем каждую модель
            for model_name in self.models.keys():
                print(f"\n🤖 МОДЕЛЬ: {model_name}")
                
                # 1. NER извлечение
                entities = self.extract_entities(abstract_text, model_name)
                print(f"   📊 Найдено сущностей: {len(entities)}")
                
                # Показываем первые 5 сущностей
                for i, entity in enumerate(entities[:5]):
                    print(f"      {i+1}. {entity.get('word', 'N/A')} -> {entity.get('entity_group', 'N/A')} (conf: {entity.get('score', 0):.2f})")
                
                # 2. Извлечение специфических данных
                specific_data = self.extract_specific_medical_data(abstract_text)
                print(f"   🎯 CYP450 данные: {len(specific_data['cyp450'])}")
                print(f"   🎯 Дозировки: {len(specific_data['dosages'])}")
                print(f"   🎯 Побочные эффекты: {len(specific_data['adverse_effects'])}")
                print(f"   🎯 IC50/Ki значения: {len(specific_data['kinetic_values'])}")
    
    def extract_entities(self, text: str, model_name: str) -> List[Dict]:
        """Извлекает медицинские сущности с помощью NER"""
        if model_name in self.ner_pipelines:
            try:
                entities = self.ner_pipelines[model_name](text)
                return entities
            except Exception as e:
                print(f"      ❌ Ошибка NER для {model_name}: {e}")
        
        return []
    
    def extract_specific_medical_data(self, text: str) -> Dict[str, List]:
        """Извлекает специфические медицинские данные с помощью regex"""
        
        data = {
            "cyp450": [],
            "dosages": [],
            "adverse_effects": [],
            "kinetic_values": [],
            "study_participants": [],
            "bioavailability": [],
            "contraindications": []
        }
        
        # CYP450 данные
        cyp_patterns = [
            r'(CYP\w+)\s+(?:activity|enzyme)',
            r'cytochrome\s+p450\s+(\w+)',
            r'(CYP\w+)\s+(?:inhibition|substrate|induction)'
        ]
        
        for pattern in cyp_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                data["cyp450"].append({
                    "enzyme": match.group(1),
                    "context": match.group(0)
                })
        
        # Дозировки
        dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(mg|g|mcg|μg)\s+(?:daily|twice\s+daily|once\s+daily)',
            r'doses?\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(mg|g|mcg|μg)',
            r'(\d+(?:\.\d+)?)\s*(mg|g|mcg|μg)\s+(?:per\s+day|bid|tid)'
        ]
        
        for pattern in dosage_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                data["dosages"].append({
                    "amount": match.group(1),
                    "unit": match.group(2),
                    "context": match.group(0)
                })
        
        # Кинетические значения
        kinetic_patterns = [
            r'ic50[^\d]*(\d+(?:\.\d+)?)\s*(nm|μm|mm)',
            r'ki[^\d]*(\d+(?:\.\d+)?)\s*(nm|μm|mm)',
            r'auc[^\d]*(\d+(?:\.\d+)?)',
            r'tmax[^\d]*(\d+(?:\.\d+)?)\s*(hours?|h|min)'
        ]
        
        for pattern in kinetic_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                data["kinetic_values"].append({
                    "parameter": pattern.split('[')[0],
                    "value": match.group(1),
                    "unit": match.group(2) if len(match.groups()) > 1 else "",
                    "context": match.group(0)
                })
        
        # Побочные эффекты
        ae_patterns = [
            r'(nausea|diarrhea|headache|dizziness)\s+(?:occurred\s+in\s+)?(\d+)%',
            r'(\d+)%\s+(?:of\s+(?:subjects|patients))?\s+experienced\s+(\w+)',
            r'side\s+effects?\s+include[d]?\s+([^.]+)'
        ]
        
        for pattern in ae_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                data["adverse_effects"].append({
                    "effect": match.group(1) if match.group(1) else match.group(2),
                    "frequency": match.group(2) if match.group(2) and match.group(2).isdigit() else None,
                    "context": match.group(0)
                })
        
        # Участники исследования
        participant_patterns = [
            r'(?:n\s*=\s*)?(\d+)\s+(?:subjects?|patients?|volunteers?)',
            r'(\d+)\s+(?:healthy\s+)?(?:adults?|participants?)'
        ]
        
        for pattern in participant_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                data["study_participants"].append({
                    "count": int(match.group(1)),
                    "context": match.group(0)
                })
        
        # Биодоступность
        bioavail_patterns = [
            r'bioavailability[^\d]*(\d+(?:\.\d+)?)%',
            r'(\d+(?:\.\d+)?)%\s+bioavailable'
        ]
        
        for pattern in bioavail_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                data["bioavailability"].append({
                    "value": float(match.group(1)),
                    "context": match.group(0)
                })
        
        # Противопоказания
        contraind_patterns = [
            r'contraindicated?\s+in\s+([^.]+)',
            r'avoid\s+in\s+([^.]+)',
            r'not\s+recommended\s+(?:for|in)\s+([^.]+)'
        ]
        
        for pattern in contraind_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                data["contraindications"].append({
                    "condition": match.group(1).strip(),
                    "context": match.group(0)
                })
        
        return data
    
    def compare_model_performance(self):
        """Сравнивает производительность разных моделей"""
        
        test_sentences = [
            "Curcumin inhibits CYP3A4 with IC50 of 8.2 μM",
            "Patients received magnesium 400 mg twice daily",
            "Nausea occurred in 23% of subjects taking high doses",
            "Contraindicated in severe renal impairment",
            "Bioavailability was 45% for oral administration"
        ]
        
        print("\n" + "="*80)
        print("⚖️  СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ МОДЕЛЕЙ")
        print("="*80)
        
        for sentence in test_sentences:
            print(f"\n📝 ТЕСТОВОЕ ПРЕДЛОЖЕНИЕ:")
            print(f"   {sentence}")
            print("-" * 60)
            
            for model_name in self.models.keys():
                entities = self.extract_entities(sentence, model_name)
                print(f"🤖 {model_name}: {len(entities)} сущностей")
                
                for entity in entities:
                    print(f"   • {entity.get('word', 'N/A')} -> {entity.get('entity_group', 'N/A')}")
    
    def test_edge_cases(self):
        """Тестирует сложные случаи"""
        
        edge_cases = {
            "complex_dosing": "Curcumin 500 mg twice daily with food, increased to 1000 mg if well tolerated",
            "multiple_cyp": "The compound inhibits CYP3A4, CYP2D6, and CYP2C9 with different potencies", 
            "conditional_effects": "Side effects were dose-dependent: 10% at 200 mg, 25% at 400 mg, 45% at 800 mg",
            "no_clear_data": "Drug interactions have not been studied in this population",
            "conflicting_data": "One study reported 30% bioavailability while another found 55%"
        }
        
        print("\n" + "="*80)
        print("🎭 ТЕСТИРОВАНИЕ СЛОЖНЫХ СЛУЧАЕВ")
        print("="*80)
        
        for case_name, case_text in edge_cases.items():
            print(f"\n🔍 СЛУЧАЙ: {case_name}")
            print(f"📝 Текст: {case_text}")
            print("-" * 60)
            
            # Извлекаем данные
            extracted = self.extract_specific_medical_data(case_text)
            
            print("📊 ИЗВЛЕЧЕНО:")
            for data_type, items in extracted.items():
                if items:
                    print(f"   {data_type}: {len(items)} элементов")
                    for item in items[:2]:  # Показываем первые 2
                        print(f"      • {item}")

def main():
    """Основная функция тестирования"""
    
    print("🧪 ТЕСТИРОВАНИЕ БИОМЕДИЦИНСКИХ МОДЕЛЕЙ")
    print("="*80)
    print("Проверяем что BioBERT, PubMedBERT и BlueBERT реально извлекают")
    print("из медицинских текстов перед интеграцией в MCP сервер")
    print("="*80)
    
    # Путь к файлу с данными авокадо
    supplement_data_path = "/Users/yurygagarin/Code/vitaplus-supplement-analyzer/supplement_data_avocado.json"
    
    tester = BiomedicalExtractorTester()
    
    try:
        # 1. Загружаем модели
        tester.load_models()
        
        # 2. Тестируем на реальных данных авокадо
        print(f"\n🥑 Будем анализировать реальные данные авокадо из PubMed")
        print(f"📂 Файл: {supplement_data_path}")
        tester.test_real_pubmed_abstracts(supplement_data_path)
        
        # 3. Сравниваем производительность на тестовых предложениях
        tester.compare_model_performance()
        
        # 4. Тестируем сложные случаи
        tester.test_edge_cases()
        
        print("\n" + "="*80)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("="*80)
        print("Результаты покажут:")
        print("• Какие модели лучше для медицинских данных авокадо")
        print("• Что они извлекают из реальных исследований")
        print("• Стоит ли интегрировать в MCP сервер")
        print("• Подробные результаты сохранены в avocado_analysis_results.json")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()