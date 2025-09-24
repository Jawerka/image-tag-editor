#!/usr/bin/env python3
"""Тест алгоритма подсказок с чистым CSV."""

import sys
from pathlib import Path
import pandas as pd

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_clean_suggestions():
    """Тест с чистым CSV без проблемных кавычек."""
    print("Тестирование алгоритма подсказок с чистым CSV...")
    
    from main import TagAutoCompleteApp
    
    # Создаем экземпляр приложения для тестирования
    app = TagAutoCompleteApp.__new__(TagAutoCompleteApp)
    
    # Инициализируем необходимые атрибуты
    app.tag_frequencies = {}
    app.all_tags = []
    app.all_tags_lower = []
    app.tag_cache = {}
    
    # Загружаем чистый тестовый CSV
    test_csv = Path('test_clean.csv')
    if not test_csv.exists():
        print("❌ Файл test_clean.csv не найден!")
        return False
        
    # Используем ручной парсинг как в основном коде
    df = app._manual_csv_parse(test_csv)
    
    print(f"Данные из чистого CSV:")
    for i, row in df.iterrows():
        print(f"  {i}: {list(row)}")
    
    app.all_tags, app.tag_frequencies = app.process_tags_with_frequency(df)
    app.all_tags_lower = [t.lower() for t in app.all_tags]
    
    print(f"\nОбработанные теги (всего {len(app.all_tags)}):")
    for i, tag in enumerate(app.all_tags):
        freq = app.tag_frequencies.get(tag, 0)
        print(f"  {i}: '{tag}' (freq: {freq})")
    
    # Проверяем наличие тега 'oc'
    if 'oc' in app.tag_frequencies:
        print(f"\n✓ Тег 'oc' найден с частотой: {app.tag_frequencies['oc']}")
        oc_position = app.all_tags.index('oc')
        print(f"✓ Позиция 'oc' в отсортированном списке: {oc_position}")
    else:
        print(f"\n❌ Тег 'oc' не найден!")
        return False
    
    # Проверяем конкретные случаи
    test_cases = [
        ('s', 'safe', 'для "s" первым должен быть "safe"'),
        ('oc', 'oc', 'для "oc" первым должен быть точное совпадение "oc"'),
        ('fe', 'female', 'для "fe" первым должен быть "female"'),
        ('m', 'mare', 'для "m" первым должен быть "mare"'),
    ]
    
    for query, expected, description in test_cases:
        suggestions = app.find_suggestions(query)
        print(f"\nЗапрос '{query}' -> {suggestions}")
        
        if suggestions:
            freqs = [(tag, app.tag_frequencies.get(tag, 0)) for tag in suggestions]
            print(f"  С частотами: {freqs}")
            
            if suggestions[0] == expected:
                print(f"  ✓ {description}")
            else:
                print(f"  ❌ {description} - получен '{suggestions[0]}'")
                return False
        else:
            print(f"  ❌ {description} - нет результатов")
            return False
    
    return True

if __name__ == "__main__":
    success = test_clean_suggestions()
    if success:
        print("\n🎉 Тест с чистым CSV прошел успешно!")
    else:
        print("\n❌ Тест с чистым CSV провален!")
    sys.exit(0 if success else 1)
