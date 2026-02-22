#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Система макросов для Image Tag Editor - профессиональное управление макросами.

Этот модуль предоставляет комплексную систему макросов для приложения Image Tag Editor,
позволяя пользователям создавать, управлять и выполнять предопределённые наборы тегов
одним кликом.

Ключевые возможности:
- Современный UI с тёмной темой соответствующий дизайну приложения
- Раскрывающееся меню интегрированное с основным UI
- JSON-хранилище макросов с автосохранением
- Импорт/экспорт коллекций макросов
- Умная вставка тегов с отслеживанием использования

Технические детали:
- JSON-сохранение в файле macros.json
- Современные компоненты на базе PyQt6
- Событийная архитектура для бесшовной интеграции
- Комплексная обработка ошибок и логирование

Требования:
- PyQt6
- Python 3.8+

Лицензия:
    MIT License - подробности в файле LICENSE.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import functools
import time
from typing import Callable, TypeVar

# Импортируем DEBUG_MODE из main
try:
    from main import DEBUG_MODE, DetailedLogger, log_user_action, safe_execute
    MAIN_LOGGER_AVAILABLE = True
except ImportError:
    # Fallback если main недоступен
    DEBUG_MODE = True
    MAIN_LOGGER_AVAILABLE = False

from PyQt6.QtCore import (
    Qt, QObject, pyqtSignal, QTimer, QSize
)
from PyQt6.QtGui import (
    QIcon, QFont, QPalette, QColor, QPixmap, QPainter
)
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox, QSplitter,
    QSizePolicy, QApplication, QMenu, QToolButton, QFileDialog, QSpacerItem, QDialogButtonBox
)

# --------------------------- Константы и конфигурация -------------------------------------

MACRO_DB_FILE = Path("macros.json")
MAX_RECENT_MACROS = 10
MACRO_ICON_SIZE = QSize(24, 24)

# Цвета и размеры подобраны по изображению
ACCENT_PURPLE = "#6f49a6"        # выбранный элемент списка и акцентные кнопки
BG_DIALOG = "#1d1e1f"            # основной фон диалога (чуть темнее)
PANEL_BG = "#222324"             # фон групп/панелей
FIELD_BG = "#2a2a2b"             # фон полей ввода (светлее основного фона)
BORDER = "#2f2f30"               # контуры
TEXT = "#e6e6e6"                 # основной текст
SUBTEXT = "#bdbdbd"              # вторичный текст
DISABLED_BG = "#2a2a2b"          # фон отключённых кнопок

# Цвет ручной иконки вопроса (пример как на референсе)
QUESTION_BLUE = "#2176FF"

