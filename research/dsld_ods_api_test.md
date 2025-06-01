# Тестирование DSLD и ODS API - Результаты

## ODS API (Office of Dietary Supplements) - ✅ РАБОТАЕТ

### 📊 Статус: Полностью функционален
- **Base URL**: `https://ods.od.nih.gov/api/`
- **Формат**: XML и HTML
- **Авторизация**: Не требуется
- **Ограничения**: Один факт-лист за запрос

### 🔧 Структура запроса:
```
https://ods.od.nih.gov/api/?resourcename=[НАЗВАНИЕ]&readinglevel=[УРОВЕНЬ]&outputformat=[ФОРМАТ]
```

### 📋 Параметры:
- **resourcename**: Calcium, VitaminD, Iron, Magnesium, VitaminC, и др.
- **readinglevel**: Consumer, HealthProfessional, Spanish
- **outputformat**: XML, HTML

### 🧪 Протестированные запросы:

#### 1. Кальций (XML)
```bash
curl "https://ods.od.nih.gov/api/?resourcename=Calcium&readinglevel=Consumer&outputformat=XML"
```

**Результат:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<Factsheet xmlns="http://tempuri.org/factsheet.xsd">
  <FSID>63</FSID>
  <LanguageCode>en</LanguageCode>
  <Reviewed>2023-09-14</Reviewed>
  <URL>https://ods.od.nih.gov:443/factsheets/Calcium-Consumer/</URL>
  <Title>Calcium</Title>
  <Content>
    &lt;h2&gt;What is calcium and what does it do?&lt;/h2&gt;
    &lt;p&gt;Calcium is a mineral your body needs to build and maintain strong bones...&lt;/p&gt;
    &lt;p&gt;Vitamin D helps your body absorb calcium.&lt;/p&gt;
  </Content>
</Factsheet>
```

#### 2. Витамин D (XML, для профессионалов)
```bash
curl "https://ods.od.nih.gov/api/?resourcename=VitaminD&readinglevel=HealthProfessional&outputformat=XML"
```

**Ключевые данные:**
- FSID: 45
- Последнее обновление: 2024-07-26
- Подробная информация о биохимии витамина D
- Таблицы концентраций 25(OH)D

#### 3. Железо (HTML)
```bash
curl "https://ods.od.nih.gov/api/?resourcename=Iron&readinglevel=Consumer&outputformat=HTML"
```

**Возвращает:** Полная HTML-страница с оглавлением и структурированным контентом

### 💾 Доступные данные из ODS API:

#### Структурированная информация о каждом веществе:
1. **Базовая информация**:
   - Что это и как работает
   - Рекомендуемые дозировки по возрастам
   - Источники в продуктах питания

2. **Медицинская информация**:
   - Дефицит и симптомы
   - Взаимодействия с лекарствами
   - Побочные эффекты от передозировки

3. **Научные данные**:
   - Исследования эффективности
   - Биодоступность
   - Метаболизм в организме

#### Выявленные взаимодействия из контента:
- **Кальций + Витамин D**: "Vitamin D helps your body absorb calcium"
- **Железо + Витамин C**: Упоминания об усилении абсорбции
- **Кальций + Железо**: Потенциальное снижение абсорбции железа

### 📈 Доступные ресурсы (примеры):
- Calcium
- VitaminD  
- Iron
- VitaminC
- Magnesium
- Zinc
- VitaminB12
- Folate
- Omega3FattyAcids
- Probiotics

---

## DSLD API (Dietary Supplement Label Database) - ❌ ОГРАНИЧЕННЫЙ ДОСТУП

### 📊 Статус: API существует, но заблокирован для прямого доступа
- **Base URL**: `https://dsldapi.od.nih.gov/`
- **Альтернативный URL**: `https://api.ods.od.nih.gov/dsld/v8/`
- **Проблема**: Возвращает HTML-документацию вместо JSON/XML данных

### 🚫 Выявленные проблемы:

