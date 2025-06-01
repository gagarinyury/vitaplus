#!/bin/bash
# Тестовый скрипт для скачивания нескольких факт-листов

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="https://ods.od.nih.gov/api/"
OUTPUT_DIR="test_ods"

# Тестовые ресурсы
TEST_RESOURCES=("VitaminC" "Calcium" "Iron")
READING_LEVELS=("Consumer" "HealthProfessional")  
OUTPUT_FORMATS=("XML" "HTML")

SUCCESSFUL=0
FAILED=0

echo -e "${BLUE}🧪 Тестирование скачивания факт-листов ODS...${NC}"

# Создаем структуру папок
mkdir -p "${OUTPUT_DIR}"/{xml,html}/{consumer,health_professional}

for resource in "${TEST_RESOURCES[@]}"; do
    echo -e "\n${BLUE}📦 Тестируем: ${resource}${NC}"
    
    for level in "${READING_LEVELS[@]}"; do
        for format in "${OUTPUT_FORMATS[@]}"; do
            level_dir=$(echo "$level" | tr '[:upper:]' '[:lower:]' | sed 's/health/health_/')
            file_extension=$(echo "$format" | tr '[:upper:]' '[:lower:]')
            filename="${resource}_${level}_${format}.${file_extension}"
            filepath="${OUTPUT_DIR}/${file_extension}/${level_dir}/${filename}"
            
            url="${BASE_URL}?resourcename=${resource}&readinglevel=${level}&outputformat=${format}"
            
            echo -e "${YELLOW}📥 ${resource} (${level}, ${format})${NC}"
            
            if curl -s -f -o "$filepath" "$url"; then
                file_size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo "0")
                
                if [ "$file_size" -gt 1000 ]; then
                    size_kb=$(echo "scale=1; $file_size/1024" | bc -l 2>/dev/null || echo "$(($file_size/1024))")
                    echo -e "${GREEN}✅ Сохранен: ${filename} (${size_kb}KB)${NC}"
                    ((SUCCESSFUL++))
                else
                    echo -e "❌ Файл слишком мал: ${filename}"
                    rm -f "$filepath"
                    ((FAILED++))
                fi
            else
                echo -e "❌ Ошибка скачивания: ${filename}"
                ((FAILED++))
            fi
            
            sleep 0.5
        done
    done
done

echo -e "\n${GREEN}🎉 Тестирование завершено!${NC}"
echo -e "${GREEN}✅ Успешно: ${SUCCESSFUL}${NC}"
echo -e "❌ Неудачно: ${FAILED}"

# Показываем что скачалось
echo -e "\n${BLUE}📁 Скачанные файлы:${NC}"
find "$OUTPUT_DIR" -type f | sort

total_size=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1 || echo "N/A")
echo -e "\n${BLUE}📊 Общий размер: ${total_size}${NC}"