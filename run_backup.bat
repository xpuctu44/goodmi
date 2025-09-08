@echo off
REM Скрипт для автоматического создания резервной копии базы данных
REM Используется планировщиком задач Windows

echo [%DATE% %TIME%] Starting database backup...

REM Переходим в директорию проекта
cd /d "%~dp0"

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Python not found
    exit /b 1
)

REM Запускаем скрипт бэкапа
python backup_db.py

if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Backup script failed
    exit /b 1
) else (
    echo [%DATE% %TIME%] Backup completed successfully
)

exit /b 0