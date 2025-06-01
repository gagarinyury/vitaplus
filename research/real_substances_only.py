#!/usr/bin/env python3

# Только РЕАЛЬНЫЕ названия веществ (без предложений и мусора)
real_medicines = [
    'Hydro', 'Mevacor', 'Microzide', 'Stalevo', 'Sterapred', 'Sumycin', 'Zestril'
]

real_supplements = [
    'Copper', 'Folic', 'Vitamin'  # Только чистые названия
]

real_diseases = [
    'Alzheimer', 'Crohn', 'Menkes disease', 'Wernicke', 'Wilson disease'
]

real_foods = [
    'Chinese cabbage', 'Sunscreens'
]

real_other = [
    'African', 'American', 'Child', 'Children', 'Drug', 'Health', 'Laboratory', 
    'Medications', 'Prevention', 'Supplementation', 'Treatment', 'Ukraine'
]

print('📋 ТОЛЬКО РЕАЛЬНЫЕ НАЗВАНИЯ ВЕЩЕСТВ:')
print('=' * 40)

print('💊 ЛЕКАРСТВА:')
for i, med in enumerate(real_medicines, 1):
    print(f'   {i}. {med}')

print('\n🧬 ВИТАМИНЫ/МИНЕРАЛЫ:')
for i, supp in enumerate(real_supplements, 1):
    print(f'   {i}. {supp}')

print('\n🏥 БОЛЕЗНИ:')
for i, disease in enumerate(real_diseases, 1):
    print(f'   {i}. {disease}')

print('\n🍎 ПРОДУКТЫ:')
for i, food in enumerate(real_foods, 1):
    print(f'   {i}. {food}')

print('\n❓ ПРОЧЕЕ:')
for i, item in enumerate(real_other, 1):
    print(f'   {i}. {item}')

total = len(real_medicines) + len(real_supplements) + len(real_diseases) + len(real_foods) + len(real_other)
print(f'\n📊 ИТОГО РЕАЛЬНЫХ ВЕЩЕСТВ: {total}')
print(f'   Лекарства: {len(real_medicines)}')
print(f'   БАДы/витамины: {len(real_supplements)}')  
print(f'   Болезни: {len(real_diseases)}')
print(f'   Продукты: {len(real_foods)}')
print(f'   Прочее: {len(real_other)}')

print('\n⚠️  ПРОБЛЕМА ПАРСИНГА:')
print('Из 177 "веществ" только ~30 являются реальными названиями.')
print('Остальные 147 - это части предложений из-за плохого парсинга текста.')