1. **Cloudflare защита**: Блокирует автоматические запросы
2. **Требует браузера**: API работает только через веб-интерфейс
3. **Отсутствие публичных endpoints**: Нет прямого REST API доступа

### 📋 Документированные возможности DSLD:

#### Endpoints (недоступны для прямого тестирования):
1. `/search-filter` - Поиск БАДов с фильтрами
2. `/v9/ingredient-groups` - Группы ингредиентов  
3. `/v9/browse-brands` - Поиск брендов
4. `/v9/label/{id}` - Данные о конкретном продукте

#### Потенциальные данные:
```json
{
  "id": 25,
  "fullName": "Vitamins For The Hair",
  "brandName": "Nature's Bounty",
  "upcSku": "0 74312 02100 8",
  "targetGroups": ["Vegetarian", "Adult (18 - 50 Years)"],
  "physicalState": {
    "langualCode": "E0155", 
    "langualCodeDescription": "Tablet or Pill"
  },
  "servingsPerContainer": null
}
```

### 🔍 Альтернативные подходы к DSLD:
1. **Web scraping**: Парсинг веб-интерфейса DSLD
2. **Bulk download**: Запрос полной базы данных у NIH
3. **Коммерческие партнеры**: Использование сторонних поставщиков данных

---

## 📊 Сравнение API для нашего проекта

| Критерий | ODS API | DSLD API |
|----------|---------|----------|
| **Доступность** | ✅ Полная | ❌ Ограничена |
| **Авторизация** | ✅ Не нужна | ❓ Неизвестно |
| **Формат данных** | ✅ XML/HTML | ❓ JSON (недоступен) |
| **Составы БАДов** | ❌ Нет | ✅ Полные данные |
| **Взаимодействия** | ✅ Частично | ❓ Неизвестно |
| **Дозировки** | ✅ Подробно | ✅ На этикетках |
| **Брэнды продуктов** | ❌ Нет | ✅ 178,000+ |

## 🎯 Рекомендации для проекта

### Краткосрочная стратегия (1-3 месяца):
1. **Использовать ODS API** как основной источник научной информации
2. **Создать базу взаимодействий** на основе ODS fact sheets
3. **Парсить ключевые данные** из XML-ответов ODS API

### Среднесрочная стратегия (3-6 месяцев):
1. **Исследовать возможности доступа к DSLD**:
   - Связаться с NIH для получения API ключа
   - Рассмотреть bulk download опции
   - Изучить коммерческие альтернативы

2. **Комбинировать источники**:
   - ODS API для научной информации
   - Веб-скрапинг DSLD для составов продуктов
   - PubMed API для исследований взаимодействий

### Долгосрочная стратегия (6+ месяцев):
1. **Создать собственную базу данных** объединяющую:
   - Научные данные из ODS
   - Составы продуктов из DSLD (через скрапинг)
   - Взаимодействия из PubMed
   - Пользовательские отчеты

## 🔧 Практическая реализация

### Для ODS API:
```javascript
// Пример получения данных о кальции
const getSupplementInfo = async (name, level = 'Consumer') => {
  const url = `https://ods.od.nih.gov/api/?resourcename=${name}&readinglevel=${level}&outputformat=XML`;
  const response = await fetch(url);
  const xmlText = await response.text();
  // Парсинг XML и извлечение структурированных данных
  return parseSupplementData(xmlText);
};
```

### Для извлечения взаимодействий:
```javascript
// Поиск упоминаний взаимодействий в тексте
const extractInteractions = (content) => {
  const patterns = [
    /vitamin [A-Z] helps.*absorb/gi,
    /enhances.*absorption/gi,
    /reduces.*absorption/gi,
    /interferes with/gi
  ];
  // Логика извлечения взаимодействий
};
```

## ✅ Выводы

1. **ODS API полностью функционален** и предоставляет качественную научную информацию
2. **DSLD API технически существует**, но требует специального доступа
3. **Комбинированный подход** ODS + PubMed + веб-скрапинг DSLD оптимален для MVP
4. **80+ факт-листов ODS** содержат достаточно данных для создания базовой системы проверки взаимодействий