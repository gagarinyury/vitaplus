# Реальные примеры данных из PubMed API

## Пример 1: Поиск взаимодействий витамина D и кальция

### Запрос:
```
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=vitamin+D+AND+calcium+AND+interaction&retmode=json&retmax=5"
```

### Результат поиска:
```json
{
  "header": {
    "type": "esearch",
    "version": "0.3"
  },
  "esearchresult": {
    "count": "1627",
    "retmax": "5",
    "retstart": "0",
    "idlist": ["40431395", "40390107", "40362897", "40320139", "40314085"],
    "translationset": [
      {
        "from": "vitamin D",
        "to": "\"vitamin d\"[Supplementary Concept] OR \"vitamin d\"[All Fields] OR \"ergocalciferols\"[Supplementary Concept] OR \"ergocalciferols\"[All Fields] OR \"vitamin d\"[MeSH Terms] OR \"ergocalciferols\"[MeSH Terms]"
      },
      {
        "from": "calcium",
        "to": "\"calcium\"[Supplementary Concept] OR \"calcium\"[All Fields] OR \"calcium\"[MeSH Terms] OR \"calciums\"[All Fields] OR \"calcium's\"[All Fields]"
      }
    ],
    "querytranslation": "(\"vitamin d\"[Supplementary Concept] OR \"vitamin d\"[All Fields]...) AND (\"calcium\"[Supplementary Concept] OR \"calcium\"[All Fields]...) AND (\"interact\"[All Fields] OR \"interaction\"[All Fields]...)"
  }
}
```

**Ключевые находки:**
- **1,627 статей** найдено по теме взаимодействий витамина D и кальция
- API автоматически расширяет поисковые термины через MeSH
- Возвращает PMID для дальнейшего получения полных данных

### Получение полной статьи (PMID: 40431395):

```
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=40431395&retmode=xml&rettype=abstract"
```

### Извлеченные данные:
- **Название**: "The Importance of Vitamin D and Magnesium in Athletes"
- **Журнал**: Nutrients, 2025
- **Абстракт**: "Magnesium and vitamin D are closely linked—vitamin D aids magnesium absorption, while magnesium is vital for vitamin D synthesis, transport, and activation."
- **MeSH термины**: Magnesium, Vitamin D, Athletes, Dietary Supplements
- **Ключевые слова**: ATP, bone, cardiovascular, magnesium, muscle, vitamin D

## Пример 2: Поиск взаимодействий БАДов с лекарствами

### Запрос:
```
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=supplement+drug+interaction&retmode=json&retmax=3"
```

### Результат:
```json
{
  "esearchresult": {
    "count": "9690",
    "retmax": "3",
    "idlist": ["40445985", "40439969", "40438492"],
    "translationset": [
      {
        "from": "supplement",
        "to": "\"dietary supplements\"[MeSH Terms] OR (\"dietary\"[All Fields] AND \"supplements\"[All Fields]) OR \"dietary supplements\"[All Fields] OR \"supplement\"[All Fields]"
      },
      {
        "from": "drug interaction", 
        "to": "\"drug interactions\"[MeSH Terms] OR (\"drug\"[All Fields] AND \"interactions\"[All Fields]) OR \"drug interactions\"[All Fields]"
      }
    ]
  }
}
```

**Находки:**
- **9,690 статей** о взаимодействиях БАДов с лекарствами
- Автоматическое сопоставление с MeSH Terms

## Пример 3: Взаимодействия железа и витамина C

### Запрос:
```
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=iron+AND+vitamin+C+AND+absorption&retmode=json&retmax=3"
```

### Результат:
- **794 статьи** о взаимодействии железа и витамина C
- ID статей: ["40362794", "40194561", "40104105"]

### Полные данные статьи (PMID: 40362794):
- **Название**: "Impact of Side Effects on Anemia Therapy Compliance"
- **Журнал**: Nutrients, 2025
- **Ключевые находки из абстракта**:
  - "Supplements like magnesium and vitamin D3 showed positive effects in mitigating the side effects"
  - "whereas probiotics and vitamin C had mixed outcomes"
  - Исследование 382 пациентов с анемией
  - 45% сообщили о побочных эффектах

## Структура данных, которые мы можем извлечь

### 1. Метаданные статей
```xml
<PMID>40431395</PMID>
<ArticleTitle>The Importance of Vitamin D and Magnesium in Athletes</ArticleTitle>
<Journal>
  <Title>Nutrients</Title>
  <ISSN>2072-6643</ISSN>
</Journal>
<PubDate>
  <Year>2025</Year>
  <Month>May</Month>
</PubDate>
```

### 2. Абстракты с информацией о взаимодействиях
```xml
<Abstract>
  <AbstractText>
    Vitamin D aids magnesium absorption, while magnesium is vital for vitamin D synthesis, transport, and activation...
  </AbstractText>
</Abstract>
```

### 3. MeSH термины для категоризации
```xml
<MeshHeading>
  <DescriptorName UI="D008274">Magnesium</DescriptorName>
</MeshHeading>
<MeshHeading>
  <DescriptorName UI="D014807">Vitamin D</DescriptorName>
</MeshHeading>
<MeshHeading>
  <DescriptorName UI="D019587">Dietary Supplements</DescriptorName>
</MeshHeading>
```

### 4. Ключевые слова
```xml
<KeywordList>
  <Keyword>ATP</Keyword>
  <Keyword>magnesium</Keyword>
  <Keyword>muscle</Keyword>
  <Keyword>vitamin D</Keyword>
  <Keyword>absorption</Keyword>
</KeywordList>
```

## Практические выводы для нашего приложения

### 1. Выявленные взаимодействия из реальных данных:

**Положительные взаимодействия:**
- **Витамин D + Магний**: "Vitamin D aids magnesium absorption, while magnesium is vital for vitamin D synthesis"
- **Витамин C + Железо**: Усиливает абсорбцию железа (из контекста исследований анемии)

**Нейтральные/Смешанные:**
- **Пробиотики + Витамин C**: "mixed outcomes" в контексте терапии анемии

**Проблемные взаимодействия:**
- Различные побочные эффекты БАДов в зависимости от возраста и BMI

### 2. Паттерны для извлечения данных:

**Регулярные выражения для поиска взаимодействий:**
- `"vitamin [A-Z] (aids|enhances|inhibits|blocks) [a-z]+ absorption"`
- `"magnesium is vital for vitamin [A-Z] (synthesis|transport|activation)"`
- `"supplements.*showed (positive|negative) effects"`

### 3. Статистика эффективности поиска:

| Запрос | Найдено статей | Релевантность |
|--------|----------------|---------------|
| vitamin D + calcium + interaction | 1,627 | Высокая |
| supplement + drug interaction | 9,690 | Очень высокая |
| iron + vitamin C + absorption | 794 | Высокая |

### 4. Рекомендации по использованию:

1. **Начинать с широких запросов** (supplement + interaction)
2. **Использовать MeSH термины** для точности
3. **Комбинировать с временными фильтрами** для актуальности
4. **Обрабатывать абстракты с помощью NLP** для извлечения структурированных данных
5. **Создать словарь синонимов** на основе translationset из API

Эти реальные примеры показывают, что PubMed API содержит богатую базу данных для создания системы проверки взаимодействий БАДов.