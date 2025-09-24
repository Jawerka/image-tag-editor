#!/usr/bin/env python3
"""Диагностика проблемы с тегом 'oc'."""

import pandas as pd
from pathlib import Path

def debug_oc_tag():
    """Проверить, где именно находится тег 'oc' в данных."""
    
    # Загружаем данные
    csv_path = Path('test_derpibooru.csv')
    if not csv_path.exists():
        print("CSV файл не найден!")
        return
        
    # Сначала смотрим сырые строки
    print("=== СЫРЫЕ СТРОКИ ===")
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:10]):
            print(f"Строка {i}: {repr(line.strip())}")
    
    print("\n=== PANDAS PARSING ===")
    df = pd.read_csv(csv_path, header=None, dtype=str, encoding='utf-8', 
                     on_bad_lines='skip', quoting=3).fillna("")
    
    print(f"Всего строк в CSV: {len(df)}")
    print(f"Первые 10 строк pandas:")
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        print(f"  {i}: {list(row)}")
    
    # Ищем строки с тегом 'oc'
    oc_rows = df[df.iloc[:, 0] == 'oc']
    print(f"\nСтроки с точным тегом 'oc': {len(oc_rows)}")
    for idx, row in oc_rows.iterrows():
        print(f"  Строка {idx}: {list(row)}")
    
    # Ищем строки, которые начинаются с 'oc'
    oc_prefix_rows = df[df.iloc[:, 0].str.startswith('oc', na=False)]
    print(f"\nСтроки, начинающиеся с 'oc': {len(oc_prefix_rows)}")
    for idx, row in oc_prefix_rows.head(10).iterrows():
        print(f"  Строка {idx}: {row.iloc[0]} -> {list(row)}")
    
    # Проверяем обработку тегов
    tag_freq_map = {}
    
    for idx, row in df.iterrows():
        if len(row) < 3:
            continue
            
        # Основной тег
        main_tag = str(row.iloc[0]).strip()
        if main_tag:
            try:
                frequency = int(row.iloc[2]) if str(row.iloc[2]).isdigit() else 0
                tag_freq_map[main_tag] = frequency
                if main_tag == 'oc':
                    print(f"Найден тег 'oc' в строке {idx} с частотой {frequency}")
            except (ValueError, IndexError):
                tag_freq_map[main_tag] = 0
        
        # Альтернативные теги
        if len(row) >= 4 and str(row.iloc[3]).strip():
            alternatives = str(row.iloc[3]).strip()
            if alternatives:
                for alt_tag in alternatives.split(","):
                    alt_tag = alt_tag.strip()
                    if alt_tag and alt_tag not in tag_freq_map:
                        try:
                            base_freq = int(row.iloc[2]) if str(row.iloc[2]).isdigit() else 0
                            tag_freq_map[alt_tag] = max(1, base_freq // 2)
                            if alt_tag == 'oc':
                                print(f"Найден альтернативный тег 'oc' с частотой {tag_freq_map[alt_tag]}")
                        except (ValueError, IndexError):
                            tag_freq_map[alt_tag] = 1
    
    # Проверяем финальный result
    if 'oc' in tag_freq_map:
        print(f"Тег 'oc' в итоговом словаре с частотой: {tag_freq_map['oc']}")
    else:
        print("Тег 'oc' НЕ найден в итоговом словаре!")
    
    # Сортировка
    sorted_tags = sorted(tag_freq_map.keys(), key=lambda tag: (-tag_freq_map[tag], tag.lower()))
    
    # Найти позицию тега 'oc'
    if 'oc' in sorted_tags:
        oc_position = sorted_tags.index('oc')
        print(f"Позиция тега 'oc' в отсортированном списке: {oc_position}")
        print(f"Теги около 'oc':")
        start = max(0, oc_position - 3)
        end = min(len(sorted_tags), oc_position + 4)
        for i in range(start, end):
            marker = " -> " if i == oc_position else "    "
            print(f"{marker}{i}: {sorted_tags[i]} (freq: {tag_freq_map[sorted_tags[i]]})")
    else:
        print("Тег 'oc' не найден в отсортированном списке!")
        
    # Топ-20 для контекста
    print(f"\nТоп-20 тегов:")
    for i, tag in enumerate(sorted_tags[:20]):
        print(f"  {i+1}: {tag} (freq: {tag_freq_map[tag]})")

if __name__ == "__main__":
    debug_oc_tag()
