#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image Tag Editor - Professional image tagging application with intelligent autocomplete.

This is a modern PyQt6 application for efficient image tagging with smart autocomplete
features based on external tag databases. It provides an intuitive dark-themed interface
for managing image tags with advanced navigation and keyboard shortcuts.

Key Features:
- Intelligent tag autocomplete with relevance prioritization
- Fast image navigation using F-keys and arrow keys
- Drag & drop support for convenient image loading
- Auto-save tags in memory when switching between images
- Dark theme for comfortable extended use
- Comprehensive logging for troubleshooting
- Caching for fast performance with large collections

Technical Details:
- Multi-line tag input field (QPlainTextEdit) that fills the right panel height
- Fixed suggestions panel (QListWidget) with keyboard and mouse navigation
- Drag & drop image support plus file dialog for opening images
- Image navigation using buttons and mouse wheel over image area
- Tag persistence in .txt files alongside images with memory caching
- Enhanced error handling and detailed logging (app.log + console)

Requirements:
- Python 3.10+
- PyQt6
- pandas
- derpibooru.csv tag database (downloaded separately)

Usage:
    python main.py

License:
    MIT License - see LICENSE file for details.

Database:
    This application requires an external tag database file 'derpibooru.csv'.
    Download from: https://github.com/DominikDoom/a1111-sd-webui-tagcomplete/tree/main/tags