# Стиль с уменьшенной высотой кнопок и темными диалогами
# Добавлены исправления: QLabel фон сделан прозрачным, чтобы не было "темных подложек" за текстом
# Теперь стили для кнопок в QMessageBox зависят от objectName (DangerButton / PrimaryButton)
MACRO_STYLESHEET = f"""
/* Global dark theme for all windows and dialogs */
* {{ font-family: 'Segoe UI', 'Tahoma', 'Verdana', sans-serif; color: {TEXT}; }}

QDialog {{ 
    background-color: {BG_DIALOG}; 
    color: {TEXT}; 
}}

QMainWindow {{ 
    background-color: {BG_DIALOG}; 
    color: {TEXT}; 
}}

QWidget {{ 
    background-color: {BG_DIALOG}; 
    color: {TEXT}; 
}}

QDialog#MacroManagerDialog {{ background-color: {BG_DIALOG}; }}

/* Ensure labels have transparent background to avoid darker boxes on lighter areas */
QLabel {{
    background: transparent;
    color: {TEXT};
}}

/* Dark theme for menus */
QMenu {{ 
    background-color: {PANEL_BG}; 
    color: {TEXT}; 
    border: 1px solid {BORDER}; 
    border-radius: 6px; 
}}

QMenu::item {{ 
    padding: 6px 12px; 
    border-radius: 4px; 
}}

QMenu::item:selected {{ 
    background-color: {ACCENT_PURPLE}; 
    color: white; 
}}

QMenu::separator {{ 
    height: 1px; 
    background-color: {BORDER}; 
    margin: 2px 0px; 
}}

/* Dark theme for toolbuttons */
QToolButton {{ 
    background-color: {PANEL_BG}; 
    color: {TEXT}; 
    border: 1px solid {BORDER}; 
    border-radius: 6px; 
    padding: 6px; 
}}

QToolButton:hover {{ 
    background-color: #2f2f2f; 
}}

QToolButton:pressed {{ 
    background-color: #202020; 
}}

/* Dark theme for file dialogs */
QFileDialog {{ 
    background-color: {BG_DIALOG}; 
    color: {TEXT}; 
}}

QFileDialog QLabel {{ 
    color: {TEXT}; 
}}

QFileDialog QLineEdit {{ 
    background-color: {FIELD_BG}; 
    color: {TEXT}; 
    border: 1px solid {BORDER}; 
    border-radius: 4px; 
    padding: 4px; 
}}

/* Top search field */
QLineEdit#TopSearch {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {SUBTEXT};
    min-height: 24px;
}}
QLineEdit#TopSearch:focus {{ color: {TEXT}; }}

/* Group boxes */
QGroupBox {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 8px;
    padding: 10px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 6px; color: {TEXT}; font-weight: 600; }}

/* Macro list */
QListWidget#MacroList {{
    background-color: #141414;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px;
    min-width: 260px;
}}
QListWidget#MacroList::item {{
    padding: 12px 10px;
    margin: 6px 4px;
    border-radius: 6px;
}}
QListWidget#MacroList::item:selected {{
    background-color: {ACCENT_PURPLE};
    color: #ffffff;
}}
QListWidget#MacroList::item:hover {{ background-color: #333234; }}

/* Input fields */
QLineEdit#DetailInput {{
    background-color: {FIELD_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px;
    color: {SUBTEXT};
    min-height: 24px;
}}
QLineEdit#DetailInput:focus {{ color: {TEXT}; border: 1px solid {ACCENT_PURPLE}; }}

QTextEdit#MacroContentEditor {{
    background-color: {FIELD_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: 'Consolas', 'Courier New', monospace;
    color: {SUBTEXT};
}}

/* Buttons - uniform with reduced height */
QPushButton {{
    background-color: #262626;
    color: {TEXT};
    border: 1px solid #2e2e2e;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 24px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: #2f2f2f; }}
QPushButton:pressed {{ background-color: #202020; }}

QPushButton#PrimaryButton {{ background-color: {ACCENT_PURPLE}; color: white; }}
QPushButton#DangerButton {{ background-color: #c43b3b; color: white; }}
QPushButton:disabled {{ background-color: {DISABLED_BG}; color: #7f7f7f; }}

/* Small secondary top buttons (Import/Export) */
QPushButton#TopAction {{ 
    min-width: 86px; 
    min-height: 24px;
    border-radius: 6px; 
    background-color: #2a2a2b; 
    color: {TEXT}; 
}}

/* Floating Save button inside details */
QWidget#SaveContainer {{ background: transparent; }}

QSplitter::handle {{ background-color: #2b2b2b; width: 6px; }}

/* Dark themed message boxes */
QMessageBox {{
    background-color: {BG_DIALOG};
    color: {TEXT};
    border: 2px solid #3a3a3a;
    border-radius: 8px;
}}
QMessageBox QLabel {{
    color: {TEXT};
    padding: 10px;
    font-size: 12pt;
}}

/* Message box button layout - buttons aligned to right with spacing */
QMessageBox .QDialogButtonBox {{
    spacing: 14px;
    margin: 14px;
}}

QMessageBox QPushButton {{
    background-color: #262626;
    color: {TEXT};
    border: 1px solid #2e2e2e;
    border-radius: 8px;
    padding: 10px 18px;
    min-height: 38px;
    min-width: 110px;
    font-weight: 700;
    margin: 0px 5px;
}}
QMessageBox QPushButton:hover {{
    background-color: #2f2f2f;
}}
QMessageBox QPushButton:pressed {{
    background-color: #202020;
}}

/* Danger/Primary buttons in message boxes by objectName (works for any localization) */
QMessageBox QPushButton#DangerButton {{
    background-color: #c43b3b;
    color: white;
    border: 1px solid #d64545;
    min-width: 140px;
}}
QMessageBox QPushButton#DangerButton:hover {{
    background-color: #d64545;
}}
QMessageBox QPushButton#DangerButton:pressed {{
    background-color: #b33030;
}}

QMessageBox QPushButton#PrimaryButton {{
    background-color: #3a3a3a;
    color: {TEXT};
    border: 1px solid #4a4a4a;
    min-width: 110px;
}}
QMessageBox QPushButton#PrimaryButton:hover {{
    background-color: #4a4a4a;
}}
QMessageBox QPushButton#PrimaryButton:pressed {{
    background-color: #343434;
}}
"""

# Создаем логгер для системы макросов
if MAIN_LOGGER_AVAILABLE:
    # Используем централизованную систему логирования из main.py
    logger = DetailedLogger("MacroSystem", DEBUG_MODE)
else:
    # Fallback на стандартное логирование
    logger = logging.getLogger("MacroSystem")
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

# --------------------------- Применение тёмной темы -------------------------------------

def apply_dark_theme(app: QApplication) -> None:
    """Применить комплексную тёмную тему ко всему приложению, включая заголовки окон."""
    # Устанавливаем тёмную палитру для всего приложения
    dark_palette = QPalette()

    # Цвета окон
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(BG_DIALOG))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))

    # Базовые цвета (фон для текстовых полей, списков и т.д.)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(FIELD_BG))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(PANEL_BG))

    # Цвета текста
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))

    # Цвета кнопок
    dark_palette.setColor(QPalette.ColorRole.Button, QColor("#262626"))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))

    # Цвета выделения
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_PURPLE))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

    # Цвета отключённых элементов
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#7f7f7f"))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#7f7f7f"))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#7f7f7f"))

    # Цвета ссылок
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(ACCENT_PURPLE))
    dark_palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#8e5ca6"))

    # Цвета подсказок
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(PANEL_BG))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))

    app.setPalette(dark_palette)
    app.setStyleSheet(MACRO_STYLESHEET)

    logger.info("Applied comprehensive dark theme to application")

