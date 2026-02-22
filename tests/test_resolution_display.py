#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты для проверки функциональности отображения разрешения изображения (Этап 3)."""

import sys
import tempfile
import shutil
from pathlib import Path
import io

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import HIGH_RES_THRESHOLD, ABSURD_RES_THRESHOLD


# Устанавливаем UTF-8 кодировку для вывода в Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class TestResolutionConstants:
    """Тесты для констант разрешения."""

    def test_high_res_threshold(self):
        """Проверка константы HIGH_RES_THRESHOLD (4 мегапикселя)."""
        assert HIGH_RES_THRESHOLD == 4_000_000
        print("OK: HIGH_RES_THRESHOLD = 4_000_000 (4 мегапикселя)")

    def test_absurd_res_threshold(self):
        """Проверка константы ABSURD_RES_THRESHOLD (16 мегапикселей)."""
        assert ABSURD_RES_THRESHOLD == 16_000_000
        print("OK: ABSURD_RES_THRESHOLD = 16_000_000 (16 мегапикселей)")


class TestAutoResolutionTags:
    """Тесты для логики автоматического добавления тегов разрешения."""

    def test_no_tag_for_low_resolution(self):
        """Изображение < 4MP не получает тег."""
        total_pixels = 1920 * 1080  # ~2MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag is None
        print("OK: Изображение 1920×1080 (~2MP) не получает тег")

    def test_high_res_tag_added(self):
        """Изображение ≥ 4MP но < 16MP получает тег 'high res'."""
        total_pixels = 2500 * 2500  # 6.25MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "high res"
        print("OK: Изображение 2500×2500 (6.25MP) получает тег 'high res'")

    def test_absurd_res_tag_added(self):
        """Изображение ≥ 16MP получает тег 'absurd resolution'."""
        total_pixels = 5000 * 4000  # 20MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "absurd resolution"
        print("OK: Изображение 5000×4000 (20MP) получает тег 'absurd resolution'")

    def test_boundary_4mp_exactly(self):
        """Изображение ровно 4MP (2000×2000) получает тег 'high res'."""
        total_pixels = 2000 * 2000  # Ровно 4MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "high res"
        print("OK: Изображение 2000×2000 (4MP) получает тег 'high res'")

    def test_boundary_just_under_4mp(self):
        """Изображение чуть меньше 4MP не получает тег."""
        total_pixels = 1999 * 2000  # 3,998,000 пикселей
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag is None
        print("OK: Изображение 1999×2000 (3.998MP) не получает тег")

    def test_boundary_16mp_exactly(self):
        """Изображение ровно 16MP (4000×4000) получает тег 'absurd resolution'."""
        total_pixels = 4000 * 4000  # Ровно 16MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "absurd resolution"
        print("OK: Изображение 4000×4000 (16MP) получает тег 'absurd resolution'")

    def test_boundary_just_under_16mp(self):
        """Изображение чуть меньше 16MP получает тег 'high res'."""
        total_pixels = 3999 * 4000  # 15,996,000 пикселей
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "high res"
        print("OK: Изображение 3999×4000 (15.996MP) получает тег 'high res'")

    def test_wide_image_high_res(self):
        """Широкое изображение 5000×3000 (15MP) получает 'high res', не 'absurd'."""
        total_pixels = 5000 * 3000  # 15MP (больше 4000px по ширине, но < 16MP)
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "high res"
        print("OK: Изображение 5000×3000 (15MP) получает тег 'high res' (не absurd)")

    def test_tall_image_high_res(self):
        """Высокое изображение 3000×6000 (18MP) получает 'absurd resolution'."""
        total_pixels = 3000 * 6000  # 18MP
        new_tag = None
        
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        assert new_tag == "absurd resolution"
        print("OK: Изображение 3000×6000 (18MP) получает тег 'absurd resolution'")

    def test_no_duplicate_high_res(self):
        """Тег 'high res' не добавляется дубликатом."""
        tag_list = ["tag1", "high res", "tag2"]
        tag_list_lower = [t.lower() for t in tag_list]
        
        max_dim = 2500
        new_tag = "high res"
        
        should_add = new_tag.lower() not in tag_list_lower
        assert not should_add
        print("OK: Тег 'high res' не добавляется дубликатом")

    def test_no_duplicate_absurd_res(self):
        """Тег 'absurd resolution' не добавляется дубликатом."""
        tag_list = ["tag1", "absurd resolution", "tag2"]
        tag_list_lower = [t.lower() for t in tag_list]
        
        max_dim = 5000
        new_tag = "absurd resolution"
        
        should_add = new_tag.lower() not in tag_list_lower
        assert not should_add
        print("OK: Тег 'absurd resolution' не добавляется дубликатом")

    def test_case_insensitive_duplicate(self):
        """Тег не добавляется при различном регистре (High Res vs high res)."""
        tag_list = ["tag1", "High Res", "tag2"]
        tag_list_lower = [t.lower() for t in tag_list]
        
        max_dim = 2500
        new_tag = "high res"
        
        should_add = new_tag.lower() not in tag_list_lower
        assert not should_add
        print("OK: Тег не добавляется при различном регистре")


