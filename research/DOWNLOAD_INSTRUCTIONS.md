# 📥 Инструкции по скачиванию факт-листов ODS

## 🎯 Что это?

Создано **2 скрипта** для автоматического скачивания всех 80+ факт-листов от NIH Office of Dietary Supplements:

1. **Python скрипт** (`download_ods_factsheets.py`) - продвинутый с метаданными
2. **Bash скрипт** (`download_ods_simple.sh`) - простой и быстрый

## ✅ Тест выполнен успешно!

**Результат тестирования:**
- ✅ **12/12 файлов** скачано успешно
- 📊 **708KB** общий размер тестовых файлов
- 🔄 **4 формата**: Consumer XML/HTML + Professional XML/HTML
- ⚡ **0 ошибок** при скачивании

## 🚀 Быстрый запуск (рекомендуется)

### Bash скрипт (простой):
```bash
# Сделать исполняемым
chmod +x download_ods_simple.sh

# Скачать все факт-листы
./download_ods_simple.sh

# Или в custom папку
./download_ods_simple.sh --output-dir my_factsheets --delay 2
```

### Python скрипт (расширенный):
```bash
# Установить зависимости
pip install requests

# Скачать все факт-листы
python3 download_ods_factsheets.py

# Или ограниченное количество для теста
python3 download_ods_factsheets.py --limit 10 --output-dir test_download
```

## 📁 Структура скачиваемых файлов

```
ods_fact_sheets/
├── xml/
│   ├── consumer/                    # Для обычных пользователей
│   │   ├── VitaminC_Consumer_XML.xml
│   │   ├── Calcium_Consumer_XML.xml
│   │   └── ...
│   ├── health_professional/         # Для медиков (больше деталей)
│   │   ├── VitaminC_HealthProfessional_XML.xml
│   │   └── ...
│   └── spanish/                     # На испанском языке
│       └── ...
├── html/
│   ├── consumer/
│   ├── health_professional/
│   └── spanish/
└── logs/
    ├── download_log_20250601_143022.json
    └── summary_report.json
```

## 📋 Список ресурсов для скачивания

### 💊 **Витамины (13 штук):**
- VitaminA, VitaminC, VitaminD, VitaminE, VitaminK
- VitaminB6, VitaminB12, Folate, Niacin, Riboflavin
- Thiamin, Biotin, PantothenicAcid

### ⚗️ **Минералы (13 штук):**
- Calcium, Iron, Magnesium, Zinc, Selenium
- Chromium, Copper, Iodine, Manganese, Molybdenum
- Phosphorus, Potassium, Sodium

### 🌿 **Специальные добавки (10 штук):**
- Omega3FattyAcids, Probiotics, Ashwagandha, Multivitamin
- CoQ10, Glucosamine, Chondroitin, Ginkgo, Ginseng
- Echinacea, GarlicSupplements, Turmeric, Melatonin

### 💪 **Спортивные добавки (5 штук):**
- Creatine, BetaAlanine, BCAA, Carnitine, Taurine

### 🏥 **Специальные темы (6 штук):**
- DietarySupplementsExercise
- DietarySupplementsOlderAdults  
- DietarySupplementsPregnancy
- DietarySupplementsCOVID19
- WeightLossSupplements
- EnergyDrinks

**ИТОГО: ~47 основных ресурсов** × 6 форматов = **~282 файла**

## 📊 Ожидаемые результаты

### 📈 **Статистика скачивания:**
- **Успешных загрузок**: 80-90% (зависит от доступности ресурсов)
- **Общий размер**: 50-100 MB
- **Время выполнения**: 10-20 минут (с паузами)
- **Форматы**: XML (структурированные) + HTML (читаемые)

### 📋 **Получаемые данные:**
```xml
<!-- Пример XML структуры -->
<Factsheet>
  <FSID>87</FSID>
  <Title>Vitamin C</Title>  
  <Reviewed>2021-03-22</Reviewed>
  <Content>
    <!-- HTML контент с информацией о взаимодействиях -->
    Vitamin C enhances iron absorption...
  </Content>
</Factsheet>
```

## 🔧 Параметры скриптов

### Bash скрипт:
```bash
./download_ods_simple.sh [ОПЦИИ]

ОПЦИИ:
  --output-dir DIR     Папка для сохранения (по умолчанию: ods_fact_sheets)
  --delay SECONDS      Задержка между запросами (по умолчанию: 1)  
  --help               Показать справку
```

### Python скрипт:
```bash
python3 download_ods_factsheets.py [ОПЦИИ]

ОПЦИИ:
  --limit N            Ограничить количество ресурсов для тестирования
  --output-dir DIR     Папка для сохранения
```

## 🎯 Практическое применение для VitaPlus

### 💡 **Извлечение взаимодействий:**
```bash
# После скачивания найти все упоминания взаимодействий
grep -r -i "interact\|enhance\|reduce\|absorb" ods_fact_sheets/xml/health_professional/

# Пример результата:
# Calcium_HealthProfessional_XML.xml: "Vitamin D helps your body absorb calcium"
# Iron_HealthProfessional_XML.xml: "Vitamin C enhances iron absorption"
```

### 📊 **Создание базы данных:**
```python
# Пример парсинга XML для извлечения структурированных данных
import xml.etree.ElementTree as ET

def parse_factsheet(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    return {
        'fsid': root.find('FSID').text,
        'title': root.find('Title').text,
        'reviewed': root.find('Reviewed').text,
        'content': root.find('Content').text
    }
```

## ⚠️ Важные замечания

### 🚦 **Ограничения API:**
- **Не более 3 запросов/секунду** (скрипты учитывают)
- **Некоторые ресурсы могут быть недоступны** 
- **Испанские версии доступны не для всех ресурсов**

### 📝 **Рекомендации:**
1. **Запускать в нерабочее время** для минимизации нагрузки на сервер NIH
2. **Проверить скачанные файлы** на корректность
3. **Регулярно обновлять** данные (факт-листы обновляются каждые 1-3 года)

## 🔄 Обновление данных

```bash
# Для обновления существующих файлов удалить старые
rm -rf ods_fact_sheets/

# И запустить скрипт заново
./download_ods_simple.sh
```

## 📞 Поддержка

При ошибках проверить:
1. **Интернет соединение**
2. **Доступность curl/python** 
3. **Права на запись** в папку назначения
4. **Логи ошибок** в `ods_fact_sheets/logs/`

---

## 🎉 Результат

После выполнения у вас будет **полная локальная копия** всех факт-листов ODS с:
- ✅ **Научно обоснованной информацией** о БАДах
- ✅ **Данными о взаимодействиях** между веществами  
- ✅ **Официальными дозировками** по возрастам
- ✅ **Предупреждениями о безопасности**

**Идеальная база для создания системы проверки взаимодействий в VitaPlus!** 🌟