# --------------------------- Модели данных -------------------------------------

@dataclass
class Macro:
    name: str
    tags: str
    description: str = ""
    created_date: str = ""
    last_used: str = ""
    use_count: int = 0
    hotkey: str = ""
    category: str = "General"

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

    def get_tag_list(self) -> List[str]:
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def set_tag_list(self, tag_list: List[str]) -> None:
        self.tags = ', '.join(tag_list)

    def increment_usage(self) -> None:
        self.use_count += 1
        self.last_used = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Macro':
        return cls(**data)

# --------------------------- MacroManager -------------------------------------

class MacroManager(QObject):
    macros_changed = pyqtSignal()
    macro_executed = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.macros: Dict[str, Macro] = {}
        self.db_file = MACRO_DB_FILE
        self.auto_save = True
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_macros)
        self.save_timer.setInterval(2000)
        self._load_macros()

    # (все методы менеджера остаются как в вашем исходнике)
    def create_macro(self, name: str, tags: str, description: str = "") -> bool:
        if name in self.macros:
            logger.warning("Macro with name '%s' already exists", name)
            return False
        macro = Macro(name=name, tags=tags, description=description)
        self.macros[name] = macro
        self._schedule_save()
        self.macros_changed.emit()
        logger.info("Created macro '%s' with tags: %s", name, tags)
        return True

    def update_macro(self, old_name: str, new_name: str, tags: str, description: str = "") -> bool:
        if old_name not in self.macros:
            logger.error("Macro '%s' not found for update", old_name)
            return False
        if new_name != old_name and new_name in self.macros:
            logger.warning("Cannot rename macro to existing name '%s'", new_name)
            return False
        macro = self.macros[old_name]
        macro.tags = tags
        macro.description = description
        if new_name != old_name:
            macro.name = new_name
            del self.macros[old_name]
            self.macros[new_name] = macro
        self._schedule_save()
        self.macros_changed.emit()
        logger.info("Updated macro '%s' -> '%s'", old_name, new_name)
        return True

    def delete_macro(self, name: str) -> bool:
        if name not in self.macros:
            logger.error("Macro '%s' not found for deletion", name)
            return False
        del self.macros[name]
        self._schedule_save()
        self.macros_changed.emit()
        logger.info("Deleted macro '%s'", name)
        return True

    def get_macro(self, name: str) -> Optional[Macro]:
        return self.macros.get(name)

    def get_all_macros(self) -> List[Macro]:
        return sorted(self.macros.values(), key=lambda m: m.name.lower())

    def get_recent_macros(self, limit: int = MAX_RECENT_MACROS) -> List[Macro]:
        macros_with_usage = [m for m in self.macros.values() if m.last_used]
        return sorted(macros_with_usage, key=lambda m: m.last_used, reverse=True)[:limit]

    def execute_macro(self, name: str) -> Optional[str]:
        macro = self.macros.get(name)
        if not macro:
            logger.error("Macro '%s' not found for execution", name)
            return None
        macro.increment_usage()
        self._schedule_save()
        logger.info("Executed macro '%s': %s", name, macro.tags)
        self.macro_executed.emit(name, macro.tags)
        return macro.tags

    def import_macros(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            imported_count = 0
            overwritten_count = 0
            for macro_data in data.get('macros', []):
                try:
                    macro = Macro.from_dict(macro_data)
                    # Import priority: imported macros overwrite existing ones
                    if macro.name in self.macros:
                        logger.info("Overwriting existing macro '%s' with imported data", macro.name)
                        overwritten_count += 1
                    else:
                        imported_count += 1
                    # Always import/overwrite the macro (imported data has priority)
                    self.macros[macro.name] = macro
                except Exception as e:
                    logger.warning("Failed to import macro: %s", e)
                    continue
            
            total_processed = imported_count + overwritten_count
            if total_processed > 0:
                self._schedule_save()
                self.macros_changed.emit()
                if overwritten_count > 0:
                    logger.info("Imported %d new macros and overwrote %d existing macros from %s", 
                              imported_count, overwritten_count, file_path)
                else:
                    logger.info("Imported %d macros from %s", imported_count, file_path)
            return total_processed > 0
        except Exception as e:
            logger.exception("Failed to import macros: %s", e)
            return False

    def export_macros(self, file_path: Path) -> bool:
        try:
            data = { 'version': '1.0', 'export_date': datetime.now().isoformat(), 'macros': [macro.to_dict() for macro in self.macros.values()] }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Exported %d macros to %s", len(self.macros), file_path)
            return True
        except Exception as e:
            logger.exception("Failed to export macros: %s", e)
            return False

    def _load_macros(self) -> None:
        if not self.db_file.exists():
            self._create_default_macros()
            return
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.macros.clear()
            for macro_data in data.get('macros', []):
                try:
                    macro = Macro.from_dict(macro_data)
                    self.macros[macro.name] = macro
                except Exception as e:
                    logger.warning("Failed to load macro: %s", e)
                    continue
            logger.info("Loaded %d macros from %s", len(self.macros), self.db_file)
        except Exception as e:
            logger.exception("Failed to load macros: %s", e)
            self._create_default_macros()

    def _create_default_macros(self) -> None:
        default_macros = [
            { 'name': 'BJ1', 'tags': 'unicorn oc, pony, unicorn, solo, mare oc, female oc, mare, female, oc, oc only, prosthetic leg', 'description': 'Unicorn OC with prosthetic leg - female mare character set' },
            { 'name': 'Rainbow', 'tags': 'rd, safe, cute', 'description': 'Rainbow Dash related tags' },
            { 'name': 'Basic OC', 'tags': 'oc, oc only, solo, pony', 'description': 'Basic original character tags' }
        ]
        for macro_data in default_macros:
            macro = Macro(name=macro_data['name'], tags=macro_data['tags'], description=macro_data['description'])
            self.macros[macro.name] = macro
        self._schedule_save()
        logger.info("Created %d default macros", len(default_macros))

    def _save_macros(self) -> None:
        if not self.auto_save:
            return
        try:
            data = { 'version': '1.0', 'last_saved': datetime.now().isoformat(), 'macros': [m.to_dict() for m in self.macros.values()] }
            if self.db_file.exists():
                backup_file = self.db_file.with_suffix('.json.bak')
                try:
                    backup_file.write_bytes(self.db_file.read_bytes())
                except Exception:
                    pass
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _schedule_save(self) -> None:
        if self.auto_save:
            self.save_timer.start()

# --------------------------- UI компоненты -------------------------------------

# Вспомогательные функции для стандартизированных диалоговых окон

def _create_question_icon(size: int = 72) -> QPixmap:
    """Создать круглую синюю иконку с вопросительным знаком похожую на референсное изображение."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Draw blue circle
    p.setBrush(QColor(QUESTION_BLUE))
    p.setPen(Qt.PenStyle.NoPen)
    radius = size // 2
    p.drawEllipse(0, 0, size, size)
    # Draw question mark
    font = QFont('Segoe UI', max(10, size // 2))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor('#ffffff'))
    # center the question mark
    rect = pix.rect()
    p.drawText(rect, Qt.AlignmentFlag.AlignCenter, '?')
    p.end()
    return pix


def _standard_question(parent, title: str, text: str, default_is_yes: bool = True) -> QMessageBox.StandardButton:
    """Показать диалог вопроса оформленный точно как на референсе.

    - Использует пользовательскую синюю круглую иконку с вопросительным знаком.
    - Гарантирует что кнопки 'Yes' (слева) и 'No' (справа) размещены справа от диалога,
      с 'No' оформленной как заметная опасность (красная) и большей ширины.
    - Работает корректно независимо от локализации.
    
    Возвращает: QMessageBox.StandardButton.Yes или .No
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.NoIcon)  # Используем пользовательскую иконку
    msg.setWindowTitle(title)
    msg.setText(text)
    # Рисуем и устанавливаем пользовательскую иконку
    pix = _create_question_icon(76)
    msg.setIconPixmap(pix)

    # Убеждаемся что текст сообщения выглядит как на референсе
    msg.setStyleSheet(MACRO_STYLESHEET)

    # Создаём кнопки явно чтобы контролировать размеры и objectNames
    yes = msg.addButton(QMessageBox.StandardButton.Yes)
    no = msg.addButton(QMessageBox.StandardButton.No)

    # Назначаем object names для стилизации
    if yes is not None:
        yes.setObjectName('PrimaryButton')
        yes.setMinimumHeight(38)
        yes.setMinimumWidth(120)
        yes.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
    if no is not None:
        no.setObjectName('DangerButton')
        no.setMinimumHeight(38)
        no.setMinimumWidth(160)
        no.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))

    # Устанавливаем кнопку по умолчанию
    if default_is_yes:
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
    else:
        msg.setDefaultButton(QMessageBox.StandardButton.No)

    # Выполняем модальный диалог.
    # Не можем полностью контролировать цвет нативного заголовка (контролируется ОС).
    # Клиентская область диалога соответствует таблице стилей.
    msg.exec()
    clicked = msg.clickedButton()
    if clicked == yes:
        return QMessageBox.StandardButton.Yes
    return QMessageBox.StandardButton.No