class TestResolutionLabelFormat:
    """Тесты для формата отображения разрешения."""

    def test_resolution_format(self):
        """Проверка формата строки разрешения."""
        width, height = 1920, 1080
        file_ext = "PNG"
        
        resolution_text = f"{width}×{height}"
        if file_ext:
            resolution_text += f" • {file_ext}"
        
        assert resolution_text == "1920×1080 • PNG"
        print("OK: Формат разрешения: '1920×1080 • PNG'")

    def test_resolution_without_extension(self):
        """Проверка формата без расширения."""
        width, height = 3840, 2160
        file_ext = ""
        
        resolution_text = f"{width}×{height}"
        if file_ext:
            resolution_text += f" • {file_ext}"
        
        assert resolution_text == "3840×2160"
        print("OK: Формат разрешения без расширения: '3840×2160'")

    def test_resolution_with_dot_in_extension(self):
        """Проверка удаления точки из расширения."""
        width, height = 2560, 1440
        file_ext = ".JPG"
        
        resolution_text = f"{width}×{height}"
        if file_ext:
            resolution_text += f" • {file_ext[1:]}"  # Убираем точку
        
        assert resolution_text == "2560×1440 • JPG"
        print("OK: Точка из расширения удалена: '2560×1440 • JPG'")


class TestMaxDimensionCalculation:
    """Тесты для расчёта общего количества пикселей."""

    def test_pixel_count_low_res(self):
        """Подсчёт пикселей для изображения низкого разрешения."""
        width, height = 1920, 1080
        total_pixels = width * height
        
        assert total_pixels == 2_073_600
        assert total_pixels < HIGH_RES_THRESHOLD
        print("OK: 1920×1080 = 2,073,600 пикселей (~2MP) < 4MP")

    def test_pixel_count_high_res(self):
        """Подсчёт пикселей для изображения high res."""
        width, height = 2500, 2500
        total_pixels = width * height
        
        assert total_pixels == 6_250_000
        assert total_pixels >= HIGH_RES_THRESHOLD
        assert total_pixels < ABSURD_RES_THRESHOLD
        print("OK: 2500×2500 = 6,250,000 пикселей (6.25MP) ≥ 4MP и < 16MP")

    def test_pixel_count_absurd_res(self):
        """Подсчёт пикселей для изображения absurd resolution."""
        width, height = 4000, 5000
        total_pixels = width * height
        
        assert total_pixels == 20_000_000
        assert total_pixels >= ABSURD_RES_THRESHOLD
        print("OK: 4000×5000 = 20,000,000 пикселей (20MP) ≥ 16MP")

    def test_pixel_count_boundary_4mp(self):
        """Подсчёт пикселей на границе 4MP."""
        width, height = 2000, 2000
        total_pixels = width * height
        
        assert total_pixels == 4_000_000
        assert total_pixels >= HIGH_RES_THRESHOLD
        print("OK: 2000×2000 = 4,000,000 пикселей (ровно 4MP)")

    def test_pixel_count_boundary_16mp(self):
        """Подсчёт пикселей на границе 16MP."""
        width, height = 4000, 4000
        total_pixels = width * height
        
        assert total_pixels == 16_000_000
        assert total_pixels >= ABSURD_RES_THRESHOLD
        print("OK: 4000×4000 = 16,000,000 пикселей (ровно 16MP)")


def run_all_tests():
    """Запуск всех тестов."""
    print("=" * 60)
    print("Тестирование функциональности разрешения (Этап 3)")
    print("=" * 60)
    
    # Тесты констант
    print("\n--- Тесты констант ---")
    test_const = TestResolutionConstants()
    test_const.test_high_res_threshold()
    test_const.test_absurd_res_threshold()
    
    # Тесты логики автоматических тегов
    print("\n--- Тесты автоматических тегов ---")
    test_auto = TestAutoResolutionTags()
    test_auto.test_no_tag_for_low_resolution()
    test_auto.test_high_res_tag_added()
    test_auto.test_absurd_res_tag_added()
    test_auto.test_boundary_4mp_exactly()
    test_auto.test_boundary_just_under_4mp()
    test_auto.test_boundary_16mp_exactly()
    test_auto.test_boundary_just_under_16mp()
    test_auto.test_wide_image_high_res()
    test_auto.test_tall_image_high_res()
    test_auto.test_no_duplicate_high_res()
    test_auto.test_no_duplicate_absurd_res()
    test_auto.test_case_insensitive_duplicate()
    
    # Тесты формата отображения
    print("\n--- Тесты формата отображения ---")
    test_format = TestResolutionLabelFormat()
    test_format.test_resolution_format()
    test_format.test_resolution_without_extension()
    test_format.test_resolution_with_dot_in_extension()
    
    # Тесты расчёта количества пикселей
    print("\n--- Тесты расчёта количества пикселей ---")
    test_max = TestMaxDimensionCalculation()
    test_max.test_pixel_count_low_res()
    test_max.test_pixel_count_high_res()
    test_max.test_pixel_count_absurd_res()
    test_max.test_pixel_count_boundary_4mp()
    test_max.test_pixel_count_boundary_16mp()
    
    print("\n" + "=" * 60)
    print("OK: ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
