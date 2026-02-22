#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image Tag Editor - профессиональное приложение для добавления тегов к изображениям.

Современное приложение PyQt6 для эффективного добавления тегов к изображениям с
интеллектуальным автодополнением на основе внешних баз тегов. Предоставляет
интуитивный интерфейс с тёмной темой для управления тегами с расширенной навигацией
и горячими клавишами.

Ключевые возможности:
- Интеллектуальное автодополнение тегов с приоритизацией по релевантности
- Быстрая навигация по изображениям с помощью F-клавиш и стрелок
- Поддержка drag & drop для удобной загрузки изображений
- Автосохранение тегов в памяти при переключении между изображениями
- Тёмная тема для комфортной длительной работы
- Комплексное логирование для устранения неполадок
- Кэширование для высокой производительности при работе с большими коллекциями

Технические детали:
- Многострочное поле ввода тегов (QPlainTextEdit) заполняющее высоту правой панели
- Фиксированная панель подсказок (QListWidget) с навигацией клавиатурой и мышью
- Поддержка drag & drop изображений плюс диалог открытия файлов
- Навигация по изображениям кнопками и колесом мыши над областью просмотра
- Сохранение тегов в .txt файлах рядом с изображениями с кэшированием в памяти
- Расширенная обработка ошибок и детальное логирование (app.log + консоль)

Требования:
- Python 3.10+
- PyQt6
- pandas
- Файл базы тегов derpibooru.csv (загружается отдельно)

Использование:
    python main.py

Лицензия:
    MIT License - подробности в файле LICENSE.

База данных:
    Приложению требуется внешний файл базы тегов 'derpibooru.csv'.
    Загрузить с: https://github.com/DominikDoom/a1111-sd-webui-tagcomplete/tree/main/tags
