#!/bin/bash
# Простой скрипт для скачивания факт-листов ODS
# Использование: ./download_ods_simple.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Базовые настройки
BASE_URL="https://ods.od.nih.gov/api/"
OUTPUT_DIR="ods_fact_sheets"
DELAY=1  # Секунды между запросами

# Список ресурсов для скачивания
RESOURCES=(
    # Основные витамины
    "VitaminA" "VitaminC" "VitaminD" "VitaminE" "VitaminK"
    "VitaminB6" "VitaminB12" "Folate" "Niacin" "Riboflavin" 
    "Thiamin" "Biotin" "PantothenicAcid"
    
    # Минералы
    "Calcium" "Iron" "Magnesium" "Zinc" "Selenium" 
    "Chromium" "Copper" "Iodine" "Manganese" "Molybdenum"
    "Phosphorus" "Potassium" "Sodium"
    
    # Специальные добавки
    "Omega3FattyAcids" "Probiotics" "Ashwagandha" "Multivitamin"
    "CoQ10" "Glucosamine" "Chondroitin" "Ginkgo" "Ginseng"
    "Echinacea" "GarlicSupplements" "Turmeric" "Melatonin"
    
    # Аминокислоты
    "Creatine" "BetaAlanine" "BCAA" "Carnitine" "Taurine"
    
    # Специальные темы
    "DietarySupplementsExercise" "DietarySupplementsOlderAdults"
    "DietarySupplementsPregnancy" "DietarySupplementsCOVID19"
    "WeightLossSupplements" "EnergyDrinks"
)

# Уровни чтения и форматы
READING_LEVELS=("Consumer" "HealthProfessional")
OUTPUT_FORMATS=("XML" "HTML")

# Счетчики
TOTAL_ATTEMPTED=0
SUCCESSFUL_DOWNLOADS=0
FAILED_DOWNLOADS=0
EXISTING_FILES=0

# Функция для создания структуры папок
setup_directories() {
    echo -e "${BLUE}📁 Создание структуры папок...${NC}"
    
    for format in "xml" "html" "json"; do
        for level in "consumer" "health_professional" "spanish"; do
            mkdir -p "${OUTPUT_DIR}/${format}/${level}"
        done
    done
    
    mkdir -p "${OUTPUT_DIR}/logs"
    echo -e "${GREEN}✅ Структура папок создана в: ${OUTPUT_DIR}${NC}"
}

# Функция для проверки доступности ресурса
test_resource() {
    local resource=$1
    local level=$2
    local format=$3
    
    local url="${BASE_URL}?resourcename=${resource}&readinglevel=${level}&outputformat=${format}"
    
    # Проверяем доступность
    local response_size=$(curl -s -o /dev/null -w "%{size_download}" "$url" 2>/dev/null || echo "0")
    
    if [ "$response_size" -gt 1000 ]; then
        return 0  # Доступен
    else
        return 1  # Недоступен
    fi
}

# Функция для скачивания факт-листа
download_fact_sheet() {
    local resource=$1
    local level=$2
    local format=$3
    
    # Определяем путь для сохранения
    local level_dir=$(echo "$level" | tr '[:upper:]' '[:lower:]' | sed 's/health/health_/')
    local file_extension=$(echo "$format" | tr '[:upper:]' '[:lower:]')
    local filename="${resource}_${level}_${format}.${file_extension}"
    local filepath="${OUTPUT_DIR}/${file_extension}/${level_dir}/${filename}"
    
    # Проверяем, существует ли файл
    if [ -f "$filepath" ]; then
        echo -e "${YELLOW}⏭️  Уже существует: ${filename}${NC}"
        ((EXISTING_FILES++))
        return 0
    fi
    
    local url="${BASE_URL}?resourcename=${resource}&readinglevel=${level}&outputformat=${format}"
    
    echo -e "${BLUE}📥 Скачивание: ${resource} (${level}, ${format})${NC}"
    
    # Скачиваем файл
    if curl -s -f -o "$filepath" "$url"; then
        local file_size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo "0")
        
        if [ "$file_size" -gt 1000 ]; then
            echo -e "${GREEN}✅ Сохранен: ${filename} ($(echo "scale=1; $file_size/1024" | bc -l)KB)${NC}"
            ((SUCCESSFUL_DOWNLOADS++))
            return 0
        else
            echo -e "${RED}❌ Файл слишком мал: ${filename}${NC}"
            rm -f "$filepath"
            ((FAILED_DOWNLOADS++))
            return 1
        fi
    else
        echo -e "${RED}❌ Ошибка скачивания: ${filename}${NC}"
        ((FAILED_DOWNLOADS++))
        return 1
    fi
}

