# Инструкция по компиляции Image Tag Editor в один файл с помощью Nuitka

Данная инструкция описывает процесс компиляции приложения Image Tag Editor в единый исполняемый файл с помощью Nuitka с полной поддержкой PyQt6.

## Предварительные требования

### 1. Установка Python и зависимостей
```powershell
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

```powershell
nuitka --onefile `
       --enable-plugin=pyqt6 `
       --disable-console `
       --windows-icon-from-ico=icon.ico `
       --output-filename=ImageTagEditor.exe `
       --assume-yes-for-downloads `
       --include-data-file=derpibooru.csv=derpibooru.csv `
       --include-data-file=icon.ico=icon.ico `
       --output-dir=dist `
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

```powershell
nuitka --onefile --enable-plugin=pyqt6 --disable-console --windows-icon-from-ico=icon.ico --output-filename=ImageTagEditor.exe --assume-yes-for-downloads --include-data-file=derpibooru.csv=derpibooru.csv --include-data-file=icon.ico=icon.ico --output-dir=dist main.py
```

## Дополнительные опции

### Для уменьшения размера файла:
```powershell
# Добавьте эти параметры для оптимизации размера
nuitka --onefile `
       --enable-plugin=pyqt6 `
       --disable-console `
       --windows-icon-from-ico=icon.ico `
       --output-filename=ImageTagEditor.exe `
       --assume-yes-for-downloads `
       --include-data-file=derpibooru.csv=derpibooru.csv `
       --include-data-file=icon.ico=icon.ico `
       --python-flag=no_docstrings `
       --python-flag=no_asserts `
       --remove-output `
       --output-dir=dist `
       main.py
```

### Для отладки проблем компиляции:
```powershell
# Добавьте эти параметры для диагностики
nuitka --onefile `
       --enable-plugin=pyqt6 `
       --disable-console `
       --windows-icon-from-ico=icon.ico `
       --output-filename=ImageTagEditor.exe `
       --assume-yes-for-downloads `
       --include-data-file=derpibooru.csv=derpibooru.csv `
       --include-data-file=icon.ico=icon.ico `
       --show-progress `
       --show-memory `
       --verbose `
       --output-dir=dist `
       main.py
```

### Для включения логирования в релизе:
```powershell
# Если нужны логи в скомпилированной версии
nuitka --onefile `
       --enable-plugin=pyqt6 `
       --enable-plugin=anti-bloat `
       --disable-console `
       --windows-icon-from-ico=icon.ico `
       --output-filename=ImageTagEditor.exe `
       --assume-yes-for-downloads `
       --include-data-file=derpibooru.csv=derpibooru.csv `
       --include-data-file=icon.ico=icon.ico `
       --nofollow-import-to=logging `
       --output-dir=dist `
       main.py
```

## Полная команда с оптимизацией

```powershell
nuitka --onefile `
       --enable-plugin=pyqt6 `
       --enable-plugin=anti-bloat `
       --disable-console `
       --windows-icon-from-ico=icon.ico `
       --output-filename=ImageTagEditor.exe `
       --assume-yes-for-downloads `
       --include-data-file=derpibooru.csv=derpibooru.csv `
       --include-data-file=icon.ico=icon.ico `
       --python-flag=no_docstrings `
       --python-flag=no_asserts `
       --remove-output `
       --show-progress `
       --output-dir=dist `
       main.py
```

## Возможные проблемы и решения

### 1. Ошибка "PyQt6 not found"
```powershell
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

### 6. Проблемы с путями в PowerShell
```powershell
# Если возникают проблемы с путями, используйте абсолютные пути
$currentDir = Get-Location
nuitka --onefile `
       --enable-plugin=pyqt6 `
       --disable-console `
       --windows-icon-from-ico="$currentDir\icon.ico" `
       --output-filename=ImageTagEditor.exe `
       --assume-yes-for-downloads `
       --include-data-file="$currentDir\derpibooru.csv=derpibooru.csv" `
       --include-data-file="$currentDir\icon.ico=icon.ico" `
       --output-dir="$currentDir\dist" `
       "$currentDir\main.py"
```