"""
from __future__ import annotations

from pathlib import Path
import logging
import sys
import argparse
from typing import List, Optional, Tuple

import difflib
import pandas as pd
from PyQt6.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
    QObject,
    QEvent,
    QSize,
)
from PyQt6.QtGui import (
    QPixmap,
    QImageReader,
    QPalette,
    QColor,
    QKeySequence,
    QShortcut,
    QFontMetrics,
    QIcon,
    QSyntaxHighlighter,
    QTextDocument,
    QTextCharFormat,
    QBrush,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QMessageBox,
)

# Импорт системы макросов
try:
    from macro_system import MacroManager, MacroDropdown
    MACRO_SYSTEM_AVAILABLE = True
except ImportError as e:
    MACRO_SYSTEM_AVAILABLE = False

# --------------------------- Константы конфигурации ---------------------------
DEBUG_MODE = False  # Включить подробное логирование и дополнительные проверки
MIN_SUGGESTIONS = 1
MAX_SUGGESTIONS = 7
DEBOUNCE_MS = 150
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
LOG_FILE = "app.log"
TAG_DB_CSV = Path("derpibooru.csv")
DESCRIPTION_SEPARATOR = "###DESCRIPTION###"  # Разделитель между тегами и описанием

# Пороги разрешения для автоматических тегов (в пикселях)
# Основано на оригинальном определении:
# - high res: ≥ 4 мегапикселей (2000×2000px) но < 16 мегапикселей (4000×4000px)
# - absurd resolution: ≥ 16 мегапикселей (4000×4000px)
HIGH_RES_THRESHOLD = 4_000_000  # 4 мегапикселя (2000×2000)
ABSURD_RES_THRESHOLD = 16_000_000  # 16 мегапикселей (4000×4000)

# Стиль — вынесен в константу для удобства правок
APP_STYLESHEET = """
QMainWindow { background-color: #2b2b2b; font-size: 10pt; }
QLabel { color: #ffffff; padding: 4px; font-size: 10pt; }
QPlainTextEdit { background-color: #3c3f41; color: #ffffff; border: 1px solid #555555; border-radius: 6px; padding: 8px; selection-background-color: #9345c5; font-size: 10pt; }
QPushButton { background-color: #5c5c5c; color: #ffffff; border: none; border-radius: 6px; padding: 8px; font-weight: bold; font-size: 10pt; }
QPushButton:hover { background-color: #6c6c6c; }
QListWidget { background-color: #3c3f41; color: #ffffff; border: 1px solid #555555; border-radius: 6px; padding: 6px; font-size: 10pt; }
QListWidget::item { padding: 6px; border-radius: 4px; }
QListWidget::item:selected { background-color: #9345c5; color: #000000; }
QStatusBar { color: #ffffff; background-color: #3c3f41; }
"""


# --------------------------- Централизованная система логирования ---------------------------
import functools
import traceback
import time
from typing import Any, Callable, TypeVar

F = TypeVar('F', bound=Callable[..., Any])

class DetailedLogger:
    """Централизованная система логирования с поддержкой DEBUG_MODE."""
    
    def __init__(self, name: str, debug_mode: bool = False):
        self.logger = logging.getLogger(name)
        self.debug_mode = debug_mode
        self._setup_logger()
    
    def _setup_logger(self):
        """Настроить логгер с соответствующими уровнями."""
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Устанавливаем уровень логирования
        if self.debug_mode:
            self.logger.setLevel(logging.DEBUG)
            console_level = logging.DEBUG
        else:
            self.logger.setLevel(logging.WARN)
            console_level = logging.WARN
        
        # Файловый обработчик
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")

        if self.debug_mode:
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel(logging.WARN)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        
        # Форматтер
        if self.debug_mode:
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)8s] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
            )
        else:
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: str, *args, **kwargs):
        """Отладочное сообщение (только в DEBUG_MODE)."""
        if self.debug_mode:
            self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Информационное сообщение."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Предупреждение."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Ошибка."""
        self.logger.error(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Ошибка с трассировкой."""
        self.logger.exception(msg, *args, **kwargs)
    
    def user_action(self, action: str, **details):
        """Логирование действий пользователя."""
        if self.debug_mode:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            self.info(f"USER_ACTION: {action} [{detail_str}]")
        else:
            self.info(f"USER_ACTION: {action}")
    
    def performance(self, operation: str, duration: float, **details):
        """Логирование производительности."""
        if self.debug_mode:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            self.debug(f"PERFORMANCE: {operation} took {duration:.3f}s [{detail_str}]")

# Создаем глобальный логгер
logger = DetailedLogger("TagAutoComplete", DEBUG_MODE)

def log_user_action(action_name: str = None):
    """Декоратор для логирования действий пользователя."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Определяем имя действия
            if action_name:
                action = action_name
            else:
                action = func.__name__
            
            # Собираем контекст
            start_time = time.time()
            context = {}
            
            # Если это метод класса, добавляем информацию об объекте
            if args and hasattr(args[0], '__class__'):
                context['class'] = args[0].__class__.__name__
            
            try:
                # Логируем начало действия
                logger.user_action(f"{action} STARTED", **context)
                
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Логируем успешное завершение
                duration = time.time() - start_time
                logger.user_action(f"{action} COMPLETED", duration=f"{duration:.3f}s", **context)
                logger.performance(action, duration, **context)
                
                return result
                
            except Exception as e:
                # Логируем ошибку
                duration = time.time() - start_time
                logger.error(f"USER_ACTION: {action} FAILED after {duration:.3f}s - {str(e)}")
                
                if DEBUG_MODE:
                    logger.exception(f"Detailed error in {action}")
                
                # Показываем пользователю ошибку (если доступен объект приложения)
                if args and hasattr(args[0], 'show_status'):
                    args[0].show_status(f"Ошибка в {action}: {str(e)}", 5000)
                
                raise
        
        return wrapper
    return decorator

def safe_execute(operation_name: str, default_return=None):
    """Декоратор для безопасного выполнения операций с обработкой ошибок."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"SAFE_EXECUTE: {operation_name} failed - {str(e)}")
                if DEBUG_MODE:
                    logger.exception(f"Detailed error in {operation_name}")
                return default_return
        return wrapper
    return decorator


# --------------------------- Система подсветки тегов ---------------------------

class TagHighlighter(QSyntaxHighlighter):
    """Система подсветки специальных тегов в поле ввода.
    
    Подсвечивает различные категории тегов разными цветами:
    - Artist: теги - голубой цвет (#64B5F6 с прозрачностью 40%)
    - OC: теги - зеленый цвет (#81C784 с прозрачностью 40%)  
    - Количественные теги (solo, duo, trio) - желтый цвет (#FFB74D с прозрачностью 40%)
    - Видовые теги (pony, unicorn, etc.) - фиолетовый цвет (#BA68C8 с прозрачностью 40%)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_highlight_formats()
    
    def _setup_highlight_formats(self):
        """Настройка форматов подсветки для различных категорий тегов."""
        
        # Artist теги - голубой цвет
        self.artist_format = QTextCharFormat()
        self.artist_format.setBackground(QBrush(QColor(100, 181, 246, 102)))  # #64B5F6 с 40% прозрачности
        
        # OC теги - зеленый цвет
        self.oc_format = QTextCharFormat()
        self.oc_format.setBackground(QBrush(QColor(129, 199, 132, 102)))  # #81C784 с 40% прозрачности
        
        # Количественные теги - желтый цвет
        self.quantity_format = QTextCharFormat()
        self.quantity_format.setBackground(QBrush(QColor(255, 183, 77, 102)))  # #FFB74D с 40% прозрачности
        
        # Видовые теги - фиолетовый цвет
        self.species_format = QTextCharFormat()
        self.species_format.setBackground(QBrush(QColor(186, 104, 200, 102)))  # #BA68C8 с 40% прозрачности
        
        # Определяем видовые теги
        self.species_tags = {
            # Основные виды пони
            'pony', 'earth pony', 'pegasus', 'unicorn', 'alicorn', 'bat pony',
            # Другие виды
            'dragon', 'griffon', 'griffin', 'changeling', 'zebra', 'donkey', 'mule',
            'hippogriff', 'seapony', 'kirin', 'yak', 'buffalo', 'minotaur',
            # Общие категории
            'anthro', 'human', 'humanized', 'robot', 'cyborg',
            # Дополнительные варианты написания
            'earth_pony', 'bat_pony', 'sea_pony'
        }
        
        # Количественные теги
        self.quantity_tags = {'solo', 'duo', 'trio', 'group', 'crowd'}
    
    def highlightBlock(self, text):
        """Основная функция подсветки блока текста."""
        if not text.strip():
            return
        
        # Разбиваем текст на теги по запятым
        tags = [tag.strip() for tag in text.split(',')]
        current_pos = 0
        
        for tag in tags:
            if not tag:
                current_pos = text.find(',', current_pos) + 1
                continue
            
            # Находим позицию тега в тексте
            tag_start = text.find(tag, current_pos)
            if tag_start == -1:
                current_pos = text.find(',', current_pos) + 1
                continue
            
            tag_end = tag_start + len(tag)
            tag_lower = tag.lower()
            
            # Проверяем категории тегов и применяем соответствующий формат
            if tag_lower.startswith('artist:'):
                self.setFormat(tag_start, len(tag), self.artist_format)
            elif tag_lower.startswith('oc:'):
                self.setFormat(tag_start, len(tag), self.oc_format)
            elif tag_lower in self.quantity_tags:
                self.setFormat(tag_start, len(tag), self.quantity_format)
            elif self._is_species_tag(tag_lower):
                self.setFormat(tag_start, len(tag), self.species_format)
            
            # Переходим к следующему тегу
            current_pos = text.find(',', tag_end)
            if current_pos == -1:
                break
            current_pos += 1
    
    def _is_species_tag(self, tag: str) -> bool:
        """Проверить, является ли тег видовым."""
        # Проверяем точное совпадение
        if tag in self.species_tags:
            return True
        
        # Проверяем варианты с подчеркиваниями и пробелами
        tag_normalized = tag.replace('_', ' ').replace('+', ' ')
        if tag_normalized in self.species_tags:
            return True
        
        # Проверяем обратное преобразование
        tag_with_underscores = tag.replace(' ', '_')
        if tag_with_underscores in self.species_tags:
            return True
        
        return False


# --------------------------- Виджеты ---------------------------
class TagInputTextEdit(QPlainTextEdit):
    """Многострочное поле ввода с сигналами на спец. клавиши.

    Сигналы: tabPressed, upPressed, downPressed, escapePressed, enterPressed.
    """

    tabPressed = pyqtSignal()
    upPressed = pyqtSignal()
    downPressed = pyqtSignal()
    escapePressed = pyqtSignal()
    enterPressed = pyqtSignal()

    def keyPressEvent(self, event):  # pragma: no cover - GUI
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+Enter — сохранить (дублирует Ctrl+S)
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (
            modifiers & Qt.KeyboardModifier.ControlModifier
        ):
            main_window = self.window()
            if hasattr(main_window, "save_tags"):
                main_window.save_tags()
            event.accept()
            return

        if key == Qt.Key.Key_Tab:
            self.tabPressed.emit()
            event.accept()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.enterPressed.emit()
            event.accept()
            return

        if key == Qt.Key.Key_Up:
            self.upPressed.emit()
            event.accept()
            return

        if key == Qt.Key.Key_Down:
            self.downPressed.emit()
            event.accept()
            return

        if key == Qt.Key.Key_Escape:
            self.escapePressed.emit()
            event.accept()
            return

        # По умолчанию — стандартная обработка
        super().keyPressEvent(event)


class SuggestionsList(QListWidget):
    """Список подсказок — фиксированная высота, выбор через Enter/Tab и клик."""

    itemSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFixedHeight(140)

    def keyPressEvent(self, event):  # pragma: no cover - GUI
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            item = self.currentItem()
            if item:
                self.itemSelected.emit(item.text())
            event.accept()
            return

        if key == Qt.Key.Key_Escape:
            self.clear()
            event.accept()
            return

        super().keyPressEvent(event)


class ClickableImageLabel(QLabel):
    """Область предпросмотра изображений с поддержкой drag & drop и индикатором загрузки.

    Этот класс не содержит логику загрузки — она выполняется в основном окне
    (чтобы не дублировать код и позволить логирование/обработку ошибок в одном месте).
    """

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Виджет превью — даём ему резиновую политику размера; фактический минимум будет
        # динамически рассчитываться из размеров главного окна в TagAutoCompleteApp.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Более консервативный базовый минимум, чтобы не заставлять окно расти
        self.setMinimumSize(200, 150)
        # Рамка вокруг превью; уменьшили padding, чтобы картинка могла занять больше площади
        self.setStyleSheet("border: 3px dashed #6b6b6b; border-radius: 12px; padding: 8px; background-clip: padding-box;")
        # Лёгкая рамка, чтобы обозначить область дропа
        self.setStyleSheet("border: 2px dashed #666; border-radius: 8px;")

        self.loading_label = QLabel("Loading...", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet(
            "background-color: rgba(0,0,0,0.6); color: #fff; padding: 12px 18px; border-radius: 8px; font-weight: bold;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and any(url.toLocalFile().lower().endswith(ext) for url in urls for ext in IMAGE_EXTENSIONS):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if any(file_path.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                    # вызов функции в родителе (главном окне)
                    parent = self.parent()
                    if hasattr(parent, "load_image_from_path"):
                        parent.load_image_from_path(file_path)
                    event.acceptProposedAction()
                else:
                    event.ignore()
        else:
            event.ignore()

    def show_loading(self):
        self.loading_label.adjustSize()
        lw = self.loading_label.width()
        lh = self.loading_label.height()
        self.loading_label.move((self.width() - lw) // 2, (self.height() - lh) // 2)
        self.loading_label.setVisible(True)

    def hide_loading(self):
        self.loading_label.setVisible(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.loading_label.isVisible():
            self.show_loading()


class ClickOutsideFilter(QObject):
    """Скрывает подсказки при клике вне поля ввода и списка.

    Фильтр добавляется к QApplication в основном окне.
    """

    def __init__(self, parent_window: "TagAutoCompleteApp"):
        super().__init__(parent_window)
        self.window = parent_window

    def eventFilter(self, watched, event):  # pragma: no cover - GUI
        # Обрабатываем клики мыши и потерю фокуса
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.FocusOut):
            if self.window.suggestions_list.isVisible():
                if event.type() == QEvent.Type.MouseButtonPress:
                    global_pos = event.globalPosition().toPoint()
                else:
                    global_pos = None

                if global_pos is None:
                    self.window.hide_suggestions()
                    return False

                inside_input = self.window.tag_input.geometry().contains(
                    self.window.tag_input.mapFromGlobal(global_pos)
                )
                inside_suggestions = self.window.suggestions_list.geometry().contains(
                    self.window.suggestions_list.mapFromGlobal(global_pos)
                )
                if not inside_input and not inside_suggestions:
                    if DEBUG_MODE:
                        logger.debug("Click outside detected: hiding suggestions")
                    self.window.hide_suggestions()
        return super().eventFilter(watched, event)


class ImageWheelFilter(QObject):
    """Перехватывает вращение колесика мыши над изображением для навигации."""

    def __init__(self, parent_window: "TagAutoCompleteApp"):
        super().__init__(parent_window)
        self.window = parent_window

    def eventFilter(self, watched, event):  # pragma: no cover - GUI
        if event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            logger.debug(f"Wheel event detected: delta={delta}")
            if delta > 0:
                self.window.show_prev_image()
            elif delta < 0:
                self.window.show_next_image()
            return True
        return super().eventFilter(watched, event)


# --------------------------- Основное приложение ---------------------------
class TagAutoCompleteApp(QMainWindow):
    """Главное окно приложения.

    Ключевая идея: не менять поведение оригинального скрипта, но улучшить
    читабельность, структуру и UX. Все внешние точки входа (методы) сохранены.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Image Tag Editor")

        # Получаем размеры экрана для адаптивного размера окна
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            screen_w, screen_h = screen_geo.width(), screen_geo.height()

            # Устанавливаем разумный размер окна (не более 80% экрана)
            max_w = int(screen_w * 0.8)
            max_h = int(screen_h * 0.8)

            # Предпочтительные размеры, но не превышающие лимиты экрана
            preferred_w = min(1200, max_w)
            preferred_h = min(720, max_h)

            self.resize(preferred_w, preferred_h)

            # Ограничиваем минимальную ширину окна чтобы предотвратить "разрастание"
            self.setMinimumSize(800, 600)
        else:
            # Fallback для случая, когда не удается получить размеры экрана
            self.resize(1000, 600)
            self.setMinimumSize(800, 600)

        # Установка иконки для окна, заголовка и панели задач
        try:
            icon_path = Path("assets/icon.ico")
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                self.setWindowIcon(icon)
                # Устанавливаем иконку для всего приложения (панель задач)
                if QApplication.instance():
                    QApplication.instance().setWindowIcon(icon)
                logger.info("Window icon set successfully: %s", icon_path)
            else:
                logger.warning("Icon file not found: %s", icon_path)
        except Exception as exc:
            logger.exception("Failed to set window icon: %s", exc)

        # ----- Данные -----
        self.tag_db: Optional[pd.DataFrame] = None
        self.all_tags: List[str] = []
        self.all_tags_lower: List[str] = []
        self.tag_frequencies: dict[str, int] = {}  # tag -> frequency mapping
        self.tag_cache: dict[str, List[str]] = {}

        self.current_image_path: Optional[Path] = None
        self.image_list: List[Path] = []
        self.current_index: Optional[int] = None

        # Кэш текста для изображений в памяти
        # Структура: {path: {'tags': str, 'description': str}}
        self.text_cache: dict[str, dict] = {}

        # Хранение оригинального QPixmap для корректного ресайза
        self._original_pixmap: Optional[QPixmap] = None

        # Размеры текущего изображения (width, height)
        self.current_image_dimensions: Optional[Tuple[int, int]] = None

        # ----- Система макросов -----
        self.macro_manager = None
        self.macro_dropdown = None
        self._setup_macro_system()

        # ----- UI -----
        self._create_widgets()
        self._setup_layouts()
        self._apply_styles()

        # ----- Данные -----
        self._setup_data()

        # ----- Подсказки (таймер) -----
        self.suggestion_timer = QTimer(self)
        self.suggestion_timer.setSingleShot(True)
        self.suggestion_timer.setInterval(DEBOUNCE_MS)

        # ----- Подключения -----
        self._setup_connections()

        # ----- Фильтры событий -----
        self.click_filter = ClickOutsideFilter(self)
        QApplication.instance().installEventFilter(self.click_filter)
        self.wheel_filter = ImageWheelFilter(self)
        self.image_label.installEventFilter(self.wheel_filter)

        logger.info("Application initialized")

        # Попытка сразу рассчитать подходящий минимальный размер превью на старте
        try:
            self._recalc_image_label_min_size()
        except Exception:
            # пересчёт будет выполнен при первом ресайзе, так что можно проигнорировать
            pass

    # ---------------- UI: Создание виджетов ----------------
    def _create_widgets(self) -> None:
        # Навигация
        self.left_btn = QPushButton("◀")
        self.right_btn = QPushButton("▶")
        self.left_btn.setEnabled(False)
        self.right_btn.setEnabled(False)
        self.left_btn.setAccessibleName("Previous image")
        self.right_btn.setAccessibleName("Next image")
        # Увеличим размеры навигационных кнопок и сделаем их более заметными
        self.left_btn.setFixedSize(44, 100)
        self.right_btn.setFixedSize(44, 100)
        self.left_btn.setStyleSheet("QPushButton{border-radius:8px; font-weight:bold;}")
        self.right_btn.setStyleSheet("QPushButton{border-radius:8px; font-weight:bold;}")

        # Метка с именем изображения
        self.image_name_label = QLabel("No image loaded")
        self.image_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_name_label.setWordWrap(True)
        self.image_name_label.setFixedHeight(28)

        # Область предпросмотра
        self.image_label = ClickableImageLabel(self)
        self.image_label.setText("Click or drag & drop an image to load")

        # Поле ввода тегов (многострочное)
        self.tag_input = TagInputTextEdit()
        self.tag_input.setPlaceholderText("Enter tags separated by commas...")
        self.tag_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tag_input.setAccessibleName("Tags input")

        # Добавляем подсветку синтаксиса для специальных тегов
        self.tag_highlighter = TagHighlighter(self.tag_input.document())

        # Поле ввода описания (многострочное, 3-4 строки)
        self.description_input = QPlainTextEdit()
        self.description_input.setPlaceholderText("Image description (optional)...")
        self.description_input.setMaximumHeight(100)  # ~3-4 строки
        self.description_input.setMinimumHeight(80)
        self.description_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.description_input.setAccessibleName("Description input")

        # Список подсказок
        self.suggestions_label = QLabel("Suggestions:")
        # Закрепляем область подсказок — она всегда видна как элемент интерфейса
        self.suggestions_label.setVisible(True)
        self.suggestions_list = SuggestionsList(self)
        # Фиксированная высота и всегда видимый контейнер подсказок
        self.suggestions_list.setVisible(True)
        self.suggestions_list.setFixedHeight(220)

        # Устанавливаем моноширный шрифт для правильного выравнивания
        from PyQt6.QtGui import QFont
        mono_font = QFont("Consolas", 9)  # Consolas - стандартный моноширный шрифт в Windows
        mono_font.setStyleHint(QFont.StyleHint.Monospace)  # Fallback на системный моноширный
        self.suggestions_list.setFont(mono_font)

        # Кнопка сохранить
        self.save_button = QPushButton("Save Tags (Ctrl+S)")
        self.save_button.setEnabled(False)
        # Сделаем кнопку сохранения более крупной и растягиваемой
        self.save_button.setFixedHeight(44)
        self.save_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.save_button.setStyleSheet(self.save_button.styleSheet() + "QPushButton{font-size:11pt;}")

        # Кнопка для перемещения важных тегов
        self.priority_tags_button = QPushButton("⭐ Move Important Tags to Top")
        self.priority_tags_button.setEnabled(True)  # Включаем сразу - работает и без изображения
        self.priority_tags_button.setFixedHeight(36)
        self.priority_tags_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.priority_tags_button.setStyleSheet("QPushButton{background-color:#4a6741; color:#ffffff; font-weight:bold;}")
        self.priority_tags_button.setToolTip("Moves important tags (artist:, oc:, species, etc.) to the beginning of the tag list")

        # Индикатор статуса
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        
        # Метка с разрешением изображения в левой части status bar
        self.resolution_label = QLabel("")
        self.resolution_label.setStyleSheet("color: #888; font-size: 9pt;")
        self.status_bar.addPermanentWidget(self.resolution_label, 0)  # 0 = фиксированный размер

        # Шорткаты: открыть, сохранить, навигация
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.load_image)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_tags)
        QShortcut(QKeySequence("Left"), self, activated=self.show_prev_image)
        QShortcut(QKeySequence("Right"), self, activated=self.show_next_image)

        # F-key navigation hotkeys (alternative to arrow keys)
        QShortcut(QKeySequence("F1"), self, activated=self.show_prev_image)
        QShortcut(QKeySequence("F2"), self, activated=self.show_next_image)
        QShortcut(QKeySequence("F3"), self, activated=self.load_image)
        QShortcut(QKeySequence("F5"), self, activated=self.refresh_image)
        QShortcut(QKeySequence("F9"), self, activated=self.save_tags)
        QShortcut(QKeySequence("F12"), self, activated=self.focus_input)

    # ---------------- Настройка системы макросов ----------------
    def _setup_macro_system(self) -> None:
        """Инициализировать систему макросов если доступна."""
        if not MACRO_SYSTEM_AVAILABLE:
            logger.info("Macro system not available, skipping initialization")
            return

        try:
            # Инициализируем менеджер макросов
            self.macro_manager = MacroManager(self)

            # Создаём выпадающее меню макросов (будет добавлено в layout позже)
            self.macro_dropdown = MacroDropdown(self.macro_manager, self)

            logger.info("Macro system initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize macro system: %s", e)
            self.macro_manager = None
            self.macro_dropdown = None

    # ---------------- UI: Компоновка ----------------
    def _setup_layouts(self) -> None:
        main_widget = QWidget(self)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Левая панель — предпросмотр и навигация
        img_layout = QVBoxLayout()
        img_layout.addWidget(self.image_name_label)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.left_btn)
        nav_layout.addWidget(self.image_label, 2)
        nav_layout.addWidget(self.right_btn)

        img_layout.addLayout(nav_layout, 1)
        img_layout.addWidget(self.save_button)

        # Правая панель — теги и подсказки
        right_panel = QVBoxLayout()

        # Top row: Tags label and action buttons
        tags_header = QHBoxLayout()
        tags_label = QLabel("Tags:")
        tags_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        tags_header.addWidget(tags_label)
        tags_header.addStretch()

        # Add priority tags button and macro dropdown
        tags_header.addWidget(self.priority_tags_button)
        if self.macro_dropdown:
            # Make macro dropdown button square
            self.macro_dropdown.dropdown_button.setFixedSize(36, 36)
            tags_header.addWidget(self.macro_dropdown)

        right_panel.addLayout(tags_header)
        right_panel.addWidget(self.tag_input, 2)  # stretch factor 2 (возвращено)
        right_panel.addWidget(self.suggestions_label)
        right_panel.addWidget(self.suggestions_list)
        right_panel.addWidget(self.description_input)  # перемещено под список подсказок

        main_layout.addLayout(img_layout, 70)
        main_layout.addLayout(right_panel, 30)

        self.setCentralWidget(main_widget)

    # ---------------- Данные: Загрузка базы тегов ----------------
    def _setup_data(self) -> None:
        if not TAG_DB_CSV.exists():
            logger.warning("Tag database %s not found - suggestions will be unavailable.", TAG_DB_CSV)
            self.all_tags = []
            self.all_tags_lower = []
            self.tag_frequencies = {}
            return

        try:
            # Always use manual parsing for reliability
            # Standard pandas often skips lines due to incorrect quotes
            logger.info("Using manual CSV parsing for maximum reliability")
            self.tag_db = self._manual_csv_parse(TAG_DB_CSV)

            self.all_tags, self.tag_frequencies = self.process_tags_with_frequency(self.tag_db)
            self.all_tags_lower = [t.lower() for t in self.all_tags]
            logger.info("Loaded %d tags with frequencies from %s", len(self.all_tags), TAG_DB_CSV)
        except Exception as exc:
            logger.exception("Error loading tag DB: %s", exc)
            self.all_tags = []
            self.all_tags_lower = []
            self.tag_frequencies = {}

    def _manual_csv_parse(self, csv_path: Path) -> pd.DataFrame:
        """Manual CSV parsing for cases when pandas can't handle it.

        Handles lines like: tag,category,frequency,"alternatives"
        """
        import csv
        from io import StringIO

        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                try:
                    # Simple CSV line parsing
                    reader = csv.reader([line.strip()], quotechar='"', delimiter=',')
                    row = next(reader)
                    # Pad to 4 columns if needed
                    while len(row) < 4:
                        row.append("")
                    rows.append(row)
                except Exception as e:
                    logger.warning("Failed to parse line %d: %s", line_no, e)
                    continue

        logger.info("Manual CSV parsing: %d rows processed", len(rows))
        return pd.DataFrame(rows)

    def process_tags_with_frequency(self, df: pd.DataFrame) -> tuple[List[str], dict[str, int]]:
        """Extract tags and their frequencies from CSV dataframe.

        CSV structure: tag_name, category, frequency, alternatives
        Returns: (list of tags, dict tag -> frequency)
        """
        tag_freq_map: dict[str, int] = {}
        
        for _, row in df.iterrows():
            if len(row) < 3:
                continue
                
            # Основной тег из первого столбца
            main_tag = str(row.iloc[0]).strip()
            if main_tag:
                try:
                    frequency = int(row.iloc[2]) if str(row.iloc[2]).isdigit() else 0
                    tag_freq_map[main_tag] = frequency
                except (ValueError, IndexError):
                    tag_freq_map[main_tag] = 0
            
            # Альтернативные теги из четвертого столбца (если есть)
            if len(row) >= 4 and str(row.iloc[3]).strip():
                alternatives = str(row.iloc[3]).strip()
                if alternatives:
                    for alt_tag in alternatives.split(","):
                        alt_tag = alt_tag.strip()
                        if alt_tag and alt_tag not in tag_freq_map:
                            # Альтернативные теги получают половину частоты основного тега
                            try:
                                base_freq = int(row.iloc[2]) if str(row.iloc[2]).isdigit() else 0
                                tag_freq_map[alt_tag] = max(1, base_freq // 2)
                            except (ValueError, IndexError):
                                tag_freq_map[alt_tag] = 1
        
        # Сортируем теги по частоте (популярные первыми), потом алфавитно
        sorted_tags = sorted(tag_freq_map.keys(), key=lambda tag: (-tag_freq_map[tag], tag.lower()))
        
        logger.debug("Top 10 most frequent tags: %s", 
                    [(tag, tag_freq_map[tag]) for tag in sorted_tags[:10]])
        
        return sorted_tags, tag_freq_map

    # ---------------- Подключения сигналов ----------------
    def _setup_connections(self) -> None:
        self.tag_input.textChanged.connect(self.on_text_changed)
        self.suggestion_timer.timeout.connect(self.update_suggestions)
        self.suggestions_list.itemClicked.connect(lambda item: self.select_suggestion(item))
        self.suggestions_list.itemSelected.connect(self.select_suggestion)
        self.save_button.clicked.connect(lambda: self.save_tags())

        # клики по изображению
        self.image_label.clicked.connect(self.load_image)

        # клавиши в поле ввода
        self.tag_input.tabPressed.connect(self.on_tab_pressed)
        self.tag_input.enterPressed.connect(self.on_enter_pressed)
        self.tag_input.upPressed.connect(self.on_up_pressed)
        self.tag_input.downPressed.connect(self.on_down_pressed)
        self.tag_input.escapePressed.connect(self.on_escape_pressed)
        self.tag_input.textChanged.connect(self.on_text_cache_changed)

        # навигация
        self.left_btn.clicked.connect(lambda: self.show_prev_image())
        self.right_btn.clicked.connect(lambda: self.show_next_image())
        
        # кнопка важных тегов
        self.priority_tags_button.clicked.connect(lambda: self.move_important_tags_to_top())
        
        # macro system connections
        if self.macro_dropdown:
            self.macro_dropdown.macro_selected.connect(self.execute_macro)

        # Подключение для поля описания
        self.description_input.textChanged.connect(self.on_text_cache_changed)

    # ---------------- Подсказки ----------------
    def on_text_changed(self) -> None:
        """Запускается при изменении текста в поле ввода.

        Запускает debounce-таймер обновления подсказок.
        """
        current_part = self.get_current_tag_part()
        logger.debug("Text changed: current_part='%s'", current_part)
        if not current_part or len(current_part.strip()) < MIN_SUGGESTIONS:
            self.hide_suggestions()
            return
        self.suggestion_timer.start()

    def get_current_tag_part(self) -> str:
        """Вернуть текущую часть тега, в которой находится курсор.

        Тег считается фрагментом между ближайшими запятыми.
        """
        text = self.tag_input.toPlainText()
        cursor = self.tag_input.textCursor()
        cursor_pos = cursor.position()
        left = text.rfind(",", 0, cursor_pos)
        right = text.find(",", cursor_pos)
        start = 0 if left == -1 else left + 1
        end = len(text) if right == -1 else right
        fragment = text[start:end]
        return fragment.strip()

    def update_suggestions(self) -> None:
        current_part = self.get_current_tag_part()
        logger.debug("Updating suggestions for: '%s'", current_part)
        if len(current_part) < MIN_SUGGESTIONS:
            self.hide_suggestions()
            return
        suggestions = self.find_suggestions(current_part)
        logger.debug("Found suggestions: %s", suggestions)
        self.show_suggestions(suggestions)

    def find_suggestions(self, query: str) -> List[str]:
        """Найти подсказки для запроса с приоритизацией по частоте и релевантности.
        
        Новый улучшенный алгоритм:
        1. Точные совпадения (query == tag) - по частоте (самые популярные первыми)
        2. Теги, начинающиеся с query - по частоте, затем по длине (короткие лучше)
        3. Теги, где query начинает слово после разделителя - по частоте, позиции, длине
        4. Теги, содержащие query как подстроку - по частоте, позиции, длине
        
        Ключевые улучшения:
        - Строгий приоритет точных совпадений
        - Частота как главный критерий сортировки
        - Никаких орфографических исправлений
        - Максимальная производительность поиска
        """
        q = query.lower().strip()
        if not q or not self.all_tags:
            logger.debug("Empty query or no tags available")
            return []
            
        # Используем кэш для часто запрашиваемых результатов
        if q in self.tag_cache:
            logger.debug("Cache hit for '%s'", q)
            return self.tag_cache[q]

        # Функция для получения частоты тега
        def get_frequency(tag: str) -> int:
            return self.tag_frequencies.get(tag, 0)

        # Категории совпадений для приоритизации
        exact_matches = []      # [(tag, frequency)]
        prefix_matches = []     # [(tag, frequency, tag_length)]
        word_start_matches = [] # [(tag, frequency, match_position, tag_length)]
        substring_matches = []  # [(tag, frequency, match_position, tag_length)]

        # Быстрый поиск для производительности и точности
        for i in range(len(self.all_tags)):
            orig_tag = self.all_tags[i]
            lower_tag = self.all_tags_lower[i]
            frequency = get_frequency(orig_tag)
            
            if lower_tag == q:
                # Точное совпадение - наивысший приоритет
                exact_matches.append((orig_tag, frequency))
                logger.debug("Exact match found: %s (freq: %d)", orig_tag, frequency)
                
            elif lower_tag.startswith(q):
                # Префиксное совпадение - высокий приоритет
                prefix_matches.append((orig_tag, frequency, len(orig_tag)))
                
            else:
                # Поиск вхождения подстроки
                pos = lower_tag.find(q)
                if pos != -1:
                    # Проверяем, начинается ли с начала слова
                    is_word_start = (pos == 0 or lower_tag[pos - 1] in ('_', '-', ' ', ':'))
                    
                    if is_word_start:
                        word_start_matches.append((orig_tag, frequency, pos, len(orig_tag)))
                    else:
                        substring_matches.append((orig_tag, frequency, pos, len(orig_tag)))
            
            # Ранний выход для точных совпадений - если нашли точное, можно сразу показать лучшие результаты
            if exact_matches and len(exact_matches) >= 2:
                # Если нашли точные совпадения, завершаем поиск рано
                break
                
            # Ограничение для производительности - но только после потенциального точного совпадения
            total_found = len(exact_matches) + len(prefix_matches) + len(word_start_matches) + len(substring_matches)
            if total_found >= MAX_SUGGESTIONS * 8:  # Собираем больше для лучшей сортировки
                break

        # Сортировка каждой категории
        
        # 1. Точные совпадения - по частоте (популярные первыми)
        exact_matches.sort(key=lambda x: -x[1])
        exact_results = [tag for tag, _ in exact_matches]
        
        # 2. Префиксные совпадения - по частоте, затем по длине (короткие теги лучше)
        prefix_matches.sort(key=lambda x: (-x[1], x[2]))
        prefix_results = [tag for tag, _, _ in prefix_matches]
        
        # 3. Начало слова - по частоте, позиции совпадения, длине
        word_start_matches.sort(key=lambda x: (-x[1], x[2], x[3]))
        word_start_results = [tag for tag, _, _, _ in word_start_matches]
        
        # 4. Вхождения подстроки - по частоте, позиции, длине
        substring_matches.sort(key=lambda x: (-x[1], x[2], x[3]))
        substring_results = [tag for tag, _, _, _ in substring_matches]

        # Объединяем в порядке приоритета: точные -> префиксы -> начала слов -> подстроки
        all_results = exact_results + prefix_results + word_start_results + substring_results
        
        # Убираем дубликаты, сохраняя порядок
        seen = set()
        unique_results = []
        for tag in all_results:
            if tag not in seen:
                seen.add(tag)
                unique_results.append(tag)
        
        # Ограничиваем до MAX_SUGGESTIONS
        suggestions = unique_results[:MAX_SUGGESTIONS]
        
        # Кэшируем результат
        self.tag_cache[q] = suggestions
        
        # Логирование для отладки
        if suggestions:
            suggestions_with_freq = [(tag, get_frequency(tag)) for tag in suggestions]
            logger.debug("Suggestions for '%s': %s", q, suggestions_with_freq)
        else:
            logger.debug("No suggestions found for '%s'", q)
        
        return suggestions

    def show_suggestions(self, suggestions: List[str]) -> None:
        # наполняем список подсказок с частотой
        self.suggestions_list.clear()
        if not suggestions:
            self.hide_suggestions()
            return

        for s in suggestions:
            # Получаем частоту использования тега
            frequency = self.tag_frequencies.get(s, 0)
            # Конвертируем underscores и plus в пробелы для отображения
            display_tag = self.convert_tag_for_display(s)
            # Форматируем строку с выравниванием частоты справа
            display_text = self.format_suggestion_with_frequency(display_tag, frequency)
            
            item = QListWidgetItem(display_text)
            # Сохраняем оригинальный тег как данные для выбора
            item.setData(0x0100, s)  # Qt.ItemDataRole.UserRole
            
            # Применяем цветовую подсветку для специальных тегов
            self._apply_suggestion_highlighting(item, s)
            
            self.suggestions_list.addItem(item)

        if self.suggestions_list.count():
            self.suggestions_list.setCurrentRow(0)

        # показываем метку и список
        self.suggestions_label.setVisible(True)
        self.suggestions_list.setVisible(True)
        logger.debug("Showing %d suggestions with frequencies in fixed field", len(suggestions))

    def convert_tag_for_display(self, tag: str) -> str:
        """Конвертировать тег для отображения:
        - rainbow_dash → Rainbow Dash
        - rainbow+dash → Rainbow Dash
        """
        # Заменяем подчеркивания и плюсы пробелами, сохраняя оригинальный регистр
        display_tag = tag.replace('_', ' ').replace('+', ' ')
        return display_tag

    def convert_tag_for_storage(self, display_tag: str) -> str:
        """Конвертировать отображаемый тег обратно в формат хранения:
        - Rainbow Dash → rainbow_dash
        """
        # Приводим к нижнему регистру и заменяем пробелы подчеркиваниями
        return display_tag.lower().replace(' ', '_')

    def format_suggestion_with_frequency(self, display_tag: str, frequency: int) -> str:
        """Форматировать строку предложения с частотой, выровненной справа."""
        # Получаем ширину виджета для выравнивания
        widget_width = self.suggestions_list.width()
        if widget_width <= 0:
            widget_width = 300  # fallback ширина

        # Форматируем частоту с разделителями тысяч
        if frequency >= 1000000:
            freq_str = f"{frequency/1000000:.1f}M"
        elif frequency >= 1000:
            freq_str = f"{frequency/1000:.1f}K"
        else:
            freq_str = str(frequency)

        # Рассчитываем примерную ширину в символах
        font_metrics = QFontMetrics(self.suggestions_list.font())
        char_width = font_metrics.horizontalAdvance("0")
        available_chars = max(20, (widget_width - 40) // char_width)  # -40 для padding

        # Резервируем место для частоты (примерно 8 символов)
        freq_space = 8
        tag_space = available_chars - freq_space

        # Обрезаем тег если он слишком длинный
        if len(display_tag) > tag_space:
            display_tag = display_tag[:tag_space-3] + "..."

        # Создаем строку с выравниванием
        padding = available_chars - len(display_tag) - len(freq_str)
        padding = max(1, padding)  # минимум 1 пробел

        return f"{display_tag}{' ' * padding}{freq_str}"

    def _apply_suggestion_highlighting(self, item: QListWidgetItem, tag: str) -> None:
        """Применить цветовую подсветку для специальных тегов в списке предложений.
        
        Args:
            item: Элемент списка для подсветки
            tag: Оригинальный тег для анализа категории
        """
        tag_lower = tag.lower()
        
        # Определяем категорию тега и применяем соответствующий цвет фона
        if tag_lower.startswith('artist:'):
            # Artist теги - голубой цвет
            item.setBackground(QBrush(QColor(100, 181, 246, 102)))  # #64B5F6 с 40% прозрачности
        elif tag_lower.startswith('oc:'):
            # OC теги - зеленый цвет  
            item.setBackground(QBrush(QColor(129, 199, 132, 102)))  # #81C784 с 40% прозрачности
        elif tag_lower in {'solo', 'duo', 'trio', 'group', 'crowd'}:
            # Количественные теги - желтый цвет
            item.setBackground(QBrush(QColor(255, 183, 77, 102)))  # #FFB74D с 40% прозрачности
        elif self._is_species_tag(tag_lower):
            # Видовые теги - фиолетовый цвет
            item.setBackground(QBrush(QColor(186, 104, 200, 102)))  # #BA68C8 с 40% прозрачности

    def hide_suggestions(self) -> None:
        """Очистить список подсказок, но не убирать сам контейнер из интерфейса.

        Подсказки остаются закреплёнными в правой панели — это уменьшает "прыжки"
        интерфейса и делает UX более предсказуемым.
        """
        self.suggestions_list.clear()
        # не прячем сам контейнер — он всегда должен быть там
        if DEBUG_MODE:
            logger.debug("Cleared suggestions (container kept visible)")

    def select_suggestion(self, displayed_text_or_item) -> None:
        """Вставить выбранный тег в текущую позицию курсора.

        Новая логика:
        - Использует оригинальный тег из данных элемента, если доступен
        - Поддерживает пробелы вместо запятых в качестве разделителей
        - Конвертирует теги с подчеркиваниями и плюсами в читаемый формат
        """
        # Получаем оригинальный тег из данных элемента
        original_tag = None
        if hasattr(displayed_text_or_item, 'data'):
            # Это QListWidgetItem
            original_tag = displayed_text_or_item.data(0x0100)  # Qt.ItemDataRole.UserRole
        elif isinstance(displayed_text_or_item, str):
            # Это строка - может быть из старого кода
            displayed_text = displayed_text_or_item
            # Попробуем найти соответствующий элемент в списке
            for i in range(self.suggestions_list.count()):
                item = self.suggestions_list.item(i)
                if item and item.text() == displayed_text:
                    original_tag = item.data(0x0100)
                    break
            
            # Если не найден, используем отображаемый текст (fallback)
            if not original_tag:
                original_tag = displayed_text.split()[0] if displayed_text else ""
        
        if not original_tag:
            logger.warning("Could not determine original tag from: %s", displayed_text_or_item)
            return

        logger.info("Selecting suggestion: %s (original: %s)", displayed_text_or_item, original_tag)
        
        text = self.tag_input.toPlainText()
        cursor = self.tag_input.textCursor()
        cursor_pos = cursor.position()
        
        # Ищем границы текущего тега - используем как запятые, так и пробелы как разделители
        # Для более гибкого определения границ
        separators = [',', ' ']
        
        # Поиск левой границы (ищем последни�� разделитель слева от к������������рсора)
        left = -1
        for sep in separators:
            pos = text.rfind(sep, 0, cursor_pos)
            if pos > left:
                left = pos
        
        # Поиск правой границы (ищем первый разделитель справа от курсора)  
        right = len(text)
        for sep in separators:
            pos = text.find(sep, cursor_pos)
            if pos != -1 and pos < right:
                right = pos

        start = 0 if left == -1 else left + 1
        end = right

        fragment = text[start:end]
        # Сохраняем ведущие пробелы в фрагменте
        leading_ws_len = len(fragment) - len(fragment.lstrip(" \t"))
        leading_ws = fragment[:leading_ws_len]

        prefix = text[:start]
        suffix = text[end:]

        # Конвертируем тег для отображения (rainbow_dash -> Rainbow Dash)
        display_tag = self.convert_tag_for_display(original_tag)
        
        # Определяем разделитель - используем пробел как основной разделитель
        add_separator = ""
        if not suffix.strip():
            add_separator = " "  # Пробел вместо запятой
        elif suffix and not suffix[0].isspace():
            add_separator = " "  # Добавляем пробел если его н����т

        # Собираем новый текст
        new_text = prefix + leading_ws + display_tag + add_separator + suffix

        self.tag_input.setPlainText(new_text)

        # Устанавливаем новый курсор — после вставленного тега
        new_cursor_pos = len(prefix) + len(leading_ws) + len(display_tag) + len(add_separator)
        new_cursor = self.tag_input.textCursor()
        new_cursor.setPosition(new_cursor_pos)
        self.tag_input.setTextCursor(new_cursor)

        # Оставляем контейнер подска��ок видимым, но очищаем выбор
        self.suggestions_list.clearSelection()
        self.tag_input.setFocus()

    # ---------------- Управление клавишами ----------------
    def on_tab_pressed(self) -> None:
        if self.suggestions_list.count() > 0 and self.suggestions_list.currentItem():
            self.select_suggestion(self.suggestions_list.currentItem())
        else:
            self.focusNextChild()

    def on_up_pressed(self) -> None:
        if self.suggestions_list.count() > 0:
            row = self.suggestions_list.currentRow()
            if row > 0:
                self.suggestions_list.setCurrentRow(row - 1)
            else:
                self.tag_input.setFocus()
        else:
            self.update_suggestions()

    def on_down_pressed(self) -> None:
        if self.suggestions_list.count() > 0:
            row = self.suggestions_list.currentRow()
            if row < self.suggestions_list.count() - 1:
                self.suggestions_list.setCurrentRow(row + 1)
        else:
            self.update_suggestions()

    def on_enter_pressed(self) -> None:
        if self.suggestions_list.count() > 0 and self.suggestions_list.currentItem():
            self.select_suggestion(self.suggestions_list.currentItem())

    def on_escape_pressed(self) -> None:
        if self.suggestions_list.count() > 0:
            self.hide_suggestions()
        else:
            self.tag_input.clearFocus()

    def on_text_cache_changed(self) -> None:
        """Сохраняет теги и описание в память для текущего изображения."""
        if self.current_image_path:
            tags = self.tag_input.toPlainText()
            description = self.description_input.toPlainText()
            self.text_cache[str(self.current_image_path)] = {
                'tags': tags,
                'description': description
            }

    def focus_input(self) -> None:
        self.tag_input.setFocus()

    def refresh_image(self) -> None:
        """Перезагрузить текущее изображение из файла."""
        if self.current_image_path:
            self.load_image_from_path(str(self.current_image_path))
            self.show_status("Image refreshed", 2000)
        else:
            self.show_status("No image to refresh", 2000)

    def execute_macro(self, macro_name: str, macro_tags: str) -> None:
        """Execute a macro by inserting its tags into the input field.
        
        Args:
            macro_name: Name of the executed macro
            macro_tags: Comma-separated string of tags to insert
        """
        if not macro_tags.strip():
            logger.warning("Attempted to execute macro '%s' with empty tags", macro_name)
            return
        
        # Get current text and cursor position
        current_text = self.tag_input.toPlainText()
        cursor = self.tag_input.textCursor()
        cursor_pos = cursor.position()
        
        # Convert macro tags from storage format to display format
        macro_tag_list = [tag.strip() for tag in macro_tags.split(',') if tag.strip()]
        display_tags = [self.convert_tag_for_display(tag) for tag in macro_tag_list]
        
        # Determine insertion strategy based on current text
        if not current_text.strip():
            # Empty field - just insert the macro tags
            new_text = ', '.join(display_tags)
            new_cursor_pos = len(new_text)
        else:
            # Field has content - append with appropriate separator
            if current_text.rstrip().endswith(','):
                # Already has comma at end
                separator = " "
            elif current_text.rstrip().endswith(' '):
                # Has space at end - add comma
                separator = ", "
            else:
                # Need to add comma separator
                separator = ", "
            
            # Insert at end with separator
            new_text = current_text + separator + ', '.join(display_tags)
            new_cursor_pos = len(new_text)
        
        # Apply the new text
        self.tag_input.setPlainText(new_text)
        
        # Set cursor to end of inserted text
        new_cursor = self.tag_input.textCursor()
        new_cursor.setPosition(new_cursor_pos)
        self.tag_input.setTextCursor(new_cursor)
        
        # Focus the input field
        self.tag_input.setFocus()
        
        # Show status message
        tag_count = len(display_tags)
        self.show_status(f"Macro '{macro_name}' executed: {tag_count} tags inserted", 3000)
        
        logger.info("Executed macro '%s': inserted %d tags", macro_name, tag_count)

    @log_user_action("Move Important Tags to Top")
    def move_important_tags_to_top(self) -> None:
        """Переместить важные теги в начало списка тегов.
        
        Важными считаются:
        - Теги начинающиеся с "artist:"
        - Теги начинающиеся с "oc:"
        - Количественные теги: solo, duo, trio
        - Видовые теги: pony, earth pony, pegasus, unicorn, alicorn, bat pony, dragon и др.
        """
        current_text = self.tag_input.toPlainText().strip()
        if not current_text:
            self.show_status("No tags to reorder", 2000)
            return
        
        # Определяем важные теги по категориям
        priority_patterns = {
            'artist': lambda tag: tag.lower().startswith('artist:'),
            'oc': lambda tag: tag.lower().startswith('oc:'),
            'quantity': lambda tag: tag.lower().strip() in ['solo', 'duo', 'trio', 'group', 'crowd'],
            'species': lambda tag: self._is_species_tag(tag.lower().strip()),
        }
        
        # Парсим теги из текста
        tags = self._parse_tags_from_text(current_text)
        if len(tags) <= 1:
            self.show_status("Not enough tags to reorder", 2000)
            return
        
        # Разделяем теги на важные и обычные
        important_tags = []
        regular_tags = []
        
        # Сначала добавляем теги в порядке приоритета
        priority_order = ['artist', 'oc', 'quantity', 'species']
        
        for category in priority_order:
            check_func = priority_patterns[category]
            category_tags = [tag for tag in tags if check_func(tag)]
            for tag in category_tags:
                if tag not in important_tags:
                    important_tags.append(tag)
        
        # Добавляем остальные теги в том порядке, в котором они были
        for tag in tags:
            if tag not in important_tags:
                regular_tags.append(tag)
        
        # Объединяем списки
        reordered_tags = important_tags + regular_tags
        
        # Проверяем, изменился ли порядок
        if reordered_tags == tags:
            self.show_status("Tags are already in optimal order", 2000)
            return
        
        # Создаем новый текст с переупорядоченными тегами
        new_text = ', '.join(reordered_tags)
        
        # Обновляем поле ввода
        self.tag_input.setPlainText(new_text)
        
        # Курсор в конец
        cursor = self.tag_input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.tag_input.setTextCursor(cursor)
        
        # Показываем результат
        moved_count = len(important_tags)
        self.show_status(f"Moved {moved_count} important tags to top", 3000)
        
        logger.info("Reordered tags: %d important tags moved to top", moved_count)

    def _parse_tags_from_text(self, text: str) -> List[str]:
        """Парсить теги из текста, используя запятую как разделитель.
        
        Удаляет дубликаты, сохраняя порядок первого появления тега.
        """
        if not text.strip():
            return []
        
        # Используем только запятую как разделитель
        tags = [tag.strip() for tag in text.split(',') if tag.strip()]
        
        # Удаляем дубликаты, сохраняя порядок первого появления
        seen = set()
        unique_tags = []
        for tag in tags:
            # Сравниваем в нижнем регистре для обнаружения дубликатов
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_tags.append(tag)
        
        return unique_tags

    def _is_species_tag(self, tag: str) -> bool:
        """Проверить, является ли тег видовым."""
        # Список видовых тегов для пони/MLP
        species_tags = {
            # Основные виды пони
            'pony', 'earth pony', 'pegasus', 'unicorn', 'alicorn', 'bat pony',
            # Другие виды
            'dragon', 'griffon', 'griffin', 'changeling', 'zebra', 'donkey', 'mule',
            'hippogriff', 'seapony', 'kirin', 'yak', 'buffalo', 'minotaur',
            # Общие категории
            'anthro', 'human', 'humanized', 'robot', 'cyborg',
            # Дополнительные варианты написания
            'earth_pony', 'bat_pony', 'sea_pony'
        }
        
        # Проверяем точное совпадение
        if tag in species_tags:
            return True
        
        # Проверяем варианты с подчеркиваниями и пробелами
        tag_normalized = tag.replace('_', ' ').replace('+', ' ')
        if tag_normalized in species_tags:
            return True
        
        # Проверяем обратное преобразование
        tag_with_underscores = tag.replace(' ', '_')
        if tag_with_underscores in species_tags:
            return True
        
        return False

    # ---------------- Обработка изображений ----------------
    @log_user_action("Open Image Dialog")
    def load_image(self) -> None:
        """Открыть диалог выбора изображения и загрузить файл.

        Метод вызывается как из GUI (кнопка, клик по preview), так и по шорткату
        (Ctrl+O).
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif *.bmp)",
        )
        if not file_path:
            logger.user_action("Open Image Dialog CANCELLED")
            return
        self.load_image_from_path(file_path)

    @log_user_action("Load Image")
    def load_image_from_path(self, file_path: str) -> None:
        """Загрузить изображение по пути: обновить превью, список изображений и теги.

        Сохраняем оригинальный QPixmap для правильного масштабирования при ресайзе
        и логируем все ошибки.
        """
        try:
            self.image_label.show_loading()

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(file_path)

            self.current_image_path = path
            self.build_image_list(self.current_image_path.parent)

            reader = QImageReader(str(path))
            reader.setAutoTransform(True)
            image = reader.read()

            self.image_label.hide_loading()

            if image.isNull():
                self.show_status(f"Error loading image: {reader.errorString()}", 5000)
                logger.error("Failed to read image: %s", reader.errorString())
                return

            # Получаем размеры изображения
            width, height = image.width(), image.height()
            self.current_image_dimensions = (width, height)

            pixmap = QPixmap.fromImage(image)
            self._original_pixmap = pixmap
            self._update_preview_pixmap()

            # Обновляем метку с разрешением
            self.update_resolution_label()

            if self.current_image_path in self.image_list:
                self.current_index = self.image_list.index(self.current_image_path)
            else:
                self.current_index = None

            # Сначала загружаем теги из файла
            self.load_tags_from_file()
            
            # Потом добавляем авто-теги разрешения (если их еще нет)
            self._auto_add_resolution_tags(width, height)

            self.save_button.setEnabled(True)
            self.priority_tags_button.setEnabled(True)
            logger.info("Loaded image: %s (%dx%d)", self.current_image_path, width, height)
            self.update_nav_buttons()

        except Exception as exc:
            self.image_label.hide_loading()
            logger.exception("Error loading image: %s", exc)
            self.show_status(f"Error loading image: {exc}", 5000)

    def _update_preview_pixmap(self) -> None:
        """Обновить изображение предпросмотра, учитывая текущий размер виджета."""
        if not self._original_pixmap:
            return
        target = QSize(self.image_label.width(), self.image_label.height())
        scaled = self._original_pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def _recalc_image_label_min_size(self) -> None:
        """Пересчитать минимальный размер виджета превью на основе размеров окна.

        Правильный расчёт учитывает доступную область центрального виджета и
        высоту других контролов в левой панели (метка имени изображения и кнопка
        сохранения). Это предотвращает эффект "разрастания" окна, когда установка
        минимального размера дочернего виджета заставляет окно увеличиваться,
        что в свою очередь увеличивает требуемый минимальный размер — замкнутый
        цикл.
        """
        # Размер доступной центральной области (без внешних рамок)
        central = self.centralWidget()
        if central and central.size().width() > 0 and central.size().height() > 0:
            central_w = central.width()
            central_h = central.height()
        else:
            # fallback на окно целиком
            central_w = max(200, self.width())
            central_h = max(200, self.height())

        # Экранные ограничения — чтобы не запрашивать размеры больше, чем монитор
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            screen_w, screen_h = screen_geo.width(), screen_geo.height()
        else:
            screen_w, screen_h = 3840, 2160

        # Оценка ширины правой панели (текущая ширина поля тегов или его sizeHint)
        tag_w = self.tag_input.width() if self.tag_input.width() > 0 else self.tag_input.sizeHint().width()
        if tag_w <= 0:
            tag_w = int(self.width() * 0.3)

        # Оценка высоты прочих элементов в левой колонке
        name_h = self.image_name_label.sizeHint().height()
        save_h = self.save_button.sizeHint().height()
        # попытка получить разумный отступ из layout'а
        spacing = 12
        try:
            main_layout = self.centralWidget().layout()
            if main_layout:
                spacing = main_layout.spacing()
        except Exception:
            pass

        other_vertical = name_h + save_h + spacing + 24  # +24 запас на padding/margins

        # Доступное пространство под превью — вычитаем правую панель и верх/низовые контролы
        available_w_for_image = max(320, central_w - tag_w - 40)
        available_h_for_image = max(240, central_h - other_vertical - 20)

        # Желаемые проценты от общего окна (как просили): 70% ширины, 90% высоты
        # Но ограничиваем чтобы не вызывать циклический рост
        current_window_w = self.width()
        desired_w = int(current_window_w * 0.5)  # Уменьшил с 0.7 до 0.5
        desired_h = int(current_window_w * 0.9)

        # Ограничиваем желаемое доступной площадью и размерами экрана
        desired_w = min(desired_w, available_w_for_image, screen_w - 40)
        desired_h = min(desired_h, available_h_for_image, screen_h - 80)
        
        # Дополнительно ограничиваем сверху чтобы не вызывать рост окна
        desired_w = min(desired_w, 800)  # Максимум 800px для превью
        desired_h = min(desired_h, 600)  # Максимум 600px для превью

        # Приводим к разумным минимумам
        min_w, min_h = 320, 240
        desired_w = max(min_w, desired_w)
        desired_h = max(min_h, desired_h)

        # Применяем рассчитанный минимальный размер — теперь он не превышает
        # реальной доступной области, поэтому не вызывает рост окна.
        try:
            self.image_label.setMinimumSize(desired_w, desired_h)
            self._last_image_min_size = (desired_w, desired_h)
            logger.debug(
                "Recalculated image preview min size to %dx%d (central %dx%d, tag_w=%d)",
                desired_w,
                desired_h,
                central_w,
                central_h,
                tag_w,
            )
        except Exception as exc:
            logger.exception("Failed to apply image preview min size: %s", exc)

    def build_image_list(self, folder: Path) -> None:
        try:
            files = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in IMAGE_EXTENSIONS]
            self.image_list = files
            logger.debug("Built image list with %d items from %s", len(files), folder)
        except Exception as exc:
            logger.exception("Error building image list: %s", exc)
            self.image_list = []

    def show_image_by_index(self, index: int) -> None:
        """Показать изображение по индексу в списке.
        
        Автосохраняет теги и описание предыдущего изображения перед переключением.
        """
        if not self.image_list:
            return
        index = max(0, min(index, len(self.image_list) - 1))
        path = self.image_list[index]
        
        # Автосохраняем теги предыдущего изображения если они изменились
        if self.current_image_path and self.current_image_path != path:
            self.save_tags()
        
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            logger.error("Cannot read image at %s", path)
            return

        # Получаем и сохраняем размеры
        width, height = image.width(), image.height()
        self.current_image_dimensions = (width, height)

        pixmap = QPixmap.fromImage(image)
        self._original_pixmap = pixmap
        self._update_preview_pixmap()

        # Обновляем метку с разрешением
        self.current_image_path = path
        self.update_resolution_label()

        self.current_index = index
        # Сначала загружаем теги из файла
        self.load_tags_from_file()
        # Потом добавляем авто-теги разрешения (если их еще нет)
        self._auto_add_resolution_tags(width, height)

        self.update_nav_buttons()
        logger.info("Switched to image %d: %s (%dx%d)", index + 1, path.name, width, height)

    @log_user_action("Navigate Next Image")
    def show_next_image(self) -> None:
        if self.current_index is None or not self.image_list:
            logger.debug("Navigation blocked: no image list or current index")
            return
        if self.current_index < len(self.image_list) - 1:
            next_index = self.current_index + 1
            logger.debug(f"Navigating to next image: {next_index + 1}/{len(self.image_list)}")
            self.show_image_by_index(next_index)
        else:
            logger.debug("Navigation blocked: already at last image")

    @log_user_action("Navigate Previous Image")
    def show_prev_image(self) -> None:
        if self.current_index is None or not self.image_list:
            logger.debug("Navigation blocked: no image list or current index")
            return
        if self.current_index > 0:
            prev_index = self.current_index - 1
            logger.debug(f"Navigating to previous image: {prev_index + 1}/{len(self.image_list)}")
            self.show_image_by_index(prev_index)
        else:
            logger.debug("Navigation blocked: already at first image")

    def update_nav_buttons(self) -> None:
        if self.image_list and self.current_index is not None:
            self.left_btn.setEnabled(self.current_index > 0)
            self.right_btn.setEnabled(self.current_index < len(self.image_list) - 1)
        else:
            self.left_btn.setEnabled(False)
            self.right_btn.setEnabled(False)
        self.update_image_name_label()

    def update_image_name_label(self) -> None:
        """Обновить метку с именем изображения."""
        if not self.current_image_path:
            self.image_name_label.setText("No image loaded")
            return
        image_name = self.current_image_path.name
        if self.image_list and self.current_index is not None:
            counter = f"{self.current_index + 1}/{len(self.image_list)}"
            display_name = image_name if len(image_name) <= 60 else image_name[:57] + "..."
            text = f"{counter} • {display_name}"
        else:
            text = image_name
        self.image_name_label.setText(text)

    def update_resolution_label(self) -> None:
        """Обновить метку с разрешением и расширением изображения в status bar."""
        if not self.current_image_dimensions:
            self.resolution_label.setText("")
            return
        
        width, height = self.current_image_dimensions
        file_ext = self.current_image_path.suffix.upper() if self.current_image_path else ""
        
        # Формат: "1920×1080 • PNG"
        resolution_text = f"{width}×{height}"
        if file_ext:
            resolution_text += f" • {file_ext[1:]}"  # Убираем точку
        
        self.resolution_label.setText(resolution_text)

    def _auto_add_resolution_tags(self, width: int, height: int) -> None:
        """Автоматически добавить теги high res / absurd resolution.
        
        Основано на оригинальном определении:
        - high res: ≥ 4 мегапикселей (2000×2000px) но < 16 мегапикселей (4000×4000px)
        - absurd resolution: ≥ 16 мегапикселей (4000×4000px)
        
        Args:
            width: Ширина изображения в пикселях
            height: Высота изображения в пикселях
        """
        # Получаем текущие теги
        current_text = self.tag_input.toPlainText().strip()
        tag_list = [tag.strip() for tag in current_text.split(',') if tag.strip()]
        tag_list_lower = [tag.lower() for tag in tag_list]
        
        # Считаем общее количество пикселей
        total_pixels = width * height
        
        # Определяем нужный тег на основе общего количества пикселей
        new_tag = None
        if total_pixels >= ABSURD_RES_THRESHOLD:
            new_tag = "absurd resolution"
        elif total_pixels >= HIGH_RES_THRESHOLD:
            new_tag = "high res"
        
        # Добавляем тег если его еще нет
        if new_tag and new_tag.lower() not in tag_list_lower:
            tag_list.append(new_tag)
            new_tags_text = ', '.join(tag_list)
            self.tag_input.setPlainText(new_tags_text)
            self.show_status(f"Tag added: {new_tag}", 2000)
            logger.info(
                "Auto-added resolution tag '%s' for %dx%d image (%.2f MP)",
                new_tag, width, height, total_pixels / 1_000_000
            )

    def load_tags_from_file(self) -> None:
        """Загрузить теги и описание из файла или кэша."""
        if not self.current_image_path:
            return
        
        image_path_str = str(self.current_image_path)
        
        # Проверяем кэш сначала
        if image_path_str in self.text_cache:
            cached_data = self.text_cache[image_path_str]
            self.tag_input.setPlainText(cached_data.get('tags', ''))
            self.description_input.setPlainText(cached_data.get('description', ''))
            logger.info("Loaded cached text for %s", self.current_image_path.name)
            # курсор в конец
            cursor = self.tag_input.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.tag_input.setTextCursor(cursor)
            return

        txt_path = self.current_image_path.with_suffix(".txt")
        if txt_path.exists():
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Разделяем на теги и описание
                if DESCRIPTION_SEPARATOR in content:
                    parts = content.split(DESCRIPTION_SEPARATOR, 1)
                    tags = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ""
                else:
                    # Обратная совместимость: файл без описания
                    tags = content.strip()
                    description = ""
                
                # Заполняем поля
                self.tag_input.setPlainText(tags)
                self.description_input.setPlainText(description)
                logger.info("Loaded tags and description from %s", txt_path.name)
            except Exception as exc:
                logger.exception("Error loading tags: %s", exc)
                self.show_status(f"Error loading tags: {exc}", 5000)
                return
        else:
            self.tag_input.setPlainText("")
            self.description_input.setPlainText("")
            logger.info("No tags file found for %s, fields cleared", self.current_image_path.name)

        cursor = self.tag_input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.tag_input.setTextCursor(cursor)

    @log_user_action("Save Tags")
    def save_tags(self) -> None:
        """Сохранить теги и описание в файл.
        
        Файл создаётся только если есть теги или описание.
        Пустые файлы не создаются.
        """
        if not self.current_image_path:
            logger.warning("Attempted to save tags without loaded image")
            self.show_status("No image loaded to save tags for", 3000)
            return

        tags = self.tag_input.toPlainText().strip()
        description = self.description_input.toPlainText().strip()
        txt_path = self.current_image_path.with_suffix(".txt")

        # Проверяем есть ли что сохранять
        if not tags and not description:
            # Если файл существовал ранее, удаляем его (теги были очищены)
            if txt_path.exists():
                try:
                    txt_path.unlink()
                    logger.info("Deleted empty tags file: %s", txt_path.name)
                except Exception as exc:
                    logger.exception("Error deleting empty tags file: %s", exc)
            return

        # Формируем содержимое файла
        if description:
            content = f"{tags}\n{DESCRIPTION_SEPARATOR}\n{description}"
        else:
            content = tags

        # Логируем детали операции в дебаг-режиме
        if DEBUG_MODE:
            tag_count = len([tag.strip() for tag in tags.split(',') if tag.strip()])
            desc_lines = len(description.split('\n')) if description else 0
            logger.debug(f"Saving {tag_count} tags and {desc_lines} description lines to {txt_path}")

        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Tags and description saved to %s", txt_path)
            self.show_status(f"Tags saved to {txt_path.name}", 3000)
        except Exception as exc:
            logger.exception("Error saving tags: %s", exc)
            self.show_status(f"Error saving tags: {exc}", 5000)

    # ---------------- UX и стили ----------------
    def show_status(self, message: str, timeout: int = 0) -> None:
        """Показать сообщение в статус-баре (в миллисекундах).

        Применяется как краткое уведомление о результате операции.
        """
        self.status_bar.showMessage(message, timeout)

    def _show_missing_database_dialog(self) -> None:
        """Show dialog about missing tag database."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Tag Database Not Found")

        text = (
            "The derpibooru.csv file was not found!\n\n"
            "Tag autocomplete will be unavailable.\n\n"
            "To enable autocomplete:\n"
            "1. Download the derpibooru.csv file\n"
            "2. Place it in the program folder\n"
            "3. Restart the application"
        )
        msg.setText(text)

        # Create buttons
        download_btn = msg.addButton("Download Database", QMessageBox.ButtonRole.ActionRole)
        ok_btn = msg.addButton("Continue Without Autocomplete", QMessageBox.ButtonRole.AcceptRole)

        msg.exec()

        # Handle button click
        if msg.clickedButton() == download_btn:
            self._open_database_download_link()

    def _show_database_error_dialog(self, error: str) -> None:
        """Show dialog about database loading error."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Database Loading Error")

        text = (
            f"Error loading derpibooru.csv file:\n\n{error}\n\n"
            "Possible causes:\n"
            "• Corrupted file\n"
            "• Incorrect format\n"
            "• Insufficient memory\n\n"
            "Autocomplete will be unavailable."
        )
        msg.setText(text)
        msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msg.exec()

    def _open_database_download_link(self) -> None:
        """Open database download link."""
        import webbrowser
        url = "https://github.com/DominikDoom/a1111-sd-webui-tagcomplete/tree/main/tags"
        try:
            webbrowser.open(url)
            self.show_status("Database download link opened", 3000)
        except Exception as e:
            logger.exception("Failed to open browser: %s", e)
            # Show dialog with link to copy
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Download Link")
            msg.setText(f"Copy this link to your browser:\n\n{url}")
            msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
            msg.exec()

    def _apply_styles(self) -> None:
        # Тёмная палитра для комфортного просмотра
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(142, 45, 197).lighter())
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app = QApplication.instance()
        if app:
            app.setPalette(dark_palette)
            app.setStyleSheet(APP_STYLESHEET)

    # ---------------- События окна ----------------
    def resizeEvent(self, event):  # pragma: no cover - GUI
        # Пересчитать целевой минимальный размер превью относительно текущего окна.
        # Высота превью — 90% от общей высоты окна, ширина — 70% от общей ширины окна.
        try:
            self._recalc_image_label_min_size()
        except Exception as exc:
            logger.exception("Error recalculating image label size: %s", exc)

        # при ресайзе — пересчитываем превью
        self._update_preview_pixmap()

        # ограничиваем ширину поля для тегов примерно под 100 символов
        fm = QFontMetrics(self.tag_input.font())
        width_for_100 = fm.horizontalAdvance("0") * 100 + 32
        max_allowed = int(self.width() * 0.45)
        target_width = min(width_for_100, max_allowed)
        self.tag_input.setMaximumWidth(target_width)
        # description_input тоже ограничиваем той же шириной
        self.description_input.setMaximumWidth(target_width)
        return super().resizeEvent(event)


# --------------------------- Парсинг аргументов командной строки -----------------------------------

def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки для поддержки открытия файлов изображений.
    
    Поддерживает:
    - Открытие одного или нескольких файлов изображений
    - Работу в качестве программы по умолчанию в Windows
    """
    parser = argparse.ArgumentParser(
        description="Image Tag Editor - Professional image tagging application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Запуск без файлов
  python main.py image.jpg                 # Открыть конкретный файл
  python main.py "C:\\Photos\\photo.png"   # Открыть файл по полному пути
  
Supported formats: PNG, JPG, JPEG, WEBP, GIF, BMP
        """
    )
    
    parser.add_argument(
        "image_file",
        nargs="?",
        help="Путь к файлу изображения для открытия"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Image Tag Editor v1.3.0"
    )
    
    return parser.parse_args()


# --------------------------- Точка входа -----------------------------------

def main() -> None:
    """Основная функция запуска приложения с поддержкой аргументов командной строки."""
    logger.info("Starting TagAutoCompleteApp")
    
    # Парсинг аргументов командной строки
    args = parse_args()
    
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = TagAutoCompleteApp()
        window.show()
        
        # Если передан путь к изображению, загружаем его после отображения окна
        if args.image_file:
            image_path = Path(args.image_file)
            if image_path.exists() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                logger.info("Loading image from command line argument: %s", image_path)
                # Используем QTimer.singleShot для загрузки изображения после полной инициализации UI
                QTimer.singleShot(100, lambda: window.load_image_from_path(str(image_path)))
            else:
                if not image_path.exists():
                    logger.error("Image file not found: %s", image_path)
                    window.show_status(f"Image file not found: {image_path}", 5000)
                else:
                    logger.error("Unsupported image format: %s", image_path.suffix)
                    window.show_status(f"Unsupported image format: {image_path.suffix}", 5000)
        
        sys.exit(app.exec())
    except ImportError as e:
        if "PyQt6" in str(e):
            print("ОШИБКА: PyQt6 не установлен.")
            print("Решение: pip install -r requirements.txt")
        else:
            print(f"Ошибка импорта: {e}")
            print("При ошибках DLL установите Visual C++ Redistributable:")
            print("https://download.visualstudio.microsoft.com/download/pr/7ebf5fdb-36dc-4145-b0a0-90d3d5990a61/CC0FF0EB1DC3F5188AE6300FAEF32BF5BEEBA4BDD6E8E445A9184072096B713B/VC_redist.x64.exe")
        sys.exit(1)
    except Exception as e:
        print(f"Критическая ошибка при запуске: {e}")
        print("Проверьте файл app.log для получения подробной информации")
        logger.exception("Critical startup error")
        sys.exit(1)


if __name__ == "__main__":
    main()
