@echo off
chcp 65001 >nul
title KUAF So'rovnoma Bot

echo ========================================
echo    KUAF SO'ROVNOMA BOT
echo ========================================
echo.

:: Virtual environment yaratish
if not exist "venv" (
    echo [1/3] Virtual environment yaratilmoqda...
    python -m venv venv
    echo ✓ Virtual environment yaratildi
) else (
    echo [1/3] Virtual environment mavjud ✓
)

:: Aktivatsiya
echo [2/3] Virtual environment aktivatsiya qilinmoqda...
call venv\Scripts\activate.bat

:: Kutubxonalarni o'rnatish
echo [3/3] Kutubxonalar o'rnatilmoqda...
pip install -r requirements.txt --quiet

echo.
echo ========================================
echo    BOT ISHGA TUSHIRILMOQDA...
echo ========================================
echo.

:: Papkalar yaratish
if not exist "data" mkdir data
if not exist "data\excel_files" mkdir data\excel_files
if not exist "data\exports" mkdir data\exports
if not exist "logs" mkdir logs

:: Botni ishga tushirish
python bot.py

pause
