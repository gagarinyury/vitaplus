#!/usr/bin/env python3
"""
Тестирование PubMedBERT для медицинского анализа
"""

import torch
from transformers import AutoTokenizer, AutoModel, pipeline
import numpy as np

class PubMedBERTAnalyzer:
    def __init__(self):
        self.model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
        self.tokenizer = None
        self.model = None
        self.classifier = None
        
    def load_model(self):
        """Загружает PubMedBERT"""
        print("🚀 Загружаем PubMedBERT...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            print("✅ PubMedBERT загружен!")
            
            # Создаем классификатор для анализа настроений/безопасности
            self.classifier = pipeline(
                "text-classification",
                model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract",
                tokenizer="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
            )
            print("✅ Классификатор готов!")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False
        
        return True
    
    def get_embeddings(self, text):
        """Получает эмбеддинги для текста"""
        if not self.model:
            return None
            
        inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Берем [CLS] токен как представление всего текста
            embeddings = outputs.last_hidden_state[:, 0, :].numpy()
            
        return embeddings[0]
    
    def analyze_safety(self, supplement_text):
        """Анализирует безопасность добавки"""
        print(f"🔍 Анализируем: {supplement_text}")
        
        # Создаем контексты для анализа
        safety_contexts = [
            f"Safety and side effects of {supplement_text}",
            f"Adverse reactions and contraindications of {supplement_text}",
            f"Drug interactions with {supplement_text}",
            f"Dosage and toxicity of {supplement_text}",
            f"Clinical studies on {supplement_text} safety"
        ]
        
        results = []
        
        for context in safety_contexts:
            try:
                # Получаем эмбеддинги
                embeddings = self.get_embeddings(context)
                
                if embeddings is not None:
                    # Простой анализ на основе эмбеддингов
                    safety_score = float(np.mean(embeddings))
                    
                    results.append({
                        "context": context,
                        "safety_score": safety_score,
                        "embeddings_shape": embeddings.shape
                    })
                    
            except Exception as e:
                print(f"⚠️ Ошибка анализа контекста '{context}': {e}")
        
        return results
    
    def compare_supplements(self, supplement1, supplement2):
        """Сравнивает два препарата"""
        print(f"⚖️ Сравниваем: {supplement1} vs {supplement2}")
        
        emb1 = self.get_embeddings(f"Medical properties and effects of {supplement1}")
        emb2 = self.get_embeddings(f"Medical properties and effects of {supplement2}")
        
        if emb1 is not None and emb2 is not None:
            # Косинусное сходство
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            return {
                "supplement1": supplement1,
                "supplement2": supplement2,
                "similarity": float(similarity),
                "interpretation": "Высокое сходство" if similarity > 0.8 else "Среднее сходство" if similarity > 0.6 else "Низкое сходство"
            }
        
        return None

def test_pubmedbert():
    """Тестирует PubMedBERT"""
    
    analyzer = PubMedBERTAnalyzer()
    
    # Загружаем модель
    if not analyzer.load_model():
        return
    
    print("\n" + "="*60)
    print("🧪 ТЕСТИРОВАНИЕ PubMedBERT")
    print("="*60)
    
    # Тест 1: Анализ безопасности магния
    print("\n1️⃣ Анализ безопасности магния:")
    magnesium_results = analyzer.analyze_safety("magnesium supplement")
    
    for result in magnesium_results[:3]:  # Показываем первые 3
        print(f"   📊 {result['context']}")
        print(f"   🔢 Оценка: {result['safety_score']:.4f}")
        print()
    
    # Тест 2: Сравнение добавок
    print("\n2️⃣ Сравнение добавок:")
    comparison = analyzer.compare_supplements("magnesium", "calcium")
    if comparison:
        print(f"   ⚖️ {comparison['supplement1']} vs {comparison['supplement2']}")
        print(f"   📈 Сходство: {comparison['similarity']:.4f}")
        print(f"   💭 {comparison['interpretation']}")
    
    # Тест 3: Анализ различных добавок
    print("\n3️⃣ Анализ различных добавок:")
    supplements = ["vitamin D", "omega-3", "turmeric", "green tea extract"]
    
    for supplement in supplements:
        print(f"\n   🔍 {supplement.title()}:")
        results = analyzer.analyze_safety(supplement)
        if results:
            avg_score = np.mean([r['safety_score'] for r in results])
            print(f"   📊 Средняя оценка: {avg_score:.4f}")

if __name__ == "__main__":
    test_pubmedbert()