def _standard_info(parent, title: str, text: str) -> None:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    ok_btn = msg.button(QMessageBox.StandardButton.Ok)
    if ok_btn is not None:
        ok_btn.setObjectName('PrimaryButton')
    msg.exec()


def _standard_warn(parent, title: str, text: str) -> None:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    ok_btn = msg.button(QMessageBox.StandardButton.Ok)
    if ok_btn is not None:
        ok_btn.setObjectName('PrimaryButton')
    msg.exec()


class MacroDropdown(QWidget):
    macro_selected = pyqtSignal(str, str)

    def __init__(self, macro_manager: MacroManager, parent=None):
        super().__init__(parent)
        self.macro_manager = macro_manager
        self.setObjectName("MacroDropdown")
        self._create_ui()
        self._setup_connections()
        self._update_menu()
        self.setStyleSheet(MACRO_STYLESHEET)

    def _create_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.dropdown_button = QToolButton(self)
        self.dropdown_button.setObjectName("MacroDropdownButton")
        self.dropdown_button.setText("⚡")
        self.dropdown_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu = QMenu(self)
        self.dropdown_button.setMenu(self.menu)
        layout.addWidget(self.dropdown_button)

    def _setup_connections(self) -> None:
        self.macro_manager.macros_changed.connect(self._update_menu)

    def _update_menu(self) -> None:
        self.menu.clear()
        all_macros = self.macro_manager.get_all_macros()
        recent_macros = self.macro_manager.get_recent_macros(5)
        if not all_macros:
            action = self.menu.addAction("No macros available")
            action.setEnabled(False)
            self.menu.addSeparator()
        else:
            if recent_macros:
                heading = self.menu.addAction("Recent")
                heading.setEnabled(False)
                for macro in recent_macros[:3]:
                    a = self.menu.addAction(macro.name)
                    a.setToolTip(macro.tags)
                    a.triggered.connect(lambda checked=False, n=macro.name: self._execute_macro(n))
                self.menu.addSeparator()
            visible_count = 8
            for macro in all_macros[:visible_count]:
                a = self.menu.addAction(macro.name)
                a.setToolTip(macro.tags)
                a.triggered.connect(lambda checked=False, n=macro.name: self._execute_macro(n))
            if len(all_macros) > visible_count:
                more = self.menu.addMenu("More...")
                for macro in all_macros[visible_count:]:
                    a = more.addAction(macro.name)
                    a.triggered.connect(lambda checked=False, n=macro.name: self._execute_macro(n))
            self.menu.addSeparator()
        manage = self.menu.addAction("Manage Macros...")
        manage.triggered.connect(self._open_macro_manager)

    def _execute_macro(self, macro_name: str) -> None:
        tags = self.macro_manager.execute_macro(macro_name)
        if tags:
            self.macro_selected.emit(macro_name, tags)

    def _open_macro_manager(self) -> None:
        dialog = MacroManagerDialog(self.macro_manager, self)
        dialog.exec()