"""
from __future__ import annotations

from pathlib import Path
import logging
import sys
from typing import List, Optional

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
)

# --------------------------- Константы конфигурации ---------------------------
MIN_SUGGESTIONS = 1
MAX_SUGGESTIONS = 5
DEBOUNCE_MS = 150
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
LOG_FILE = "app.log"
TAG_DB_CSV = Path("derpibooru.csv")

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


# --------------------------- Логирование -------------------------------------
logger = logging.getLogger("TagAutoComplete")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# --------------------------- Виджеты ----------------------------------------
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
        # Небольшой базовый минимум на случай, если динамика ещё не применена
        self.setMinimumSize(320, 240)
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


# --------------------------- Основное приложение ----------------------------
class TagAutoCompleteApp(QMainWindow):
    """Главное окно приложения.

    Ключевая идея: не менять поведение оригинального скрипта, но улучшить
    читабельность, структуру и UX. Все внешние точки входа (методы) сохранены.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Image Tag Editor")
        self.resize(1200, 720)
        
        # Установка иконки для окна, заголовка и панели задач
        try:
            icon_path = Path("icon.ico")
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
        self.tag_cache: dict[str, List[str]] = {}

        self.current_image_path: Optional[Path] = None
        self.image_list: List[Path] = []
        self.current_index: Optional[int] = None

        # кэш текста для изображений в памяти
        self.text_cache: dict[str, str] = {}

        # хранение оригинального QPixmap для корректного ресайза
        self._original_pixmap: Optional[QPixmap] = None

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

        # ----- Соединения -----
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

    # ---------------- UI: создание виджетов ----------------
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

        # Список подсказок
        self.suggestions_label = QLabel("Suggestions:")
        # Закрепляем область подсказок — она всегда видна как элемент интерфейса
        self.suggestions_label.setVisible(True)
        self.suggestions_list = SuggestionsList(self)
        # Фиксированная высота и всегда видимый контейнер подсказок
        self.suggestions_list.setVisible(True)
        self.suggestions_list.setFixedHeight(220)

        # Кнопка сохранить
        self.save_button = QPushButton("Save Tags (Ctrl+S)")
        self.save_button.setEnabled(False)
        # Сделаем кнопку сохранения более крупной и растягиваемой
        self.save_button.setFixedHeight(44)
        self.save_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.save_button.setStyleSheet(self.save_button.styleSheet() + "QPushButton{font-size:11pt;}")

        # Индикатор статуса
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

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

    # ---------------- UI: компоновка ----------------
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
        tags_label = QLabel("Tags:")
        tags_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        right_panel.addWidget(tags_label)
        right_panel.addWidget(self.tag_input, 2)
        right_panel.addWidget(self.suggestions_label)
        right_panel.addWidget(self.suggestions_list)

        main_layout.addLayout(img_layout, 70)
        main_layout.addLayout(right_panel, 30)

        self.setCentralWidget(main_widget)

    # ---------------- Данные: загрузка базы тегов ----------------
    def _setup_data(self) -> None:
        if not TAG_DB_CSV.exists():
            logger.warning("Tag database %s not found — подсказки будут недоступны.", TAG_DB_CSV)
            self.all_tags = []
            self.all_tags_lower = []
            return

        try:
            self.tag_db = pd.read_csv(TAG_DB_CSV, dtype=str, encoding="utf-8", low_memory=False).fillna("")
            self.all_tags = self.process_tags(self.tag_db)
            self.all_tags_lower = [t.lower() for t in self.all_tags]
            logger.info("Loaded %d tags from %s", len(self.all_tags), TAG_DB_CSV)
        except Exception as exc:
            logger.exception("Error loading tag DB: %s", exc)
            self.all_tags = []
            self.all_tags_lower = []

    @staticmethod
    def process_tags(df: pd.DataFrame) -> List[str]:
        """Извлечь уникальные теги из датафрейма CSV.

        Возвращает отсортированный список тегов (регистронезависимая сортировка).
        """
        tags_set: set[str] = set()
        for _, row in df.iterrows():
            for cell in row:
                if not isinstance(cell, str):
                    continue
                text = cell.strip()
                if not text:
                    continue
                # столбцы могут содержать списки через запятую
                if "," in text:
                    for part in text.split(","):
                        p = part.strip()
                        if p:
                            tags_set.add(p)
                else:
                    tags_set.add(text)
        return sorted(tags_set, key=lambda s: s.lower())

    # ---------------- Подключения сигналов ----------------
    def _setup_connections(self) -> None:
        self.tag_input.textChanged.connect(self.on_text_changed)
        self.suggestion_timer.timeout.connect(self.update_suggestions)
        self.suggestions_list.itemClicked.connect(lambda item: self.select_suggestion(item.text()))
        self.suggestions_list.itemSelected.connect(self.select_suggestion)
        self.save_button.clicked.connect(self.save_tags)

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
        self.left_btn.clicked.connect(self.show_prev_image)
        self.right_btn.clicked.connect(self.show_next_image)

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
        q = query.lower()
        if not q or not self.all_tags:
            logger.debug("No query or empty tag list — returning []")
            return []
        if q in self.tag_cache:
            logger.debug("Cache hit for '%s'", q)
            return self.tag_cache[q]

        # Improved substring matching prioritizing relevance
        exact = []
        starts = []
        contains = []
        word_starts = []  # words that start with query after underscore/space

        for orig, lower in zip(self.all_tags, self.all_tags_lower):
            if lower == q:
                exact.append(orig)
            elif lower.startswith(q):
                starts.append(orig)
            elif q in lower:
                # Check if query starts a word part (after underscore, space, or dash)
                parts = lower.replace('_', ' ').replace('-', ' ').split()
                is_word_start = any(part.startswith(q) for part in parts)
                if is_word_start:
                    word_starts.append(orig)
                else:
                    contains.append(orig)
            
            if len(exact) + len(starts) + len(word_starts) + len(contains) >= MAX_SUGGESTIONS * 2:
                break

        # Prioritize: exact -> starts with -> word starts -> contains
        results = exact + starts + word_starts + contains
        
        # Add fuzzy matches if we still need more
        if len(results) < MAX_SUGGESTIONS:
            close = difflib.get_close_matches(q, self.all_tags_lower, n=MAX_SUGGESTIONS, cutoff=0.6)
            for c in close:
                try:
                    idx = self.all_tags_lower.index(c)
                    candidate = self.all_tags[idx]
                    if candidate not in results:
                        results.append(candidate)
                except ValueError:
                    continue
                if len(results) >= MAX_SUGGESTIONS:
                    break

        suggestions = results[:MAX_SUGGESTIONS]
        self.tag_cache[q] = suggestions
        logger.debug("Substring suggestions for '%s' -> %s", q, suggestions)
        return suggestions

    def show_suggestions(self, suggestions: List[str]) -> None:
        # наполняем список подсказок
        self.suggestions_list.clear()
        if not suggestions:
            self.hide_suggestions()
            return

        for s in suggestions:
            item = QListWidgetItem(s)
            self.suggestions_list.addItem(item)

        if self.suggestions_list.count():
            self.suggestions_list.setCurrentRow(0)

        # показываем метку и список
        self.suggestions_label.setVisible(True)
        self.suggestions_list.setVisible(True)
        logger.debug("Showing %d suggestions in fixed field", len(suggestions))

    def hide_suggestions(self) -> None:
        """Очистить список подсказок, но не убирать сам контейнер из интерфейса.

        Подсказки остаются закреплёнными в правой панели — это уменьшает "прыжки"
        интерфейса и делает UX более предсказуемым.
        """
        self.suggestions_list.clear()
        # не прячем сам контейнер — он всегда должен быть там
        logger.debug("Cleared suggestions (container kept visible)")

    def select_suggestion(self, tag: str) -> None:
        """Вставить выбранный тег в текущую позицию курсора.

        Исправлена логика так, чтобы сохранять пробел(ы) перед выбранным токеном
        (если они были), а также не удалять пробел после принятия предложения.
        """
        logger.info("Selecting suggestion: %s", tag)
        text = self.tag_input.toPlainText()
        cursor = self.tag_input.textCursor()
        cursor_pos = cursor.position()
        left = text.rfind(",", 0, cursor_pos)
        right = text.find(",", cursor_pos)
        start = 0 if left == -1 else left + 1
        end = len(text) if right == -1 else right

        fragment = text[start:end]
        # Сохраняем ведущие пробелы в фрагменте (если пользователь ставил пробел после запятой)
        leading_ws_len = len(fragment) - len(fragment.lstrip(" 	"))
        leading_ws = fragment[:leading_ws_len]

        prefix = text[:start]
        suffix = text[end:]

        new_token = tag.strip()
        # Если после фрагмента нет непустых символов — добавляем разделитель
        add_separator = False
        if not suffix.strip():
            add_separator = True

        # Собираем новый текст, осторожно восстанавливая пробелы
        new_text = prefix + leading_ws + new_token
        if add_separator:
            new_text += ", "
        new_text += suffix

        self.tag_input.setPlainText(new_text)

        # Устанавливаем новый курсор — после вставленного токена
        new_cursor_pos = len(prefix) + len(leading_ws) + len(new_token)
        if add_separator:
            new_cursor_pos += 2  # длина ", "
        new_cursor = self.tag_input.textCursor()
        new_cursor.setPosition(new_cursor_pos)
        self.tag_input.setTextCursor(new_cursor)

        # Оставляем контейнер подсказок видимым, но очищаем выбор
        self.suggestions_list.clearSelection()
        self.tag_input.setFocus()

    # ---------------- Управление клавишами ----------------
    def on_tab_pressed(self) -> None:
        if self.suggestions_list.count() > 0 and self.suggestions_list.currentItem():
            self.select_suggestion(self.suggestions_list.currentItem().text())
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
            self.select_suggestion(self.suggestions_list.currentItem().text())

    def on_escape_pressed(self) -> None:
        if self.suggestions_list.count() > 0:
            self.hide_suggestions()
        else:
            self.tag_input.clearFocus()

    def on_text_cache_changed(self) -> None:
        """Сохраняет содержимое поля в память (кэш) для текущего изображения."""
        if self.current_image_path:
            current_text = self.tag_input.toPlainText()
            self.text_cache[str(self.current_image_path)] = current_text

    def focus_input(self) -> None:
        self.tag_input.setFocus()

    def refresh_image(self) -> None:
        """Перезагрузить текущее изображение из файла."""
        if self.current_image_path:
            self.load_image_from_path(str(self.current_image_path))
            self.show_status("Image refreshed", 2000)
        else:
            self.show_status("No image to refresh", 2000)

    # ---------------- Работа с изображениями ----------------
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
            return
        self.load_image_from_path(file_path)

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

            pixmap = QPixmap.fromImage(image)
            self._original_pixmap = pixmap
            self._update_preview_pixmap()

            if self.current_image_path in self.image_list:
                self.current_index = self.image_list.index(self.current_image_path)
            else:
                self.current_index = None

            self.load_tags_from_file()
            self.save_button.setEnabled(True)
            logger.info("Loaded image: %s", self.current_image_path)
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
        desired_w = int(self.width() * 0.7)
        desired_h = int(self.height() * 0.9)

        # Ограничиваем желаемое доступной площадью и размерами экрана
        desired_w = min(desired_w, available_w_for_image, screen_w - 40)
        desired_h = min(desired_h, available_h_for_image, screen_h - 80)

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
        if not self.image_list:
            return
        index = max(0, min(index, len(self.image_list) - 1))
        path = self.image_list[index]
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            logger.error("Cannot read image at %s", path)
            return
        pixmap = QPixmap.fromImage(image)
        self._original_pixmap = pixmap
        self._update_preview_pixmap()
        self.current_image_path = path
        self.current_index = index
        self.load_tags_from_file()
        self.update_nav_buttons()
        logger.info("Switched to image %d: %s", self.current_index, self.current_image_path)

    def show_next_image(self) -> None:
        if self.current_index is None or not self.image_list:
            return
        if self.current_index < len(self.image_list) - 1:
            self.show_image_by_index(self.current_index + 1)

    def show_prev_image(self) -> None:
        if self.current_index is None or not self.image_list:
            return
        if self.current_index > 0:
            self.show_image_by_index(self.current_index - 1)

    def update_nav_buttons(self) -> None:
        if self.image_list and self.current_index is not None:
            self.left_btn.setEnabled(self.current_index > 0)
            self.right_btn.setEnabled(self.current_index < len(self.image_list) - 1)
        else:
            self.left_btn.setEnabled(False)
            self.right_btn.setEnabled(False)
        self.update_image_name_label()

    def update_image_name_label(self) -> None:
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

    def load_tags_from_file(self) -> None:
        if not self.current_image_path:
            return
        image_path_str = str(self.current_image_path)
        if image_path_str in self.text_cache:
            cached_text = self.text_cache[image_path_str]
            self.tag_input.setPlainText(cached_text)
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
                    tags = f.read().strip()
                self.tag_input.setPlainText(tags)
                logger.info("Loaded tags from %s", txt_path.name)
            except Exception as exc:
                logger.exception("Error loading tags: %s", exc)
                self.show_status(f"Error loading tags: {exc}", 5000)
                return
        else:
            self.tag_input.setPlainText("")
            logger.info("No tags file found for %s, field cleared", self.current_image_path.name)

        cursor = self.tag_input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.tag_input.setTextCursor(cursor)

    def save_tags(self) -> None:
        if not self.current_image_path:
            self.show_status("No image loaded to save tags for", 3000)
            return
        tags = self.tag_input.toPlainText().strip()
        txt_path = self.current_image_path.with_suffix(".txt")
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(tags)
            logger.info("Tags saved to %s", txt_path)
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
        """Показать диалог об отсутствующей базе данных тегов."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("База данных тегов не найдена")
        
        text = (
            "Файл derpibooru.csv не найден!\n\n"
            "Автодополнение тегов будет недоступно.\n\n"
            "Чтобы включить автодополнение:\n"
            "1. Скачайте файл derpibooru.csv\n"
            "2. Поместите его в папку с программой\n"
            "3. Перезапустите приложение"
        )
        msg.setText(text)
        
        # Создаем кнопки
        download_btn = msg.addButton("Скачать базу данных", QMessageBox.ButtonRole.ActionRole)
        ok_btn = msg.addButton("Продолжить без автодополнения", QMessageBox.ButtonRole.AcceptRole)
        
        msg.exec()
        
        # Обработка нажатия кнопки
        if msg.clickedButton() == download_btn:
            self._open_database_download_link()

    def _show_database_error_dialog(self, error: str) -> None:
        """Показать диалог об ошибке загрузки базы данных."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Ошибка загрузки базы данных")
        
        text = (
            f"Ошибка при загрузке файла derpibooru.csv:\n\n{error}\n\n"
            "Возможные причины:\n"
            "• Поврежденный файл\n"
            "• Неправильный формат\n"
            "• Недостаточно памяти\n\n"
            "Автодополнение будет недоступно."
        )
        msg.setText(text)
        msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msg.exec()

    def _open_database_download_link(self) -> None:
        """Открыть ссылку для скачивания базы данных."""
        import webbrowser
        url = "https://github.com/DominikDoom/a1111-sd-webui-tagcomplete/tree/main/tags"
        try:
            webbrowser.open(url)
            self.show_status("Открыта ссылка для скачивания базы данных", 3000)
        except Exception as e:
            logger.exception("Failed to open browser: %s", e)
            # Показываем диалог с ссылкой для копирования
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Ссылка для скачивания")
            msg.setText(f"Скопируйте ссылку в браузер:\n\n{url}")
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
        return super().resizeEvent(event)


# --------------------------- Точка входа -----------------------------------

def main() -> None:
    logger.info("Starting TagAutoCompleteApp")
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = TagAutoCompleteApp()
        window.show()
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
