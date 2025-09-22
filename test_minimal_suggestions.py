#!/usr/bin/env python3
"""Тест алгоритма подсказок с минимальным тестовым CSV."""

import sys
from pathlib import Path
import pandas as pd

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_minimal_suggestions():
    """Тест с минимальным набором данных."""
    print("Тестирование алгоритма подсказок с минимальными данными...")
    
    from main import TagAutoCompleteApp
    
    # Создаем экземпляр приложения для тестирования
    app = TagAutoCompleteApp.__new__(TagAutoCompleteApp)
    
    # Инициализируем необходимые атрибуты
    app.tag_frequencies = {}
    app.all_tags = []
    app.all_tags_lower = []
    app.tag_cache = {}
    
    # Загружаем минимальный тестовый CSV
    test_csv = Path('test_minimal.csv')
    if not test_csv.exists():
        print("❌ Файл test_minimal.csv не найден!")
        return False
        
    df = pd.read_csv(test_csv, header=None, dtype=str, encoding='utf-8', 
                     on_bad_lines='skip', quoting=1).fillna("")
    
    print(f"Данные из CSV:")
    for i, row in df.iterrows():
        print(f"  {i}: {list(row)}")
    
    app.all_tags, app.tag_frequencies = app.process_tags_with_frequency(df)
    app.all_tags_lower = [t.lower() for t in app.all_tags]
    
    print(f"\nОбработанные теги:")
    for i, tag in enumerate(app.all_tags):
        freq = app.tag_frequencies.get(tag, 0)
        print(f"  {i}: {tag} (freq: {freq})")
    
    # Проверяем конкретные случаи
    test_cases = [
        ('s', 'safe'),
        ('oc', 'oc'),
        ('fe', 'female'),
        ('m', 'mare'),
    ]
    
    for query, expected in test_cases:
        suggestions = app.find_suggestions(query)
        print(f"\nЗапрос '{query}' -> {suggestions}")
        if suggestions and suggestions[0] == expected:
            print(f"  ✓ Первый результат '{suggestions[0]}' соответствует ожиданию '{expected}'")
        else:
            print(f"  ❌ Ожидался '{expected}', получен '{suggestions[0] if suggestions else 'None'}'")
            return False
    
    return True

if __name__ == "__main__":
    success = test_minimal_suggestions()
    if success:
        print("\n🎉 Минимальный тест прошел успешно!")
    else:
        print("\n❌ Минимальный тест провален!")
    sys.exit(0 if success else 1)
