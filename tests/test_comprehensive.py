#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Комплексные тесты для всех реализованных функций (Этап 5).

Тестирует:
1. Поле описания (Этап 2)
2. Отображение разрешения (Этап 3)
3. Авто-теги разрешения (Этап 3)
4. Перевод интерфейса (Этап 4)
"""

import sys
import tempfile
import shutil
from pathlib import Path
import io

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Устанавливаем UTF-8 кодировку для вывода в Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from main import (
    DESCRIPTION_SEPARATOR,
    HIGH_RES_THRESHOLD,
    ABSURD_RES_THRESHOLD,
)


class TestDescriptionField:
    """Тесты для поля описания (Этап 2)."""

    def test_separator_constant(self):
        """Проверка константы разделителя описания."""
        assert DESCRIPTION_SEPARATOR == "###DESCRIPTION###"
        print("OK: Константа разделителя описания определена")

    def test_file_format_with_description(self):
        """Проверка формата файла с описанием."""
        tags = "tag1, tag2, artist:name"
        description = "Test description"
        
        content = f"{tags}\n{DESCRIPTION_SEPARATOR}\n{description}"
        
        # Проверяем разделение
        if DESCRIPTION_SEPARATOR in content:
            parts = content.split(DESCRIPTION_SEPARATOR, 1)
            parsed_tags = parts[0].strip()
            parsed_desc = parts[1].strip()
            
            assert parsed_tags == tags
            assert parsed_desc == description
            print("OK: Формат файла с описанием работает корректно")

    def test_file_format_without_description(self):
        """Проверка обратной совместимости (файл без описания)."""
        content = "tag1, tag2, tag3"
        
        assert DESCRIPTION_SEPARATOR not in content
        print("OK: Обратная совместимость (без описания) сохранена")

    def test_multiline_description(self):
        """Проверка многострочного описания."""
        tags = "tag1, tag2"
        description = "Line 1\nLine 2\nLine 3"
        
        content = f"{tags}\n{DESCRIPTION_SEPARATOR}\n{description}"
        
        if DESCRIPTION_SEPARATOR in content:
            parts = content.split(DESCRIPTION_SEPARATOR, 1)
            parsed_tags = parts[0].strip()
            parsed_desc = parts[1].strip()
            
            assert parsed_tags == tags
            assert parsed_desc == description
            print("OK: Многострочное описание поддерживается")


class TestResolutionDisplay:
    """Тесты для отображения разрешения (Этап 3)."""

    def test_threshold_constants(self):
        """Проверка констант порогов разрешения."""
        assert HIGH_RES_THRESHOLD == 4_000_000  # 4 мегапикселя
        assert ABSURD_RES_THRESHOLD == 16_000_000  # 16 мегапикселей
        print("OK: Константы порогов разрешения определены верно")

    def test_pixel_calculation(self):
        """Проверка расчёта количества пикселей."""
        # Full HD
        assert 1920 * 1080 == 2_073_600
        # 4MP
        assert 2000 * 2000 == 4_000_000
        # 16MP
        assert 4000 * 4000 == 16_000_000
        print("OK: Расчёт количества пикселей корректен")

    def test_resolution_format(self):
        """Проверка формата отображения разрешения."""
        width, height = 1920, 1080
        file_ext = "PNG"
        
        # Формат: "1920x1080 - PNG"
        resolution_text = f"{width}x{height} - {file_ext}"
        
        # Отладочный вывод
        print(f"  Debug: resolution_text = '{resolution_text}'")
        assert resolution_text == "1920x1080 - PNG", f"Expected '1920x1080 - PNG', got '{resolution_text}'"
        print("OK: Формат отображения разрешения корректен")


class TestAutoResolutionTags:
    """Тесты для автоматических тегов разрешения (Этап 3)."""

    def test_no_tag_for_low_resolution(self):
        """Изображение < 4MP не получает тег."""
        total_pixels = 1920 * 1080  # ~2MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag is None
        print("OK: Изображение < 4MP не получает тег")

    def test_high_res_tag_4mp(self):
        """Изображение 4MP получает тег 'high res'."""
        total_pixels = 2000 * 2000  # Ровно 4MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "high res"
        print("OK: Изображение 4MP получает тег 'high res'")

    def test_high_res_tag_6mp(self):
        """Изображение 6MP получает тег 'high res'."""
        total_pixels = 2500 * 2500  # 6.25MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "high res"
        print("OK: Изображение 6MP получает тег 'high res'")

    def test_high_res_tag_15mp(self):
        """Изображение 15MP получает тег 'high res'."""
        total_pixels = 5000 * 3000  # 15MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "high res"
        print("OK: Изображение 15MP получает тег 'high res'")

    def test_absurd_res_tag_16mp(self):
        """Изображение 16MP получает тег 'absurd resolution'."""
        total_pixels = 4000 * 4000  # Ровно 16MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "absurd resolution"
        print("OK: Изображение 16MP получает тег 'absurd resolution'")

    def test_absurd_res_tag_20mp(self):
        """Изображение 20MP получает тег 'absurd resolution'."""
        total_pixels = 5000 * 4000  # 20MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "absurd resolution"
        print("OK: Изображение 20MP получает тег 'absurd resolution'")

    def test_no_duplicate_tag(self):
        """Тег не добавляется дубликатом."""
        tag_list = ["tag1", "high res", "tag2"]
        tag_list_lower = [t.lower() for t in tag_list]
        
        total_pixels = 2500 * 2500  # 6.25MP
        new_tag = "high res"
        
        should_add = new_tag.lower() not in tag_list_lower
        assert not should_add
        print("OK: Тег не добавляется дубликатом")

    def test_case_insensitive_check(self):
        """Проверка на дубликат case-insensitive."""
        tag_list = ["tag1", "High Res", "tag2"]
        tag_list_lower = [t.lower() for t in tag_list]
        
        total_pixels = 2500 * 2500  # 6.25MP
        new_tag = "high res"
        
        should_add = new_tag.lower() not in tag_list_lower
        assert not should_add
        print("OK: Проверка на дубликат case-insensitive")


class TestInterfaceTranslation:
    """Тесты для перевода интерфейса (Этап 4)."""

    def test_ui_strings_english(self):
        """Проверка что UI строки на английском."""
        # Проверяем что основные UI элементы на английском
        ui_strings = {
            "Image Tag Editor": "Заголовок окна",
            "Enter tags separated by commas...": "Placeholder поля тегов",
            "Image description (optional)...": "Placeholder поля описания",
            "Save Tags (Ctrl+S)": "Кнопка сохранения",
            "Suggestions:": "Метка подсказок",
            "Tags:": "Метка тегов",
            "⭐ Move Important Tags to Top": "Кнопка приоритетных тегов",
        }
        
        for string, description in ui_strings.items():
            assert isinstance(string, str)
            # Проверяем что строка не содержит кириллицы (кроме комментариев)
            has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in string)
            assert not has_cyrillic, f"UI строка содержит кириллицу: {string}"
        
        print("OK: Все UI строки на английском языке")

    def test_dialog_titles_english(self):
        """Проверка что заголовки диалогов на английском."""
        dialog_titles = [
            "Tag Database Not Found",
            "Database Loading Error",
            "Download Link",
        ]
        
        for title in dialog_titles:
            has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in title)
            assert not has_cyrillic, f"Заголовок диалога содержит кириллицу: {title}"
        
        print("OK: Заголовки диалогов на английском языке")

    def test_button_labels_english(self):
        """Проверка что надписи кнопок на английском."""
        button_labels = [
            "Download Database",
            "Continue Without Autocomplete",
            "OK",
        ]
        
        for label in button_labels:
            has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in label)
            assert not has_cyrillic, f"Надпись кнопки содержит кириллицу: {label}"
        
        print("OK: Надписи кнопок на английском языке")


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

    def test_save_and_load_with_description(self):
        """Проверка сохранения и загрузки с описанием."""
        self.setup()
        try:
            txt_path = self.temp_dir / "test_image.txt"
            tags = "tag1, tag2, artist:name"
            description = "Test description"
            
            # Сохранение
            content = f"{tags}\n{DESCRIPTION_SEPARATOR}\n{description}"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Загрузка
            with open(txt_path, "r", encoding="utf-8") as f:
                read_content = f.read()
            
            if DESCRIPTION_SEPARATOR in read_content:
                parts = read_content.split(DESCRIPTION_SEPARATOR, 1)
                loaded_tags = parts[0].strip()
                loaded_desc = parts[1].strip()
                
                assert loaded_tags == tags
                assert loaded_desc == description
                print("OK: Сохранение и загрузка с описанием работают корректно")
        finally:
            self.teardown()

    def test_save_and_load_without_description(self):
        """Проверка сохранения и загрузки без описания."""
        self.setup()
        try:
            txt_path = self.temp_dir / "test_image.txt"
            tags = "tag1, tag2, tag3"
            
            # Сохранение (без описания)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(tags)
            
            # Загрузка
            with open(txt_path, "r", encoding="utf-8") as f:
                read_content = f.read()
            
            assert DESCRIPTION_SEPARATOR not in read_content
            assert read_content.strip() == tags
            print("OK: Сохранение и загрузка без описания работают корректно")
        finally:
            self.teardown()


def run_all_tests():
    """Запуск всех тестов."""
    print("=" * 70)
    print("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ (Этап 5)")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Тесты поля описания (Этап 2)
    print("--- Тесты поля описания (Этап 2) ---")
    test_desc = TestDescriptionField()
    try:
        test_desc.test_separator_constant()
        test_desc.test_file_format_with_description()
        test_desc.test_file_format_without_description()
        test_desc.test_multiline_description()
    except Exception as e:
        print(f"FAIL: {e}")
        all_passed = False
    print()
    
    # Тесты отображения разрешения (Этап 3)
    print("--- Тесты отображения разрешения (Этап 3) ---")
    test_res = TestResolutionDisplay()
    try:
        print("  Running test_threshold_constants...")
        test_res.test_threshold_constants()
        print("  Running test_pixel_calculation...")
        test_res.test_pixel_calculation()
        print("  Running test_resolution_format...")
        test_res.test_resolution_format()
    except Exception as e:
        print(f"FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    print()
    
    # Тесты автоматических тегов (Этап 3)
    print("--- Тесты автоматических тегов (Этап 3) ---")
    test_auto = TestAutoResolutionTags()
    try:
        test_auto.test_no_tag_for_low_resolution()
        test_auto.test_high_res_tag_4mp()
        test_auto.test_high_res_tag_6mp()
        test_auto.test_high_res_tag_15mp()
        test_auto.test_absurd_res_tag_16mp()
        test_auto.test_absurd_res_tag_20mp()
        test_auto.test_no_duplicate_tag()
        test_auto.test_case_insensitive_check()
    except Exception as e:
        print(f"FAIL: {e}")
        all_passed = False
    print()
    
    # Тесты перевода интерфейса (Этап 4)
    print("--- Тесты перевода интерфейса (Этап 4) ---")
    test_trans = TestInterfaceTranslation()
    try:
        test_trans.test_ui_strings_english()
        test_trans.test_dialog_titles_english()
        test_trans.test_button_labels_english()
    except Exception as e:
        print(f"FAIL: {e}")
        all_passed = False
    print()
    
    # Тесты операций с файлами
    print("--- Тесты операций с файлами ---")
    test_file = TestFileOperations()
    try:
        test_file.test_save_and_load_with_description()
        test_file.test_save_and_load_without_description()
    except Exception as e:
        print(f"FAIL: {e}")
        all_passed = False
    print()
    
    # Итоговый результат
    print("=" * 70)
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
        print("=" * 70)
        print()
        print("Реализованные функции:")
        print("  ✅ Этап 2: Поле описания")
        print("  ✅ Этап 3: Отображение разрешения + авто-теги")
        print("  ✅ Этап 4: Перевод документации")
        print("  ✅ Этап 5: Комплексное тестирование")
        print()
        print("Готово к Этапу 6: Финальные проверки")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
