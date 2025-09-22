# Инструкция по компиляции Image Tag Editor в один файл с помощью Nuitka

Данная инструкция описывает процесс компиляции приложения Image Tag Editor в единый исполняемый файл с помощью Nuitka с полной поддержкой PyQt6.

## Предварительные требования

### 1. Установка Python и зависимостей
```bash
# Убедитесь, что у вас установлен Python 3.10+
python --version

# Установите зависимости проекта
pip install -r requirements.txt

# Дополнительно установите Nuitka
pip install nuitka
```

### 2. Установка компилятора C++
**Windows:**
- Установите Visual Studio 2019/2022 Community (с C++ tools)
- Или установите только Build Tools для Visual Studio
- Или установите MinGW-w64

**Linux:**
```bash
sudo apt-get install gcc g++
```

**macOS:**
```bash
xcode-select --install
```

## Компиляция с Nuitka

### Команда для компиляции в один файл

```bash
nuitka --onefile \
       --enable-plugin=pyqt6 \
       --disable-console \
       --windows-icon-from-ico=icon.ico \
       --output-filename=ImageTagEditor.exe \
       --assume-yes-for-downloads \
       --include-data-file=derpibooru.csv=derpibooru.csv \
       --include-data-file=icon.ico=icon.ico \
       --output-dir=dist \
       main.py
```

### Расшифровка параметров:

- `--onefile` - компиляция в единый исполняемый файл
- `--enable-plugin=pyqt6` - включение поддержки PyQt6
- `--disable-console` - скрыть консольное окно (для GUI приложения)
- `--windows-icon-from-ico=icon.ico` - установка иконки приложения
- `--output-filename=ImageTagEditor.exe` - имя выходного файла
- `--assume-yes-for-downloads` - автоматическое согласие на загрузку зависимостей
- `--include-data-file=...` - включение файлов данных в исполняемый файл
- `--output-dir=dist` - папка для сохранения результата

### Альтернативная команда для Windows (одной строкой)

```cmd
nuitka --onefile --enable-plugin=pyqt6 --disable-console --windows-icon-from-ico=icon.ico --output-filename=ImageTagEditor.exe --assume-yes-for-downloads --include-data-file=derpibooru.csv=derpibooru.csv --include-data-file=icon.ico=icon.ico --output-dir=dist main.py
```

## Дополнительные опции

### Для уменьшения размера файла:
```bash
# Добавьте эти параметры для оптимизации размера
--python-flag=no_docstrings \
--python-flag=no_asserts \
--remove-output \
```

### Для отладки проблем компиляции:
```bash
# Добавьте эти параметры для диагностики
--show-progress \
--show-memory \
--verbose \
```

### Для включения логирования в релизе:
```bash
# Если нужны логи в скомпилированной версии
--enable-plugin=anti-bloat \
--nofollow-import-to=logging \
```

## Полная команда с оптимизацией

```bash
nuitka --onefile \
       --enable-plugin=pyqt6 \
       --enable-plugin=anti-bloat \
       --disable-console \
       --windows-icon-from-ico=icon.ico \
       --output-filename=ImageTagEditor.exe \
       --assume-yes-for-downloads \
       --include-data-file=derpibooru.csv=derpibooru.csv \
       --include-data-file=icon.ico=icon.ico \
       --python-flag=no_docstrings \
       --python-flag=no_asserts \
       --remove-output \
       --show-progress \
       --output-dir=dist \
       main.py
```

## Возможные проблемы и решения

### 1. Ошибка "PyQt6 not found"
```bash
# Переустановите PyQt6
pip uninstall PyQt6
pip install PyQt6
```

### 2. Ошибка компиляции с иконкой
- Убедитесь, что файл `icon.ico` существует в корне проекта
- Или уберите параметр `--windows-icon-from-ico=icon.ico`

### 3. Большой размер итогового файла
- Используйте параметры оптимизации выше
- Или компилируйте в папку с зависимостями (уберите `--onefile`)

### 4. Медленная компиляция
- Первая компиляция может занять 10-20 минут
- Последующие компиляции будут быстрее благодаря кэшу

### 5. Ошибки времени выполнения
- Проверьте, что все файлы данных включены через `--include-data-file`
- Добавьте `--show-progress` для диагностики

## Структура результата

После компиляции в папке `dist/` будут созданы:
- `ImageTagEditor.exe` - основной исполняемый файл
- Временные файлы компиляции (можно удалить)

## Тестирование скомпилированного приложения

1. Скопируйте `derpibooru.csv` в папку с `ImageTagEditor.exe` (если не включили в компиляцию)
2. Запустите `ImageTagEditor.exe`
3. Протестируйте основные функции:
   - Загрузка изображений
   - Автодополнение тегов  
   - Навигация между изображениями
   - Сохранение тегов

## Распространение

Скомпилированный файл можно распространять как standalone приложение:
- Не требует установки Python
- Не требует установки PyQt6
- Включает все необходимые библиотеки
- Работает на чистых Windows системах

**Примечание:** Первый запуск может быть медленнее из-за распаковки библиотек во временные файлы.
