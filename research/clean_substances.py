#!/usr/bin/env python3
import json
import re

with open('/Users/yurygagarin/Code/1/vitaplus/research/interactions_database.json', 'r', encoding='utf-8') as f:
    interactions = json.load(f)

# Получаем все вещества и очищаем их
real_substances = set()

for interaction in interactions:
    substance = interaction['interacts_with'].strip()
    if substance and substance != 'unknown':
        # Оставляем только короткие названия (вероятно, реальные вещества)
        if len(substance) < 50 and not substance.startswith(('Does ', 'Taking ', 'Some ', 'They ', 'The ', 'This ', 'It ')):
            # Дополнительная фильтрация
            if not any(word in substance.lower() for word in ['studies', 'research', 'evidence', 'clinical', 'trial', 'patients', 'people']):
                real_substances.add(substance)

print('🧹 ОЧИЩЕННЫЙ СПИСОК РЕАЛЬНЫХ ВЕЩЕСТВ:')
print('=' * 50)

# Категоризация
medicines = []
supplements = []
diseases = []
foods = []
other = []

for substance in sorted(real_substances):
    substance_lower = substance.lower()
    
    # Лекарства (по характерным названиям)
    if any(med in substance_lower for med in ['mevacor', 'sumycin', 'zestril', 'stalevo', 'sterapred', 'microzide', 'hydro']):
        medicines.append(substance)
    # Болезни
    elif any(disease in substance_lower for disease in ['disease', 'syndrome', 'alzheimer', 'crohn', 'wilson', 'wernicke', 'menkes']):
        diseases.append(substance)
    # Витамины/минералы/БАДы
    elif any(supp in substance_lower for supp in ['vitamin', 'copper', 'folic', 'calcium', 'iron', 'magnesium', 'zinc']):
        supplements.append(substance)
    # Продукты
    elif any(food in substance_lower for food in ['cabbage', 'mushrooms', 'sunscreens']):
        foods.append(substance)
    # Остальное
    else:
        other.append(substance)

print('💊 ЛЕКАРСТВА:')
for i, med in enumerate(medicines, 1):
    print(f'  {i:2d}. {med}')

print('\n🧬 ВИТАМИНЫ/МИНЕРАЛЫ/БАДы:')  
for i, supp in enumerate(supplements, 1):
    print(f'  {i:2d}. {supp}')

print('\n🏥 БОЛЕЗНИ/СОСТОЯНИЯ:')
for i, disease in enumerate(diseases, 1):
    print(f'  {i:2d}. {disease}')

print('\n🍎 ПРОДУКТЫ/ВЕЩЕСТВА:')
for i, food in enumerate(foods, 1):
    print(f'  {i:2d}. {food}')

print('\n❓ ПРОЧЕЕ:')
for i, item in enumerate(other, 1):
    print(f'  {i:2d}. {item}')

total_clean = len(medicines) + len(supplements) + len(diseases) + len(foods) + len(other)
print(f'\n📊 ИТОГО РЕАЛЬНЫХ ВЕЩЕСТВ: {total_clean}')
print(f'   Лекарства: {len(medicines)}')
print(f'   БАДы/витамины: {len(supplements)}')
print(f'   Болезни: {len(diseases)}')
print(f'   Продукты: {len(foods)}')
print(f'   Прочее: {len(other)}')

# Сохранить очищенный список
with open('/Users/yurygagarin/Code/1/vitaplus/research/clean_substances_list.txt', 'w', encoding='utf-8') as f:
    f.write('ОЧИЩЕННЫЙ СПИСОК РЕАЛЬНЫХ ВЕЩЕСТВ ДЛЯ ВЗАИМОДЕЙСТВИЙ\n')
    f.write('=' * 60 + '\n\n')
    
    f.write('💊 ЛЕКАРСТВА:\n')
    for i, med in enumerate(medicines, 1):
        f.write(f'  {i:2d}. {med}\n')
    
    f.write('\n🧬 ВИТАМИНЫ/МИНЕРАЛЫ/БАДы:\n')
    for i, supp in enumerate(supplements, 1):
        f.write(f'  {i:2d}. {supp}\n')
    
    f.write('\n🏥 БОЛЕЗНИ/СОСТОЯНИЯ:\n')
    for i, disease in enumerate(diseases, 1):
        f.write(f'  {i:2d}. {disease}\n')
    
    f.write('\n🍎 ПРОДУКТЫ/ВЕЩЕСТВА:\n')
    for i, food in enumerate(foods, 1):
        f.write(f'  {i:2d}. {food}\n')
    
    f.write('\n❓ ПРОЧЕЕ:\n')
    for i, item in enumerate(other, 1):
        f.write(f'  {i:2d}. {item}\n')
    
    f.write(f'\n📊 ИТОГО: {total_clean} реальных веществ\n')

print('\n✅ Очищенный список сохранен в: clean_substances_list.txt')