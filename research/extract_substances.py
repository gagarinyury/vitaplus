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

print('📋 ПОЛНЫЙ СПИСОК 177 ВЕЩЕСТВ ДЛЯ ВЗАИМОДЕЙСТВИЙ:')
print('=' * 60)

sorted_substances = sorted(interacting_substances)
for i, substance in enumerate(sorted_substances, 1):
    print(f'{i:3d}. {substance}')

print('=' * 60)
print(f'Всего: {len(interacting_substances)} веществ')

# Сохранить в файл для удобства
with open('/Users/yurygagarin/Code/1/vitaplus/research/all_interacting_substances.txt', 'w', encoding='utf-8') as f:
    f.write('ПОЛНЫЙ СПИСОК ВЕЩЕСТВ ДЛЯ ВЗАИМОДЕЙСТВИЙ\n')
    f.write('=' * 50 + '\n\n')
    for i, substance in enumerate(sorted_substances, 1):
        f.write(f'{i:3d}. {substance}\n')
    f.write(f'\nВсего: {len(interacting_substances)} веществ\n')

print('\n✅ Список также сохранен в файл: all_interacting_substances.txt')