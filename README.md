# 📋 KUAF SO'ROVNOMA BOT

KUAF universiteti talabalari uchun so'rovnoma boti (O'zbek tilida).

---

## 🚀 TEZKOR BOSHLASH

### Windows:
```cmd
1. .env faylida BOT_TOKEN va SUPER_ADMIN_IDS ni kiriting
2. start.bat ni ikki marta bosing
```

### Linux/Mac:
```bash
1. cp .env.example .env
2. nano .env (token va ID kiriting)
3. chmod +x start.sh && ./start.sh
```

---

## ⚙️ SOZLASH

### 1. Bot Token olish
1. Telegram'da @BotFather ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomi va username kiriting
4. Tokenni nusxalang

### 2. Admin ID olish
1. @userinfobot ga `/start` yuboring
2. Sizning ID ni ko'rsatadi

### 3. .env faylini sozlash
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
SUPER_ADMIN_IDS=123456789,987654321
CHANNEL_USERNAME=mychannel  # Ixtiyoriy
```

---

## 📊 SO'ROVNOMA SAVOLLARI

Bot quyidagi savollarni so'raydi:

1. **Telefon raqami** (qo'shimcha raqamlar ham mumkin)
2. **Doimiy yashash manzili** (pasport bo'yicha)
3. **Doimiy manzil lokatsiyasi** (GPS)
4. **Avvalgi ta'lim muassasasi**
5. **Hujjat seriya raqami** (shahodatnoma/diplom)
6. **Yutuqlar** (Ha/Yo'q, tafsilotlar)
7. **Til sertifikati** (IELTS, TOEFL va boshqalar)
8. **Grant/imtiyoz** (Ha/Yo'q, tafsilotlar)
9. **Ijtimoiy himoya reestri** (Ha/Yo'q)
10. **Temir daftar** (Ha/Yo'q)
11. **Yoshlar daftari** (Ha/Yo'q)
12. **Ota-ona ma'lumotlari** (hayotmi, ism, telefon)
13. **Yashash turi** (uy/TTJ/ijara/qarindosh)
14. **TTJ joylashuvi** (qayerdan qatnaydi)
15. **Ijara ma'lumotlari** (manzil, lokatsiya, egasi)
16. **Ishlaysizmi** (Ha/Yo'q, ish joyi)
17. **Oilalikmisiz** (Ha/Yo'q)
18. **Xorijga chiqish pasporti** (Ha/Yo'q)
19. **Ijtimoiy tarmoq kanallari** (Ha/Yo'q, linklar)

---

## 👨‍💼 ADMIN PANEL

`/admin` buyrug'i orqali:

- 📤 **Excel Export** - Barcha so'rovnoma javoblarini yuklab olish
- 📥 **Excel Import** - Talabalar ro'yxatini yuklash
- 📊 **Statistika** - Umumiy ma'lumotlar
- ➕ **Xodim qo'shish** - Yangi admin qo'shish
- ➖ **Xodim o'chirish** - Adminni olib tashlash
- 📢 **E'lon yuborish** - Barcha foydalanuvchilarga xabar

---

## 📁 FAYL TUZILISHI

```
unisorovbot/
├── bot.py              # Asosiy bot kodi
├── database.py         # Ma'lumotlar bazasi
├── excel_handler.py    # Excel import/export
├── .env               # Sozlamalar (serverda yaratiladi)
├── .env.example       # Sozlamalar namunasi
├── requirements.txt   # Python kutubxonalari
├── start.bat          # Windows uchun ishga tushirish
├── start.sh           # Linux uchun ishga tushirish
├── data/
│   ├── survey.db      # SQLite database
│   ├── excel_files/   # Import fayllari
│   └── exports/       # Export fayllari
└── logs/
    └── bot.log        # Log fayllari
```

---

## 🖥 SERVER O'RNATISH

### 1. Fayllarni serverga yuklash
```bash
scp -r unisorovbot/ user@server:/home/user/
```

### 2. Serverda sozlash
```bash
cd /home/user/unisorovbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Token va ID kiriting
```

### 3. Systemd service yaratish
```bash
sudo nano /etc/systemd/system/kuafbot.service
```

```ini
[Unit]
Description=KUAF Survey Bot
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/unisorovbot
ExecStart=/home/user/unisorovbot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Xizmatni ishga tushirish
```bash
sudo systemctl daemon-reload
sudo systemctl enable kuafbot
sudo systemctl start kuafbot
sudo systemctl status kuafbot
```

---

## 📝 TALABALAR IMPORTI

Excel fayl formati (`IT va ijtimoiy umumiy ro'yhad.xlsx`):
- 36 ta ustun (talaba ma'lumotlari)
- Unique ID avtomatik yaratiladi (1, 2, 3...)
- Passport yoki JSHSHIR bo'yicha qidiriladi

---

## 🔧 MUAMMOLARNI HAL QILISH

### Bot ishlamayapti
```bash
sudo systemctl status kuafbot
sudo journalctl -u kuafbot -f
```

### Database xatosi
```bash
rm data/survey.db
python bot.py  # Yangi database yaratiladi
```

### Log ko'rish
```bash
tail -f logs/bot.log
```

---

## 📞 ALOQA

Savollar bo'lsa: @SysMasters

---

**© 2026 KUAF Survey Bot**
