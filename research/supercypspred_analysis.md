# 🔬 SuperCYPsPred API - Анализ для VitaPlus

## 📋 Обзор
**SuperCYPsPred** - веб-сервер для предсказания активности цитохрома P450 (CYP) ферментов. Эти ферменты отвечают за метаболизм более 80% лекарств и БАДов.

## 🎯 Возможности для VitaPlus

### **CYP Ферменты (основные):**
- **CYP1A2** - кофеин, некоторые БАДы
- **CYP2C9** - варфарин, НПВС  
- **CYP2C19** - омепразол, антидепрессанты
- **CYP2D6** - многие антидепрессанты
- **CYP3A4** - ~50% всех лекарств

## 🔌 API Детали

### **Эндпоинты:**
1. **Отправка запроса:** 
   `http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php`
2. **Получение результатов:**
   `http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php`

### **Входные данные:**
- **Тип 1:** Название БАДа (PubChem поиск)
- **Тип 2:** SMILES строка (химическая структура)

### **Модели CYP:**
- Можно выбрать конкретные: CYP1A2, CYP2C9, CYP2C19, CYP2D6, CYP3A4
- Или все сразу: `ALL_MODELS`

## 💻 Пример использования API

### **Python код:**
```python
import requests
import time
import json

class SuperCYPsPredAPI:
    def __init__(self):
        self.enqueue_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php"
        self.retrieve_url = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php"
    
    def predict_cyp_interactions(self, compound_name):
        """Предсказание CYP взаимодействий для БАДа"""
        
        # 1. Отправка запроса
        data = {
            'input_type': 'name',
            'input': compound_name,
            'models': 'ALL_MODELS'
        }
        
        response = requests.post(self.enqueue_url, data=data)
        if response.status_code != 200:
            return None
            
        task_id = response.json().get('task_id')
        
        # 2. Ожидание результатов
        while True:
            time.sleep(10)  # Ждем 10 секунд
            
            check_data = {'task_id': task_id}
            result = requests.post(self.retrieve_url, data=check_data)
            
            if result.status_code == 200:
                return result.json()
                
        return None

# Использование
api = SuperCYPsPredAPI()
result = api.predict_cyp_interactions("Zinc")
```

### **Примеры запросов:**
```bash
# По названию БАДа
python simple_api.py -t name -m ALL_MODELS -o results.csv "Zinc"

# По SMILES структуре
python simple_api.py -t smiles -m CYP3A4 -o results.csv "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"

# Несколько БАДов
python simple_api.py aspirin,sertraline,zinc
```

## 📊 Результаты API

### **Формат вывода (CSV):**
```csv
Compound,CYP1A2,CYP2C9,CYP2C19,CYP2D6,CYP3A4,Confidence
Zinc,0.12,0.08,0.15,0.09,0.25,0.85
Calcium,0.05,0.03,0.07,0.04,0.11,0.78
```

### **Интерпретация:**
- **Значения:** 0-1 (0 = нет ингибирования, 1 = сильное ингибирование)
- **Confidence:** Уверенность модели (0-1)
- **Пороговые значения:** >0.5 = вероятное ингибирование

## 🔄 Интеграция с VitaPlus

### **1. Создание сервиса CYP проверки:**
```typescript
// services/CYPInteractionService.ts
export class CYPInteractionService {
  private apiUrl = 'your-backend-api/cyp-check';
  
  async checkCYPInteractions(supplements: string[]) {
    const results = [];
    
    for (const supplement of supplements) {
      try {
        const response = await fetch(`${this.apiUrl}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ compound: supplement })
        });
        
        const cypData = await response.json();
        results.push({
          supplement,
          cypProfile: cypData,
          riskLevel: this.calculateRisk(cypData)
        });
      } catch (error) {
        console.error(`CYP проверка для ${supplement} неудачна:`, error);
      }
    }
    
    return results;
  }
  
  private calculateRisk(cypData: any): 'low' | 'medium' | 'high' {
    const maxInhibition = Math.max(...Object.values(cypData.predictions));
    
    if (maxInhibition > 0.7) return 'high';
    if (maxInhibition > 0.4) return 'medium';
    return 'low';
  }
}
```

### **2. Компонент предупреждения CYP:**
```typescript
// components/CYPWarning.tsx
interface CYPWarningProps {
  cypResults: CYPResult[];
}

export const CYPWarning: React.FC<CYPWarningProps> = ({ cypResults }) => {
  const highRiskItems = cypResults.filter(r => r.riskLevel === 'high');
  
  if (highRiskItems.length === 0) return null;
  
  return (
    <View style={styles.warningContainer}>
      <Text style={styles.warningTitle}>⚠️ CYP Взаимодействия</Text>
      
      {highRiskItems.map((item, index) => (
        <View key={index} style={styles.warningItem}>
          <Text style={styles.supplementName}>{item.supplement}</Text>
          <Text style={styles.cypInfo}>
            Может влиять на метаболизм лекарств через CYP ферменты
          </Text>
          
          <TouchableOpacity onPress={() => showDetailedCYPInfo(item)}>
            <Text style={styles.moreInfoLink}>Подробнее →</Text>
          </TouchableOpacity>
        </View>
      ))}
    </View>
  );
};
```

## 🎯 Применение в VitaPlus

### **Сценарии использования:**

1. **Проверка при добавлении БАДа:**
   - Пользователь сканирует/добавляет новый БАД
   - Автоматическая CYP проверка
   - Предупреждение если высокий риск

2. **Анализ текущего списка:**
   - Периодическая проверка всех БАДов пользователя
   - Выявление потенциальных CYP конфликтов
   - Рекомендации по времени приема

3. **Перед приемом лекарств:**
   - Пользователь указывает принимаемые лекарства
   - Проверка CYP взаимодействий с БАДами
   - Рекомендации врача при высоком риске

## ⚡ Преимущества для VitaPlus

### **✅ Плюсы:**
- **Научная основа** - машинное обучение на реальных данных
- **Бесплатный доступ** - нет ограничений на запросы
- **Широкий охват** - 5 основных CYP ферментов
- **Простая интеграция** - REST API
- **Актуальность** - обновляемые модели

### **⚠️ Ограничения:**
- **Задержка обработки** - может занимать несколько минут
- **Только английские названия** - нужен перевод
- **Не все БАДы** - база PubChem может не содержать редкие БАДы
- **Предсказательная модель** - не 100% точность

## 📈 Рекомендации для реализации

### **Этап 1: MVP интеграция**
1. Создать backend сервис для CYP API
2. Добавить базовую CYP проверку для топ-20 БАДов
3. Простые предупреждения в UI

### **Этап 2: Расширение**
1. Кэширование результатов CYP
2. Персонализированные рекомендации
3. Интеграция с лекарственными базами

### **Этап 3: Продвинутые функции**
1. Предсказание времени приема
2. Дозозависимые предупреждения
3. Интеграция с электронными рецептами

## 🎯 Заключение

**SuperCYPsPred API** - мощный инструмент для VitaPlus! Позволяет:
- Предсказывать взаимодействия БАДов через CYP ферменты
- Предупреждать о потенциальных проблемах с лекарствами
- Повышать безопасность приема БАДов

**Готов к интеграции!** 🚀

---
**Контакты разработчиков:**
- Dr. Priyanka Banerjee: priyanka.banerjee@charite.de
- Charite University of Medicine, Berlin
- Лицензия: Creative Commons Attribution-Noncommercial