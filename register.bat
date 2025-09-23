@echo off
chcp 65001 >nul
echo ====================================================================
echo Image Tag Editor - Регистрация как программа по умолчанию в Windows
echo ====================================================================
echo.

echo Выберите способ регистрации:
echo.
echo 1. Для текущего пользователя (рекомендуется)
echo 2. Для всей системы (требует права администратора)
echo 3. Удалить регистрацию
echo 4. Выход
echo.
set /p choice="Ваш выбор (1-4): "

if "%choice%"=="1" (
    echo.
    echo Регистрация для текущего пользователя...
    python register_app.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo Регистрация для всей системы...
    echo Запрос прав администратора...
    python register_app.py --system
    goto end
)

if "%choice%"=="3" (
    echo.
    echo Удаление регистрации...
    python register_app.py --unregister
    goto end
)

if "%choice%"=="4" (
    echo Выход...
    goto end
)

echo Неверный выбор. Попробуйте снова.
pause
goto start

:end
echo.
echo Для назначения Image Tag Editor программой по умолчанию:
echo 1. Откройте "Параметры Windows" → "Приложения" → "Приложения по умолчанию"
echo 2. Найдите "Image Tag Editor" в списке
echo 3. Назначьте его для нужных типов файлов изображений
echo.
echo Или щелкните правой кнопкой по изображению → "Открыть с помощью" → "Image Tag Editor"
echo.
pause
