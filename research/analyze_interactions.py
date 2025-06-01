#!/usr/bin/env python3
import json

with open('/Users/yurygagarin/Code/1/vitaplus/research/interactions_database.json', 'r', encoding='utf-8') as f:
    interactions = json.load(f)

# Получаем все вещества, с которыми происходят взаимодействия
interacting_substances = set()
for interaction in interactions:
    substance = interaction['interacts_with'].strip()
    if substance and substance != 'unknown':
        interacting_substances.add(substance)

print('🔍 ВЕЩЕСТВА, С КОТОРЫМИ ВЗАИМОДЕЙСТВУЮТ НАШИ 25 БАДов:')
print()
sorted_substances = sorted(interacting_substances)
for i, substance in enumerate(sorted_substances, 1):
    print(f'{i:3d}. {substance}')
print(f'\nВсего найдено: {len(interacting_substances)} различных веществ')

print()
print('📋 КАТЕГОРИИ ВЗАИМОДЕЙСТВУЮЩИХ ВЕЩЕСТВ:')

# Лекарства
medicines = [s for s in sorted_substances if any(word in s.lower() for word in ['pill', 'drug', 'medication', 'therapy', 'treatment', 'antibiotic', 'hormone'])]
print(f'\n💊 ЛЕКАРСТВА ({len(medicines)}):')
for med in medicines[:10]:  # Показать первые 10
    print(f'   - {med}')

# Другие БАДы/витамины
supplements = [s for s in sorted_substances if any(word in s.lower() for word in ['vitamin', 'mineral', 'acid', 'iron', 'calcium', 'zinc', 'magnesium'])]
print(f'\n🧬 ДРУГИЕ БАДы/ВИТАМИНЫ ({len(supplements)}):')
for supp in supplements[:10]:
    print(f'   - {supp}')

# Болезни/состояния
conditions = [s for s in sorted_substances if any(word in s.lower() for word in ['disease', 'disorder', 'syndrome', 'deficiency', 'cancer', 'diabetes'])]
print(f'\n🏥 БОЛЕЗНИ/СОСТОЯНИЯ ({len(conditions)}):')
for cond in conditions[:10]:
    print(f'   - {cond}')