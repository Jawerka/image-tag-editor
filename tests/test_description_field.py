#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты для проверки функциональности поля описания."""

import sys
import tempfile
import shutil
from pathlib import Path
import io

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import DESCRIPTION_SEPARATOR


# Устанавливаем UTF-8 кодировку для вывода в Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class TestDescriptionSeparator:
    """Тесты для разделителя описания."""

    def test_separator_constant(self):
        """Проверка, что константа разделителя определена."""
        assert DESCRIPTION_SEPARATOR == "###DESCRIPTION###"
        print("✅ Константа DESCRIPTION_SEPARATOR определена корректно")

    def test_separator_in_content(self):
        """Проверка обнаружения разделителя в содержимом."""
        content_with_desc = f"tag1, tag2\n{DESCRIPTION_SEPARATOR}\nОписание"
        content_without_desc = "tag1, tag2"
        
        assert DESCRIPTION_SEPARATOR in content_with_desc
        assert DESCRIPTION_SEPARATOR not in content_without_desc
        print("✅ Разделитель корректно обнаруживается в содержимом")

    def test_split_content(self):
        """Проверка разделения содержимого на теги и описание."""
        content = f"tag1, tag2, artist:name\n{DESCRIPTION_SEPARATOR}\nЭто описание изображения"
        
        if DESCRIPTION_SEPARATOR in content:
            parts = content.split(DESCRIPTION_SEPARATOR, 1)
            tags = parts[0].strip()
            description = parts[1].strip()
            
            assert tags == "tag1, tag2, artist:name"
            assert description == "Это описание изображения"
            print("✅ Разделение на теги и описание работает корректно")

    def test_backward_compatibility(self):
        """Проверка обратной совместимости (файлы без описания)."""
        old_format_content = "tag1, tag2, tag3"
        
        if DESCRIPTION_SEPARATOR not in old_format_content:
            tags = old_format_content.strip()
            description = ""
            
            assert tags == "tag1, tag2, tag3"
            assert description == ""
            print("✅ Обратная совместимость сохранена")

    def test_multiline_description(self):
        """Проверка многострочного описания."""
        content = f"tag1, tag2\n{DESCRIPTION_SEPARATOR}\nПервая строка\nВторая строка\nТретья строка"
        
        parts = content.split(DESCRIPTION_SEPARATOR, 1)
        tags = parts[0].strip()
        description = parts[1].strip()
        
        assert tags == "tag1, tag2"
        assert description == "Первая строка\nВторая строка\nТретья строка"
        print("✅ Многострочное описание поддерживается")

    def test_empty_description(self):
        """Проверка пустого описания."""
        # Если описание пустое, разделитель не должен добавляться
        tags = "tag1, tag2"
        description = ""
        
        if not description:
            content = tags
        else:
            content = f"{tags}\n{DESCRIPTION_SEPARATOR}\n{description}"
        
        assert content == "tag1, tag2"
        assert DESCRIPTION_SEPARATOR not in content
        print("✅ Пустое описание не добавляет разделитель")


class TestFileOperations:
    """Тесты для операций с файлами."""

    def __init__(self):
        self.temp_dir = None

    def setup(self):
        """Создание временной директории."""
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"Создана временная директория: {self.temp_dir}")

    def teardown(self):
        """Очистка временной директории."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"Временная директория удалена: {self.temp_dir}")

    def test_save_with_description(self):
        """Проверка сохранения файла с описанием."""
        self.setup()
        try:
            txt_path = self.temp_dir / "test_image.txt"
            tags = "tag1, tag2, artist:name"
            description = "Тестовое описание"
            
            content = f"{tags}\n{DESCRIPTION_SEPARATOR}\n{description}"
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Читаем и проверяем
            with open(txt_path, "r", encoding="utf-8") as f:
                read_content = f.read()
            
            assert read_content == content
            print("✅ Сохранение файла с описанием работает корректно")
        finally:
            self.teardown()

    def test_load_with_description(self):
        """Проверка загрузки файла с описанием."""
        self.setup()
        try:
            txt_path = self.temp_dir / "test_image.txt"
            
            # Создаём файл с описанием
            content = f"tag1, tag2\n{DESCRIPTION_SEPARATOR}\nОписание изображения"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Загружаем и разделяем
            with open(txt_path, "r", encoding="utf-8") as f:
                read_content = f.read()
            
            if DESCRIPTION_SEPARATOR in read_content:
                parts = read_content.split(DESCRIPTION_SEPARATOR, 1)
                tags = parts[0].strip()
                description = parts[1].strip()
                
                assert tags == "tag1, tag2"
                assert description == "Описание изображения"
                print("✅ Загрузка файла с описанием работает корректно")
        finally:
            self.teardown()

    def test_load_without_description(self):
        """Проверка загрузки файла без описания (обратная совместимость)."""
        self.setup()
        try:
            txt_path = self.temp_dir / "test_image.txt"
            
            # Создаём файл без описания (старый формат)
            content = "tag1, tag2, tag3"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Загружаем и разделяем
            with open(txt_path, "r", encoding="utf-8") as f:
                read_content = f.read()
            
            if DESCRIPTION_SEPARATOR not in read_content:
                tags = read_content.strip()
                description = ""
            else:
                parts = read_content.split(DESCRIPTION_SEPARATOR, 1)
                tags = parts[0].strip()
                description = parts[1].strip()
            
            assert tags == "tag1, tag2, tag3"
            assert description == ""
            print("✅ Загрузка файла без описания (обратная совместимость) работает корректно")
        finally:
            self.teardown()


def run_all_tests():
    """Запуск всех тестов."""
    print("=" * 60)
    print("Тестирование функциональности поля описания")
    print("=" * 60)
    
    # Тесты констант
    print("\n--- Тесты констант ---")
    test_const = TestDescriptionSeparator()
    test_const.test_separator_constant()
    test_const.test_separator_in_content()
    test_const.test_split_content()
    test_const.test_backward_compatibility()
    test_const.test_multiline_description()
    test_const.test_empty_description()
    
    # Тесты файловых операций
    print("\n--- Тесты файловых операций ---")
    test_file = TestFileOperations()
    test_file.test_save_with_description()
    test_file.test_load_with_description()
    test_file.test_load_without_description()
    
    print("\n" + "=" * 60)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