## Полезные PowerShell команды

### Проверка зависимостей перед компиляцией:
```powershell
# Проверка установки необходимых модулей
python -c "import pandas; import numpy; import PyQt6; print('All dependencies imported successfully')"

# Проверка версий
python -c "import PyQt6; print(f'PyQt6 version: {PyQt6.QtCore.PYQT_VERSION_STR}')"
```

### Очистка артефактов компиляции:
```powershell
# Удаление папки сборки
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "main.build") { Remove-Item -Recurse -Force "main.build" }
if (Test-Path "main.dist") { Remove-Item -Recurse -Force "main.dist" }

# Удаление кэша Nuitka (если нужно)
if (Test-Path "$env:APPDATA\Nuitka") { Remove-Item -Recurse -Force "$env:APPDATA\Nuitka" }
```

## Структура результата

После компиляции в папке `dist/` будут созданы:
- `ImageTagEditor.exe` - основной исполняемый файл
- Временные файлы компиляции (можно удалить)

## Тестирование скомпилированного приложения

```powershell
# Переход в папку с результатом
Set-Location dist

# Запуск приложения
.\ImageTagEditor.exe

# Возврат в исходную папку
Set-Location ..
```

### Проверка функциональности:
1. Скопируйте `derpibooru.csv` в папку с `ImageTagEditor.exe` (если не включили в компиляцию)
2. Запустите `ImageTagEditor.exe`
3. Протестируйте основные функции:
   - Загрузка изображений
   - Автодополнение тегов  
   - Навигация между изображениями
   - Сохранение тегов

## Автоматизация сборки

### PowerShell скрипт для автоматической сборки:
```powershell
# build.ps1
param(
    [switch]$Clean,
    [switch]$Optimized
)

Write-Host "Building Image Tag Editor with Nuitka..." -ForegroundColor Green

# Очистка предыдущих сборок
if ($Clean -or $Optimized) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "main.build") { Remove-Item -Recurse -Force "main.build" }
    if (Test-Path "main.dist") { Remove-Item -Recurse -Force "main.dist" }
}

# Проверка зависимостей
Write-Host "Checking dependencies..." -ForegroundColor Yellow
python -c "import pandas; import numpy; import PyQt6; print('✓ All dependencies OK')"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Dependencies check failed!" -ForegroundColor Red
    exit 1
}

# Команда компиляции
$nuitkaArgs = @(
    "--onefile"
    "--enable-plugin=pyqt6"
    "--disable-console"
    "--windows-icon-from-ico=icon.ico"
    "--output-filename=ImageTagEditor.exe"
    "--assume-yes-for-downloads"
    "--include-data-file=derpibooru.csv=derpibooru.csv"
    "--include-data-file=icon.ico=icon.ico"
    "--show-progress"
    "--output-dir=dist"
)

if ($Optimized) {
    $nuitkaArgs += @(
        "--enable-plugin=anti-bloat"
        "--python-flag=no_docstrings"
        "--python-flag=no_asserts"
        "--remove-output"
    )
}

$nuitkaArgs += "main.py"

Write-Host "Running Nuitka compilation..." -ForegroundColor Yellow
& nuitka @nuitkaArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Build completed successfully!" -ForegroundColor Green
    Write-Host "Executable location: dist\ImageTagEditor.exe" -ForegroundColor Cyan
    
    # Показать размер файла
    $fileSize = (Get-Item "dist\ImageTagEditor.exe").Length / 1MB
    Write-Host "File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan
} else {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}
```

### Использование скрипта:
```powershell
# Обычная сборка
.\build.ps1

# Сборка с очисткой
.\build.ps1 -Clean

# Оптимизированная сборка
.\build.ps1 -Optimized

# Полная очистка и оптимизированная сборка
.\build.ps1 -Clean -Optimized
```

## Распространение

Скомпилированный файл можно распространять как standalone приложение:
- Не требует установки Python
- Не требует установки PyQt6
- Включает все необходимые библиотеки
- Работает на чистых Windows системах

**Примечание:** Первый запуск может быть медленнее из-за распаковки библиотек во временные файлы.
