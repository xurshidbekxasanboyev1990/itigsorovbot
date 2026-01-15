#!/bin/bash

echo "========================================"
echo "   KUAF SO'ROVNOMA BOT"
echo "========================================"
echo ""

# Virtual environment yaratish
if [ ! -d "venv" ]; then
    echo "[1/3] Virtual environment yaratilmoqda..."
    python3 -m venv venv
    echo "✓ Virtual environment yaratildi"
else
    echo "[1/3] Virtual environment mavjud ✓"
fi

# Aktivatsiya
echo "[2/3] Virtual environment aktivatsiya qilinmoqda..."
source venv/bin/activate

# Kutubxonalarni o'rnatish
echo "[3/3] Kutubxonalar o'rnatilmoqda..."
pip install -r requirements.txt --quiet

echo ""
echo "========================================"
echo "   BOT ISHGA TUSHIRILMOQDA..."
echo "========================================"
echo ""

# Papkalar yaratish
mkdir -p data/excel_files
mkdir -p data/exports
mkdir -p logs

# Botni ishga tushirish
python bot.py