# Функция для создания отчета
create_report() {
    local report_file="${OUTPUT_DIR}/download_report.txt"
    
    echo "📋 Создание отчета..."
    
    cat > "$report_file" << EOF
ODS Fact Sheets Download Report
===============================
Дата скачивания: $(date)

СТАТИСТИКА:
- Всего попыток: $TOTAL_ATTEMPTED
- Успешно скачано: $SUCCESSFUL_DOWNLOADS  
- Уже существовало: $EXISTING_FILES
- Не удалось скачать: $FAILED_DOWNLOADS

НАЙДЕННЫЕ РЕСУРСЫ:
EOF
    
    # Добавляем список найденных файлов
    find "$OUTPUT_DIR" -name "*.xml" -o -name "*.html" | sort >> "$report_file"
    
    echo -e "${GREEN}📊 Отчет сохранен: ${report_file}${NC}"
}

# Основная функция
main() {
    echo -e "${BLUE}🚀 Начинаем скачивание факт-листов ODS...${NC}"
    echo -e "${BLUE}📝 Будем проверять ${#RESOURCES[@]} ресурсов${NC}"
    
    setup_directories
    
    local resource_count=1
    local total_resources=${#RESOURCES[@]}
    
    for resource in "${RESOURCES[@]}"; do
        echo -e "\n${BLUE}📦 [$resource_count/$total_resources] Обрабатываем: ${resource}${NC}"
        
        local found_any=false
        
        for level in "${READING_LEVELS[@]}"; do
            for format in "${OUTPUT_FORMATS[@]}"; do
                ((TOTAL_ATTEMPTED++))
                
                if test_resource "$resource" "$level" "$format"; then
                    found_any=true
                    download_fact_sheet "$resource" "$level" "$format"
                    sleep $DELAY
                fi
            done
        done
        
        if [ "$found_any" = false ]; then
            echo -e "${RED}❌ ${resource}: Не найден${NC}"
        fi
        
        ((resource_count++))
    done
    
    # Создаем отчет
    create_report
    
    # Финальная статистика
    echo -e "\n${GREEN}🎉 Скачивание завершено!${NC}"
    echo -e "${GREEN}📊 Статистика:${NC}"
    echo -e "${GREEN}   • Скачано файлов: ${SUCCESSFUL_DOWNLOADS}${NC}"
    echo -e "${GREEN}   • Уже существовало: ${EXISTING_FILES}${NC}"
    echo -e "${GREEN}   • Не удалось скачать: ${FAILED_DOWNLOADS}${NC}"
    
    # Показываем размер папки
    local total_size=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1 || echo "N/A")
    echo -e "${GREEN}   • Общий размер: ${total_size}${NC}"
    
    echo -e "\n${BLUE}✅ Все файлы сохранены в папке: ${OUTPUT_DIR}${NC}"
    echo -e "${BLUE}📋 Отчет о скачивании: ${OUTPUT_DIR}/download_report.txt${NC}"
}

# Проверяем зависимости
check_dependencies() {
    for cmd in curl bc; do
        if ! command -v "$cmd" &> /dev/null; then
            echo -e "${RED}❌ Требуется установить: $cmd${NC}"
            exit 1
        fi
    done
}

# Обработка аргументов командной строки
while [[ $# -gt 0 ]]; do
    case $1 in
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --delay)
            DELAY="$2"
            shift 2
            ;;
        --help)
            echo "Использование: $0 [--output-dir DIR] [--delay SECONDS]"
            echo "  --output-dir DIR     Папка для сохранения (по умолчанию: ods_fact_sheets)"
            echo "  --delay SECONDS      Задержка между запросами (по умолчанию: 1)"
            echo "  --help               Показать эту справку"
            exit 0
            ;;
        *)
            echo "Неизвестный параметр: $1"
            echo "Используйте --help для справки"
            exit 1
            ;;
    esac
done

# Запускаем скрипт
check_dependencies
main