class MacroManagerDialog(QDialog):
    def __init__(self, macro_manager: MacroManager, parent=None):
        super().__init__(parent)
        self.macro_manager = macro_manager
        self.current_macro = None
        # Флаг, отображающий наличие несохранённых изменений по сравнению с оригиналом
        self.unsaved_changes = False
        # Store original values to detect actual changes
        self._original_name = ""
        self._original_description = ""
        self._original_tags = ""
        # Флаг, чтобы временно подавлять обработку сигналов изменений (при программном заполнении полей)
        self._suppress_change_signals = False
        # Флаг для отслеживания операций сохранения
        self._saving_in_progress = False
        
        self.setObjectName("MacroManagerDialog")
        self.setWindowTitle("Macro Manager")
        self.resize(980, 680)
        self.setFont(QFont('Segoe UI', 10))
        self.setStyleSheet(MACRO_STYLESHEET)
        
        # Set window icon if available
        try:
            icon_path = Path("icon.ico")
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                self.setWindowIcon(icon)
        except Exception:
            pass  # Ignore icon errors
        
        self._create_ui()
        self._setup_connections()
        self._refresh_macro_list()

    def _make_button(self, text: str, obj_name: str = 'MacroButton', minimum_width: int = 96) -> QPushButton:
        """Create a button with consistent styling and reduced height."""
        btn = QPushButton(text)
        btn.setObjectName(obj_name)
        btn.setMinimumHeight(24)  # Reduced from 36px to 24px (1/3 reduction)
        btn.setMinimumWidth(minimum_width)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return btn

    def _create_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Top row: search on left, Import/Export on right (as in mock)
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setObjectName('TopSearch')
        self.search_input.setPlaceholderText('Search macros...')
        top_row.addWidget(self.search_input, 1)
        # Right actions
        top_actions = QHBoxLayout()
        self.top_import = QPushButton('Import')
        self.top_import.setObjectName('TopAction')
        self.top_export = QPushButton('Export')
        self.top_export.setObjectName('TopAction')
        top_actions.addWidget(self.top_import)
        top_actions.addWidget(self.top_export)
        top_row.addLayout(top_actions)
        main_layout.addLayout(top_row)

        # Content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # LEFT PANEL
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        list_group = QGroupBox('Macros')
        list_group_layout = QVBoxLayout(list_group)
        list_group_layout.setContentsMargins(8, 8, 8, 8)

        self.macro_list = QListWidget()
        self.macro_list.setObjectName('MacroList')
        self.macro_list.setUniformItemSizes(True)
        # Make the macro list expand to fill available height
        self.macro_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        list_group_layout.addWidget(self.macro_list)
        # ensure the list inside the group expands and occupies most space
        list_group_layout.setStretch(list_group_layout.indexOf(self.macro_list), 1)

        # Bottom controls inside left panel (Duplicate, New, Delete)
        ctrl_bar = QHBoxLayout()
        self.duplicate_btn = self._make_button('Duplicate', 'MacroButton', 100)
        self.new_btn = self._make_button('New', 'MacroButton', 100)
        self.delete_btn = self._make_button('Delete', 'DangerButton', 100)
        ctrl_bar.addWidget(self.duplicate_btn)
        ctrl_bar.addWidget(self.new_btn)
        ctrl_bar.addWidget(self.delete_btn)
        ctrl_bar.addStretch()
        list_group_layout.addLayout(ctrl_bar)

        # Let list_group expand in the left layout
        list_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(list_group)
        # Make left_layout give all remaining vertical space to list_group
        left_layout.setStretch(left_layout.indexOf(list_group), 1)

        stats_group = QGroupBox('')
        stats_layout = QHBoxLayout(stats_group)
        self.stats_label = QLabel('')
        self.stats_label.setStyleSheet('color: #bfbfbf;')
        stats_layout.addWidget(self.stats_label)
        stats_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(stats_group)

        splitter.addWidget(left_panel)

        # RIGHT PANEL
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        details_group = QGroupBox('Macro Details')
        details_layout = QGridLayout(details_group)
        details_layout.setHorizontalSpacing(12)
        details_layout.setVerticalSpacing(8)
        details_layout.setColumnStretch(1, 1)

        lbl_name = QLabel('Name:')
        self.name_input = QLineEdit()
        self.name_input.setObjectName('DetailInput')
        self.name_input.setPlaceholderText('Enter macro name...')
        details_layout.addWidget(lbl_name, 0, 0)
        details_layout.addWidget(self.name_input, 0, 1)

        lbl_desc = QLabel('Description:')
        self.description_input = QLineEdit()
        self.description_input.setObjectName('DetailInput')
        self.description_input.setPlaceholderText('Optional description...')
        details_layout.addWidget(lbl_desc, 1, 0)
        details_layout.addWidget(self.description_input, 1, 1)

        lbl_tags = QLabel('Tags:')
        self.tags_editor = QTextEdit()
        self.tags_editor.setObjectName('MacroContentEditor')
        self.tags_editor.setPlaceholderText('tag1, tag2, tag3')
        # allow tags editor to expand vertically within right panel
        self.tags_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        details_layout.addWidget(lbl_tags, 2, 0, Qt.AlignmentFlag.AlignTop)
        details_layout.addWidget(self.tags_editor, 2, 1)
        details_layout.setRowStretch(2, 1)

        # Save button aligned to bottom-right inside details group (floating style)
        save_container = QWidget()
        save_container.setObjectName('SaveContainer')
        save_layout = QHBoxLayout(save_container)
        save_layout.setContentsMargins(0, 6, 0, 0)
        save_layout.addStretch()
        self.save_btn = QPushButton('Save')
        self.save_btn.setObjectName('PrimaryButton')
        self.save_btn.setMinimumWidth(120)
        save_layout.addWidget(self.save_btn)
        details_layout.addWidget(save_container, 3, 0, 1, 2)

        right_layout.addWidget(details_group)
        right_layout.setStretch(right_layout.indexOf(details_group), 1)

        info_group = QGroupBox('Macro Information')
        info_layout = QVBoxLayout(info_group)
        self.info_label = QLabel('Select a macro to view details')
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        info_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        right_layout.addWidget(info_group)

        splitter.addWidget(right_panel)

        # Set splitter proportions to match the mock (left narrower, right wider)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    def _setup_connections(self) -> None:
        """Set up signal connections for UI interactions."""
        # Basic actions
        self.top_import.clicked.connect(self._import_macros)
        self.top_export.clicked.connect(self._export_macros)
        self.duplicate_btn.clicked.connect(self._duplicate_macro)
        self.new_btn.clicked.connect(self._new_macro)
        self.delete_btn.clicked.connect(self._delete_macro)
        self.save_btn.clicked.connect(self._save_macro)

        # Editor changes - track actual changes to content
        self.name_input.textChanged.connect(self._on_editor_changed)
        self.description_input.textChanged.connect(self._on_editor_changed)
        self.tags_editor.textChanged.connect(self._on_editor_changed)

        # List interactions
        self.macro_list.currentItemChanged.connect(self._on_macro_selected)
        self.search_input.textChanged.connect(self._on_search)

        # Update from manager
        self.macro_manager.macros_changed.connect(self._refresh_macro_list)

    # ----------------- Логика методов -------------------------------------

    def _refresh_macro_list(self) -> None:
        self.macro_list.clear()
        macros = self.macro_manager.get_all_macros()
        for macro in macros:
            item = QListWidgetItem(macro.name)
            item.setData(Qt.ItemDataRole.UserRole, macro.name)
            item.setToolTip(f"Tags: {macro.tags} Used: {macro.use_count} times")
            self.macro_list.addItem(item)
        self.stats_label.setText(f"{len(macros)} macros")
        # If current macro was removed, clear editor
        if self.current_macro and self.current_macro not in [m.name for m in macros]:
            self._clear_editor()

    def _on_search(self, text: str) -> None:
        q = text.strip().lower()
        for i in range(self.macro_list.count()):
            item = self.macro_list.item(i)
            item.setHidden(bool(q) and q not in item.text().lower())

    def _on_macro_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        # Don't prompt for unsaved changes if signals are suppressed OR if we're in the middle of a save operation
        if not self._suppress_change_signals and not self._saving_in_progress:
            # Prompt only if there are actual unsaved changes compared to the original loaded values
            if self._has_actual_changes():
                choice = self._ask_save_changes()
                if choice == QMessageBox.StandardButton.Yes:
                    # save current changes before switching
                    self._save_macro()
                elif choice == QMessageBox.StandardButton.No:
                    # User chose not to save changes - clear the unsaved state
                    # This ensures clean loading of the new macro
                    self.unsaved_changes = False
                    self.current_macro = None  # Clear current macro to ensure clean load
        
        # Only load macro if signals are not suppressed (to avoid reloading during Cancel operations)
        if not self._suppress_change_signals:
            if current:
                try:
                    name = current.data(Qt.ItemDataRole.UserRole)
                    if name:
                        self._load_macro(name)
                    else:
                        self._clear_editor()
                except RuntimeError:
                    # Handle case where QListWidgetItem has been deleted
                    self._clear_editor()
            else:
                self._clear_editor()

    def _load_macro(self, macro_name: str) -> None:
        """Load a macro into the editor and store original values."""
        macro = self.macro_manager.get_macro(macro_name)
        if not macro:
            return
        self.current_macro = macro_name
        # When filling fields programmatically, suppress change signals to avoid false positives
        self._suppress_change_signals = True
        try:
            # Set values in UI
            self.name_input.setText(macro.name)
            self.description_input.setText(macro.description)
            self.tags_editor.setPlainText(macro.tags)

            # Store original values for change detection
            self._original_name = macro.name
            self._original_description = macro.description
            self._original_tags = macro.tags

            # Clear unsaved flag - we just loaded from saved data
            self.unsaved_changes = False
        finally:
            self._suppress_change_signals = False

        # Update info display
        info_text = f"Created: {self._format_date(macro.created_date)}\n"
        if macro.last_used:
            info_text += f"Last used: {self._format_date(macro.last_used)}\n"
        info_text += f"Times used: {macro.use_count}\n"
        info_text += f"Tag count: {len(macro.get_tag_list())}"
        self.info_label.setText(info_text)
        self._update_button_states()

    def _clear_editor(self) -> None:
        """Clear the editor and reset state."""
        self.current_macro = None
        # Suppress signals while clearing
        self._suppress_change_signals = True
        try:
            # Clear UI fields
            self.name_input.clear()
            self.description_input.clear()
            self.tags_editor.clear()

            # Clear original values
            self._original_name = ""
            self._original_description = ""
            self._original_tags = ""

            self.unsaved_changes = False
        finally:
            self._suppress_change_signals = False

        self.info_label.setText('Select a macro to view details')
        self._update_button_states()

    def _has_actual_changes(self) -> bool:
        """Check if there are actual changes compared to original values."""
        # Only consider changes if there is a loaded macro
        if self.current_macro is None:
            return False

        current_name = self.name_input.text().strip()
        current_description = self.description_input.text().strip()
        current_tags = self.tags_editor.toPlainText().strip()

        # Check if any field has changed
        return (
            current_name != self._original_name or
            current_description != self._original_description or
            current_tags != self._original_tags
        )

    def _on_editor_changed(self) -> None:
        """Handle editor content changes - only mark as changed if there are actual differences.

        Important: ignore signals that were triggered while programmatically setting field values.
        """
        if self._suppress_change_signals:
            return
        if self.current_macro is not None:
            self.unsaved_changes = self._has_actual_changes()
        else:
            # If no macro is loaded, treat fields as not tracked (no unsaved changes to prompt on selection/close)
            self.unsaved_changes = False
        self._update_button_states()

    def _update_button_states(self) -> None:
        has_selection = self.macro_list.currentItem() is not None
        has_changes = self.unsaved_changes
        has_macro = self.current_macro is not None
        
        # Check if there are any changes in any field for Save button
        has_any_changes = False
        if self.current_macro is not None:
            current_name = self.name_input.text().strip()
            current_description = self.description_input.text().strip()
            current_tags = self.tags_editor.toPlainText().strip()
            
            has_any_changes = (
                current_name != self._original_name or
                current_description != self._original_description or
                current_tags != self._original_tags
            )
        
        self.duplicate_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.save_btn.setEnabled(has_any_changes and bool(self.name_input.text().strip()))

    def _new_macro(self) -> None:
        if self._has_actual_changes():
            r = self._ask_save_changes()
            if r == QMessageBox.StandardButton.Yes:
                self._save_macro()
        base = 'New Macro'
        i = 1
        name = base
        while self.macro_manager.get_macro(name):
            name = f"{base} {i}"
            i += 1
        if self.macro_manager.create_macro(name, ''):
            # select newly created
            self._refresh_macro_list()
            for idx in range(self.macro_list.count()):
                it = self.macro_list.item(idx)
                if it.data(Qt.ItemDataRole.UserRole) == name:
                    # Set current item programmatically (no prompt because we use _suppress_change_signals when loading)
                    self.macro_list.setCurrentItem(it)
                    break

    def _duplicate_macro(self) -> None:
        cur = self.current_macro
        if not cur:
            return
        macro = self.macro_manager.get_macro(cur)
        if not macro:
            return
        base = f"{macro.name} Copy"
        i = 1
        name = base
        while self.macro_manager.get_macro(name):
            name = f"{base} {i}"
            i += 1
        if self.macro_manager.create_macro(name, macro.tags, macro.description):
            self._refresh_macro_list()
            for idx in range(self.macro_list.count()):
                it = self.macro_list.item(idx)
                if it.data(Qt.ItemDataRole.UserRole) == name:
                    self.macro_list.setCurrentItem(it)
                    break

    def _delete_macro(self) -> None:
        if not self.current_macro:
            return
        rep = QMessageBox.question(self, 'Delete Macro', f"Are you sure you want to delete '{self.current_macro}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            self.macro_manager.delete_macro(self.current_macro)
            self._refresh_macro_list()
            self._clear_editor()

    def _save_macro(self) -> None:
        if not self.current_macro:
            return
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, 'Invalid Name', 'Macro name cannot be empty.')
            return
        desc = self.description_input.text().strip()
        tags = self.tags_editor.toPlainText().strip()
        
        # Set saving in progress flag to prevent unsaved changes prompts during save operation
        self._saving_in_progress = True
        self._suppress_change_signals = True
        try:
            # Attempt to save/rename
            if self.macro_manager.update_macro(self.current_macro, name, tags, desc):
                # Update current macro name and originals so that subsequent selection/close won't prompt
                self.current_macro = name
                self._original_name = name
                self._original_description = desc
                self._original_tags = tags
                self.unsaved_changes = False
                self._refresh_macro_list()
                # select updated
                for idx in range(self.macro_list.count()):
                    it = self.macro_list.item(idx)
                    if it.data(Qt.ItemDataRole.UserRole) == name:
                        # programmatically set without prompting: signals are suppressed
                        self.macro_list.setCurrentItem(it)
                        break
            else:
                QMessageBox.warning(self, 'Save Failed', 'Failed to save macro. The name might already exist.')
        finally:
            self._suppress_change_signals = False
            self._saving_in_progress = False

    def _import_macros(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, 'Import Macros', '', 'JSON Files (*.json);;All Files (*)')
        if file_path:
            ok = self.macro_manager.import_macros(Path(file_path))
            if ok:
                QMessageBox.information(self, 'Import Success', 'Macros imported successfully.')
                self._refresh_macro_list()
            else:
                QMessageBox.warning(self, 'Import Failed', 'Failed to import macros. Check the file format.')

    def _export_macros(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, 'Export Macros', 'macros_export.json', 'JSON Files (*.json);;All Files (*)')
        if file_path:
            ok = self.macro_manager.export_macros(Path(file_path))
            if ok:
                QMessageBox.information(self, 'Export Success', 'Macros exported successfully.')
            else:
                QMessageBox.warning(self, 'Export Failed', 'Failed to export macros.')

    def _ask_save_changes(self) -> QMessageBox.StandardButton:
        return QMessageBox.question(self, 'Unsaved Changes', 'You have unsaved changes. Do you want to save them?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)

    def _format_date(self, date_str: str) -> str:
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return date_str

    def closeEvent(self, event) -> None:
        # Prompt on close only when actual changes exist compared to loaded/original values
        if self._has_actual_changes():
            r = self._ask_save_changes()
            if r == QMessageBox.StandardButton.Yes:
                self._save_macro()
        super().closeEvent(event)

# Quick test launcher
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    # Apply comprehensive dark theme
    apply_dark_theme(app)
    
    mgr = MacroManager()
    dlg = MacroManagerDialog(mgr)
    dlg.show()
    sys.exit(app.exec())
