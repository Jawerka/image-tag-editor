#!/usr/bin/env python3
"""Проверить структуру данных derpibooru.csv и примеры тегов."""

import pandas as pd
from pathlib import Path

def main():
    # Проверим структуру реального CSV файла
    csv_path = Path('derpibooru.csv')
    if csv_path.exists():
        print('CSV файл найден')
        # Читаем CSV с более гибким парсингом - на случай разного числа колонок в строках
        df = pd.read_csv(csv_path, header=None, nrows=20, dtype=str, encoding='utf-8', 
                        on_bad_lines='skip', quoting=3).fillna('')
        print('Первые 10 строк:')
        print(df.head(10))
        print('\nКолонки (индексы):', df.columns.tolist())
        
        full_df = pd.read_csv(csv_path, header=None, dtype=str, encoding='utf-8', 
                             on_bad_lines='skip', quoting=3).fillna('')
        print('Количество строк в файле:', len(full_df))
        test_tags = ['safe', 'oc', 'oc only', 'mare', 'female', 'soda']
        print('\nПроверка упомянутых тегов:')
        for tag in test_tags:
            matches = full_df[full_df.iloc[:, 0] == tag]
            if not matches.empty:
                print(f'Тег "{tag}" найден с частотой: {matches.iloc[0, 2]}')
            else:
                print(f'Тег "{tag}" НЕ найден')
                
        # Найдем теги начинающиеся с 's', 'oc', 'm', 'fe', 'cola' 
        print('\nТеги начинающиеся с примеров:')
        for prefix in ['s', 'oc', 'm', 'fe', 'cola']:
            matches = full_df[full_df.iloc[:, 0].str.startswith(prefix, na=False)]
            if not matches.empty:
                top_5 = matches.head(5)
                print(f'\nТоп-5 тегов на "{prefix}":')
                for _, row in top_5.iterrows():
                    print(f'  {row.iloc[0]} (частота: {row.iloc[2]})')
            else:
                print(f'Теги на "{prefix}" не найдены')
    else:
        print('CSV файл НЕ найден')

if __name__ == "__main__":
    main()
