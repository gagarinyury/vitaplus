# Расширение MCP сервера для множественных взаимодействий

## 1. Множественные взаимодействия (3+ веществ)

### Текущая реализация
```typescript
search_interactions(substance1: string, substance2: string)
```

### Предлагаемое расширение
```typescript
search_multiple_interactions(substances: string[], options?: {
  checkAllPairs?: boolean;
  checkCombinations?: boolean;
  maxSubstances?: number;
})
```

### Как это будет работать:

#### Вариант A: Парные взаимодействия
```javascript
// Пример: ["Vitamin D", "Calcium", "Magnesium"]
// Проверяет все пары:
// 1. Vitamin D ↔ Calcium
// 2. Vitamin D ↔ Magnesium  
// 3. Calcium ↔ Magnesium
```

#### Вариант B: Комбинированный поиск
```javascript
// Ищет статьи где упоминаются ВСЕ вещества одновременно
// PubMed запрос: (vitamin D[mesh]) AND (calcium[mesh]) AND (magnesium[mesh]) AND interaction
```

#### Вариант C: Умный анализ
```javascript
// 1. Сначала парные взаимодействия
// 2. Потом поиск статей про конкретную комбинацию
// 3. Анализ совокупного риска
```

### Пример результата:
```json
{
  "substances": ["Vitamin D", "Calcium", "Magnesium"],
  "pairwiseInteractions": [
    {
      "pair": ["Vitamin D", "Calcium"],
      "interaction": "synergistic",
      "severity": "mild"
    },
    {
      "pair": ["Calcium", "Magnesium"], 
      "interaction": "competitive_absorption",
      "severity": "moderate"
    }
  ],
  "overallAssessment": {
    "combinationSafety": "caution",
    "recommendations": [
      "Take calcium and magnesium at different times",
      "Vitamin D enhances calcium absorption"
    ]
  }
}
```

## 2. Время приема и расписание

### Что можем найти в PubMed:

#### A. Время приема относительно еды
```javascript
// Поисковые запросы:
"vitamin D[mesh] AND (fasting OR 'with food' OR 'empty stomach')"
"iron[mesh] AND (meal OR food OR fasting) AND absorption"
```

#### B. Время суток
```javascript
"melatonin[mesh] AND (evening OR night OR bedtime)"
"vitamin B12[mesh] AND (morning OR timing)"
```

#### C. Интервалы между приемами
```javascript
"calcium[mesh] AND iron[mesh] AND (timing OR interval OR separation)"
"thyroid hormone[mesh] AND (coffee OR interval) AND absorption"
```

### Новый инструмент: search_timing
```typescript
interface TimingResult {
  substance: string;
  optimalTiming: {
    timeOfDay?: "morning" | "evening" | "anytime";
    withFood?: "with_food" | "empty_stomach" | "no_preference";
    intervalFromOthers?: {
      substance: string;
      minimumInterval: string; // "2 hours", "30 minutes"
      reason: string;
    }[];
  };
  evidence: Article[];
}
```

### Пример запроса времени:
```javascript
{
  "substance": "levothyroxine",
  "checkWith": ["coffee", "calcium", "iron"],
  "result": {
    "optimalTiming": {
      "timeOfDay": "morning",
      "withFood": "empty_stomach", 
      "intervalFromOthers": [
        {
          "substance": "coffee",
          "minimumInterval": "1 hour",
          "reason": "Coffee reduces absorption by 30%"
        },
        {
          "substance": "calcium", 
          "minimumInterval": "4 hours",
          "reason": "Calcium binds to levothyroxine"
        }
      ]
    }
  }
}
```

## 3. Что можем найти в PubMed по времени:

### ✅ Хорошо документировано:
- **Лекарства с едой/натощак** - много исследований
- **Интервалы между антагонистами** (кальций-железо, кальций-цинк)
- **Время суток для гормонов** (мелатонин, кортизол)
- **Щитовидка + кофе/кальций** - хорошо изучено

### ⚠️ Ограниченно:
- **БАДы между собой** - мало конкретных исследований времени
- **Оптимальные интервалы** - часто нет точных данных
- **Индивидуальные различия** - PubMed показывает средние значения

### ❌ Сложно найти:
- **Персонализированные схемы** 
- **Комплексные расписания для 5+ веществ**

## 4. Реализация расширений

### Этап 1: Множественные взаимодействия (1-2 дня)
```typescript
// Добавить в существующие инструменты
search_interactions_batch(substances: string[])
```

### Этап 2: Анализ времени приема (2-3 дня)  
```typescript
// Новый инструмент
search_timing_recommendations(substance: string, context?: string[])
```

### Этап 3: Умное расписание (3-4 дня)
```typescript
// Комбинированный анализ
generate_dosing_schedule(substances: SubstanceWithDose[])
```

## 5. Примеры запросов которые найдем:

### Хорошие примеры из PubMed:
1. **"Take iron supplements 2 hours apart from calcium"** - много статей
2. **"Levothyroxine 30-60 minutes before breakfast"** - хорошо документировано  
3. **"Magnesium before bedtime for sleep"** - есть исследования
4. **"Vitamin D with largest meal for absorption"** - изучено
5. **"Separate zinc and copper by 2+ hours"** - документировано

### Что НЕ найдем:
1. Точные индивидуальные схемы
2. Оптимизация для конкретного человека
3. Учет личного расписания

## Заключение

**Можем реализовать:**
✅ Множественные взаимодействия (3-5 веществ)  
✅ Базовые рекомендации по времени приема
✅ Интервалы между веществами
✅ Прием с едой/натощак

**Ограничения:**
- Качество данных зависит от наличия исследований
- Больше данных по лекарствам, чем по БАДам  
- Нет персонализации под конкретного человека

**Хотите, чтобы я реализовал эти расширения?**