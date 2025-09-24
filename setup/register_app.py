#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Автоматическая регистрация Image Tag Editor как программы по умолчанию в Windows.

Этот скрипт автоматически создает необходимые записи в реестре Windows
для регистрации Image Tag Editor как обработчика файлов изображений.

Использование:
    python register_app.py
    
Или запустите от имени администратора для системной регистрации:
    python register_app.py --system
"""

import sys
import winreg
import os
from pathlib import Path
import argparse


def get_exe_path() -> Path:
    """Получить путь к исполняемому файлу программы."""
    # Если запускается как Python скрипт
    current_dir = Path(__file__).parent.absolute()
    
    # Ищем ImageTagEditor.exe в текущей папке
    exe_path = current_dir / "ImageTagEditor.exe"
    if exe_path.exists():
        return exe_path
    
    # Ищем в подпапке dist (после сборки PyInstaller)
    dist_path = current_dir / "dist" / "ImageTagEditor.exe"
    if dist_path.exists():
        return dist_path
    
    # Если не найден, используем Python скрипт как основу
    python_path = current_dir / "main.py"
    if python_path.exists():
        return python_path
    
    raise FileNotFoundError("Не удалось найти ImageTagEditor.exe или main.py")


def create_registry_entries(exe_path: Path, use_system: bool = False) -> None:
    """Создать записи в реестре Windows для регистрации программы.
    
    Args:
        exe_path: Путь к исполняемому файлу
        use_system: Если True, регистрирует для всей системы (требует права администратора)
    """
    # Определяем корневой раздел реестра
    if use_system:
        root_key = winreg.HKEY_LOCAL_MACHINE
        print("Регистрация для всей системы (требует права администратора)...")
    else:
        root_key = winreg.HKEY_CURRENT_USER
        print("Регистрация для текущего пользователя...")
    
    exe_str = str(exe_path)
    exe_dir = str(exe_path.parent)
    
    # Определяем команду запуска
    if exe_path.suffix.lower() == '.py':
        # Если это Python файл, используем python.exe
        command = f'python "{exe_str}" "%1"'
        # Ищем иконку в папке assets
        icon_path = exe_str.replace('main.py', 'assets/icon.ico')
        if not Path(icon_path).exists():
            icon_path = f"{exe_str},0"
    else:
        # Если это exe файл
        command = f'"{exe_str}" "%1"'
        icon_path = f"{exe_str},0"
    
    try:
        # 1. Регистрация пути приложения
        with winreg.CreateKey(root_key, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\ImageTagEditor.exe") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, exe_str)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, exe_dir)
        print("✓ Зарегистрирован путь приложения")
        
        # 2. Регистрация в списке зарегистрированных приложений
        with winreg.CreateKey(root_key, r"SOFTWARE\RegisteredApplications") as key:
            winreg.SetValueEx(key, "Image Tag Editor", 0, winreg.REG_SZ, r"SOFTWARE\ImageTagEditor\Capabilities")
        print("✓ Добавлено в список зарегистрированных приложений")
        
        # 3. Создание раздела возможностей приложения
        with winreg.CreateKey(root_key, r"SOFTWARE\ImageTagEditor\Capabilities") as key:
            winreg.SetValueEx(key, "ApplicationDescription", 0, winreg.REG_SZ, 
                            "Professional image tagging application with intelligent autocomplete")
            winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, "Image Tag Editor")
        print("✓ Созданы записи возможностей приложения")
        
        # 4. Ассоциации файлов
        extensions = [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"]
        with winreg.CreateKey(root_key, r"SOFTWARE\ImageTagEditor\Capabilities\FileAssociations") as key:
            for ext in extensions:
                winreg.SetValueEx(key, ext, 0, winreg.REG_SZ, "ImageTagEditor.Image")
        print(f"✓ Зарегистрированы ассоциации для {len(extensions)} типов файлов")
        
        # 5. Класс файлов ImageTagEditor.Image
        with winreg.CreateKey(root_key, r"SOFTWARE\Classes\ImageTagEditor.Image") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Image Tag Editor Image File")
            winreg.SetValueEx(key, "FriendlyTypeName", 0, winreg.REG_SZ, "Image Tag Editor Image File")
        print("✓ Создан класс файлов")
        
        # 6. Иконка по умолчанию
        with winreg.CreateKey(root_key, r"SOFTWARE\Classes\ImageTagEditor.Image\DefaultIcon") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, icon_path)
        print("✓ Установлена иконка по умолчанию")
        
        # 7. Команда открытия
        with winreg.CreateKey(root_key, r"SOFTWARE\Classes\ImageTagEditor.Image\shell\open\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        print("✓ Зарегистрирована команда открытия")
        
        # 8. Дополнительная команда "Редактировать теги"
        with winreg.CreateKey(root_key, r"SOFTWARE\Classes\ImageTagEditor.Image\shell\edit") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Редактировать теги")
        
        with winreg.CreateKey(root_key, r"SOFTWARE\Classes\ImageTagEditor.Image\shell\edit\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        print("✓ Добавлена команда 'Редактировать теги' в контекстное меню")
        
        print("\n✅ Регистрация завершена успешно!")
        print("\nТеперь вы можете:")
        print("1. Открыть 'Параметры Windows' → 'Приложения' → 'Приложения по умолчанию'")
        print("2. Найти 'Image Tag Editor' в списке приложений")
        print("3. Назначить его программой по умолчанию для нужных типов файлов")
        print("\nИли:")
        print("1. Щелкните правой кнопкой по любому изображению")
        print("2. Выберите 'Открыть с помощью' → 'Выбрать другое приложение'")
        print("3. Найдите 'Image Tag Editor' в списке")
        print("4. Поставьте галочку 'Всегда использовать это приложение'")
        
    except PermissionError:
        print("❌ Ошибка: Недостаточно прав для записи в реестр")
        print("Попробуйте:")
        print("1. Запустить командную строку от имени администратора")
        print("2. Выполнить: python register_app.py --system")
        print("Или запустите без флага --system для регистрации только для текущего пользователя")
        return False
    except Exception as e:
        print(f"❌ Ошибка при регистрации: {e}")
        return False
    
    return True


def unregister_app(use_system: bool = False) -> None:
    """Удалить записи Image Tag Editor из реестра.
    
    Args:
        use_system: Если True, удаляет из системного реестра
    """
    root_key = winreg.HKEY_LOCAL_MACHINE if use_system else winreg.HKEY_CURRENT_USER
    scope = "системного" if use_system else "пользовательского"
    
    print(f"Удаление записей из {scope} реестра...")
    
    # Список ключей для удаления
    keys_to_delete = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\ImageTagEditor.exe",
        r"SOFTWARE\ImageTagEditor",
        r"SOFTWARE\Classes\ImageTagEditor.Image",
    ]
    
    deleted_count = 0
    
    for key_path in keys_to_delete:
        try:
            winreg.DeleteKeyEx(root_key, key_path)
            deleted_count += 1
            print(f"✓ Удален ключ: {key_path}")
        except FileNotFoundError:
            print(f"- Ключ не найден: {key_path}")
        except Exception as e:
            print(f"❌ Ошибка удаления ключа {key_path}: {e}")
    
    # Удаление из RegisteredApplications
    try:
        with winreg.OpenKey(root_key, r"SOFTWARE\RegisteredApplications", 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, "Image Tag Editor")
            print("✓ Удалено из RegisteredApplications")
            deleted_count += 1
    except FileNotFoundError:
        print("- RegisteredApplications запись не найдена")
    except Exception as e:
        print(f"❌ Ошибка удаления из RegisteredApplications: {e}")
    
    if deleted_count > 0:
        print(f"\n✅ Удалено {deleted_count} записей из реестра")
        print("Image Tag Editor больше не зарегистрирован как обработчик изображений")
    else:
        print("\n⚠️  Записи Image Tag Editor в реестре не найдены")


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(
        description="Регистрация Image Tag Editor как программы по умолчанию для изображений"
    )
    parser.add_argument(
        "--system",
        action="store_true",
        help="Регистрация для всей системы (требует права администратора)"
    )
    parser.add_argument(
        "--unregister",
        action="store_true",
        help="Удалить регистрацию Image Tag Editor"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Image Tag Editor - Регистрация в Windows")
    print("=" * 60)
    
    if args.unregister:
        unregister_app(args.system)
        return
    
    try:
        exe_path = get_exe_path()
        print(f"Найден исполняемый файл: {exe_path}")
        
        if not exe_path.exists():
            print(f"❌ Файл не существует: {exe_path}")
            sys.exit(1)
        
        success = create_registry_entries(exe_path, args.system)
        
        if success:
            print("\n🎉 Готово! Image Tag Editor зарегистрирован в Windows")
            if not args.system:
                print("\n💡 Совет: Для регистрации на уровне системы запустите:")
                print("python register_app.py --system")
        else:
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\nУбедитесь, что:")
        print("1. ImageTagEditor.exe находится в той же папке")
        print("2. Или программа собрана в папке dist/")
        print("3. Или main.py существует для запуска через Python")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
