# bot.py - KUAF So'rovnoma Bot (O'zbek tili)

import asyncio
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    FSInputFile, ContentType
)
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

from database import Database
from excel_handler import ExcelHandler

# Environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN_IDS = [int(x) for x in os.getenv('SUPER_ADMIN_IDS', '').split(',') if x]
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/survey.db')
EXCEL_DIR = os.getenv('EXCEL_DIR', 'data/excel_files')
EXPORT_DIR = os.getenv('EXPORT_DIR', 'data/exports')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '')

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot va Database
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

db = Database(DATABASE_PATH)
excel_handler = ExcelHandler(db, EXCEL_DIR, EXPORT_DIR)


# ================= MATNLAR (O'ZBEK TILI) =================
TEXTS = {
    'welcome': "Assalomu aleykum!\n\nKUAF talabalari uchun rasmiy so'rovnoma botiga xush kelibsiz.\n\n📋 So'rovnomani boshlash uchun quyidagilardan birini kiriting:\n\n• Passport seriya va raqami (masalan: AB1234567)\n• Talaba ID raqami\n• JSHSHIR (14 raqam)",
    'student_not_found': "❌ Talaba topilmadi!\n\nIltimos, ma'lumotlarni to'g'ri kiritganingizga ishonch hosil qiling.",
    'student_found': "✅ Talaba topildi:\n\n👤 F.I.O: {fullname}\n📞 Telefon: {phone}\n👥 Guruh: {group}",
    
    # Savollar
    'q1_phone': "📱 Telefon raqamingizni kiriting:\n\n(Qo'shimcha raqamlar ham kiritish mumkin)\nMasalan: +998901234567 yoki +998901234567, +998991234567",
    'q2_address': "🏠 Doimiy yashash manzilingizni kiriting:\n\n(To'liq yozilsin, pasport bo'yicha)\nMasalan: Andijon viloyati, Andijon shahri, Ozodlik MFY, Shahrihon ko'cha, 23-uy, 7-xonadon",
    'q3_location': "📍 Doimiy yashash joyingiz lokatsiyasini yuboring:\n\n(📎 Joylashuv tugmasini bosing yoki lokatsiyani qo'lda yuboring)",
    'q4_previous_education': "🎓 Avvalgi o'qigan ta'lim muassasangizni kiriting:\n\nMasalan: Andijon viloyati, Buloqboshi tumani, 5-umumta'lim maktabi, 2025-yil 11-sinfni tamomlagan",
    'q5_document': "📄 Hujjat seriya raqamini kiriting:\n\n(Shahodatnoma yoki diplom)",
    'q6_achievements': "🏆 Yutuqlaringiz bormi?",
    'q6_achievements_details': "🏆 Yutuqlaringizni yozing:\n\nMasalan: Shahmatdan O'zbekiston chempioni",
    'q7_certificate': "📜 Til sertifikatingiz bormi?",
    'q7_certificate_type': "📜 Qaysi til sertifikatingiz bor?",
    'q7_certificate_details': "📜 Sertifikat ma'lumotlarini kiriting:\n\n(Til, daraja, berilgan sana, amal qilish muddati)\nMasalan: IELTS 6.5, 01.01.2025, 01.01.2027",
    'q9_grant': "🎓 Grant (imtiyoz) bormi?",
    'q9_grant_details': "🎓 Grant ma'lumotlarini kiriting:\n\nMasalan: 100% 1-yil yoki 50% 4-yil",
    'q10_social_protection': "🛡 Ijtimoiy himoya reestriga kirgansizmi?",
    'q11_iron_book': "📕 Temir daftarda turasizmi?",
    'q12_youth_book': "📗 Yoshlar daftarida turasizmi?",
    
    # Ota-ona savollari
    'q13_father_name': "👨 Otangizning to'liq ISM va FAMILIYASini kiriting:\n\nMasalan: Karimov Karim Karimovich",
    'q14_father_alive': "👨 Otangiz hayotdami?",
    'q14_father_phone': "📱 Otangizning telefon raqamini kiriting:",
    'q15_mother_name': "👩 Onangizning to'liq ISM va FAMILIYASini kiriting:\n\nMasalan: Karimova Karima Karimovna",
    'q16_mother_alive': "👩 Onangiz hayotdami?",
    'q16_mother_phone': "📱 Onangizning telefon raqamini kiriting:",
    'q17_parents_together': "👨‍👩‍👦 Ota-onangiz birga yashaydimi?",
    
    # Ijara savollari
    'q18_living_type': "🏠 Qayerda yashaysiz?",
    'q19_rent_address': "🏠 Ijara xonadonining manzilini kiriting:\n\nMasalan: Andijon shahar, Bobur shox ko'chasi, Sanoat MFY, 12-uy, 34-xonadon",
    'q20_rent_location': "📍 Ijara xonadonining lokatsiyasini yuboring:",
    'q21_rent_owner': "👤 Ijara xonadoni egasining ISM va FAMILIYASini kiriting:",
    
    # Ish savollari
    'q22_working': "💼 Ishlaysizmi?",
    'q23_workplace': "🏢 Ish joyingizni kiriting:\n\n(To'liq manzil va lavozim)\nMasalan: Andijon shahar, IT Park, Dasturchi",
    
    # Oila savoli
    'q24_married': "💍 Oilalikmisiz?",
    
    # Pasport va ijtimoiy tarmoqlar
    'q25_foreign_passport': "📘 Xorijga chiqish pasportingiz mavjudmi?",
    'q26_social_channels': "📱 Ijtimoiy tarmoqlarda kanal yoki guruhlaringiz bormi?\n\n(Shaxsiy emas, o'zingiz ochgan har qanday auditoriyaga ega guruh yoki kanal)",
    'q26_social_links': "🔗 Barcha kanal va guruhlaringiz linkini yuboring:\n\n(Telegram, Instagram, YouTube, TikTok va boshqalar)\nMasalan:\nhttps://t.me/kanalim\nhttps://instagram.com/sahifam",
    
    # Yakuniy
    'survey_completed': "✅ So'rovnoma muvaffaqiyatli yakunlandi!\n\nBarcha ma'lumotlaringiz saqlandi.\n\nIshtirok etganingiz uchun rahmat! 🙏",
    'error': "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
    'skip': "⏭ O'tkazib yuborish",
    'yes': "Ha ✅",
    'no': "Yo'q ❌",
    'back': "⬅️ Orqaga",
    
    # Admin
    'admin_panel': "👨‍💼 Admin Panel",
    'excel_export': "📤 Excel Export",
    'excel_import': "📥 Excel Import",
    'statistics': "📊 Statistika",
    'add_staff': "➕ Xodim qo'shish",
    'remove_staff': "➖ Xodim o'chirish",
    'send_announcement': "📢 E'lon yuborish",
    'clear_surveys': "🗑 So'rovnomalarni tozalash",
    'access_denied': "🚫 Sizda bu bo'limga kirish huquqi yo'q.",
}


# ================= FSM STATES =================
class SurveyStates(StatesGroup):
    """So'rovnoma holatlari"""
    entering_search = State()
    
    # So'rovnoma savollari
    q1_phone = State()
    q2_address = State()
    q3_location = State()
    q4_previous_education = State()
    q5_document = State()
    q6_achievements = State()
    q6_achievements_details = State()
    q7_certificate = State()
    q7_certificate_type = State()
    q7_certificate_details = State()
    q9_grant = State()
    q9_grant_details = State()
    q10_social_protection = State()
    q11_iron_book = State()
    q12_youth_book = State()
    q13_father_name = State()
    q14_father_alive = State()
    q14_father_phone = State()
    q15_mother_name = State()
    q16_mother_alive = State()
    q16_mother_phone = State()
    q17_parents_together = State()
    q18_living_type = State()
    q18_ttj_type = State()  # TTJ uchun qo'shimcha savol
    q19_rent_address = State()
    q20_rent_location = State()
    q21_rent_owner = State()
    q22_working = State()
    q23_workplace = State()
    q24_married = State()
    q25_foreign_passport = State()
    q26_social_channels = State()
    q26_social_links = State()


class AdminStates(StatesGroup):
    """Admin panel holatlari"""
    main_panel = State()
    waiting_excel_import = State()
    waiting_staff_id = State()
    waiting_announcement = State()


# ================= KLAVIATURALAR =================
def get_yes_no_keyboard(back_callback: str = None) -> InlineKeyboardMarkup:
    """Ha/Yo'q klaviaturasi"""
    buttons = [
        [
            InlineKeyboardButton(text="Ha ✅", callback_data="answer_yes"),
            InlineKeyboardButton(text="Yo'q ❌", callback_data="answer_no")
        ]
    ]
    if back_callback:
        buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_yes_no_skip_keyboard(back_callback: str = None) -> InlineKeyboardMarkup:
    """Ha/Yo'q/O'tkazish klaviaturasi"""
    buttons = [
        [
            InlineKeyboardButton(text="Ha ✅", callback_data="answer_yes"),
            InlineKeyboardButton(text="Yo'q ❌", callback_data="answer_no")
        ],
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="answer_skip")]
    ]
    if back_callback:
        buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_certificate_type_keyboard(back_callback: str = None) -> InlineKeyboardMarkup:
    """Sertifikat turi klaviaturasi"""
    buttons = [
        [InlineKeyboardButton(text="IELTS", callback_data="cert_ielts")],
        [InlineKeyboardButton(text="Milliy sertifikat", callback_data="cert_milliy")],
        [InlineKeyboardButton(text="TOEFL iBT", callback_data="cert_toefl_ibt")],
        [InlineKeyboardButton(text="TOEFL ITP", callback_data="cert_toefl_itp")],
        [InlineKeyboardButton(text="Cambridge", callback_data="cert_cambridge")],
        [InlineKeyboardButton(text="Linguaskill", callback_data="cert_linguaskill")],
        [InlineKeyboardButton(text="Duolingo", callback_data="cert_duolingo")],
        [InlineKeyboardButton(text="CEFR", callback_data="cert_cefr")],
        [InlineKeyboardButton(text="Boshqa", callback_data="cert_other")],
    ]
    if back_callback:
        buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_living_type_keyboard(back_callback: str = None) -> InlineKeyboardMarkup:
    """Yashash turi klaviaturasi"""
    buttons = [
        [InlineKeyboardButton(text="🏠 Uydan (oila bilan)", callback_data="living_home")],
        [InlineKeyboardButton(text="🏢 TTJ (talabalar turar joyi)", callback_data="living_ttj")],
        [InlineKeyboardButton(text="🏘 Ijaradan", callback_data="living_rent")],
        [InlineKeyboardButton(text="👨‍👩‍👧 Qarindoshlarnikida", callback_data="living_relatives")],
    ]
    if back_callback:
        buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_ttj_type_keyboard(back_callback: str = None) -> InlineKeyboardMarkup:
    """TTJ turar joylari klaviaturasi"""
    buttons = [
        [InlineKeyboardButton(text="Uydan", callback_data="ttj_uydan")],
        [InlineKeyboardButton(text="Jevachi TTJ dan", callback_data="ttj_jevachi")],
        [InlineKeyboardButton(text="KUAF TTJ dan", callback_data="ttj_kuaf")],
        [InlineKeyboardButton(text="Texnika DXSH dan", callback_data="ttj_texnika")],
        [InlineKeyboardButton(text="Kamolot Ko'cha TTJ dan", callback_data="ttj_kamolot")],
        [InlineKeyboardButton(text="FAMILY MED TTJ dan", callback_data="ttj_family_med")],
        [InlineKeyboardButton(text="Ijaradan (kvartira)", callback_data="ttj_ijara")],
    ]
    if back_callback:
        buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_location_keyboard(back_callback: str = None) -> ReplyKeyboardMarkup:
    """Lokatsiya yuborish klaviaturasi"""
    buttons = [
        [KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)],
        [KeyboardButton(text="⏭ O'tkazib yuborish")]
    ]
    if back_callback:
        buttons.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


def get_skip_keyboard(back_callback: str = None) -> InlineKeyboardMarkup:
    """O'tkazib yuborish klaviaturasi"""
    buttons = [
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="answer_skip")]
    ]
    if back_callback:
        buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard(back_callback: str) -> InlineKeyboardMarkup:
    """Faqat orqaga tugmasi"""
    buttons = [
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_callback)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel klaviaturasi"""
    buttons = [
        [InlineKeyboardButton(text=TEXTS['excel_export'], callback_data="admin_export")],
        [InlineKeyboardButton(text=TEXTS['excel_import'], callback_data="admin_import")],
        [InlineKeyboardButton(text=TEXTS['statistics'], callback_data="admin_stats")],
        [InlineKeyboardButton(text=TEXTS['add_staff'], callback_data="admin_add_staff")],
        [InlineKeyboardButton(text=TEXTS['remove_staff'], callback_data="admin_remove_staff")],
        [InlineKeyboardButton(text=TEXTS['send_announcement'], callback_data="admin_announce")],
        [InlineKeyboardButton(text=TEXTS['clear_surveys'], callback_data="admin_clear_surveys")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ================= HELPER FUNKSIYALAR =================
async def is_super_admin(user_id: int) -> bool:
    """Super admin ekanligini tekshirish"""
    return user_id in SUPER_ADMIN_IDS


async def is_staff_member(user_id: int) -> bool:
    """Xodim ekanligini tekshirish"""
    return await db.is_staff(user_id)


async def check_subscription(user_id: int) -> bool:
    """Kanal obunasini tekshirish"""
    if not CHANNEL_USERNAME:
        return True
    try:
        member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return True


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Obuna klaviaturasi"""
    buttons = [
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ================= HANDLERS =================

# /start command
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Bot boshlanganda"""
    try:
        await state.clear()
        
        # Admin/xodim uchun obuna shart emas
        if not (await is_super_admin(message.from_user.id) or await is_staff_member(message.from_user.id)):
            if CHANNEL_USERNAME and not await check_subscription(message.from_user.id):
                await message.answer(
                    "❗️ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!",
                    reply_markup=get_subscription_keyboard()
                )
                return
        
        await message.answer(text=TEXTS['welcome'])
        await state.set_state(SurveyStates.entering_search)
    
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer("Xatolik yuz berdi. Qaytadan /start bosing.")


# Obuna tekshirish
@router.callback_query(F.data == "check_subscription")
async def process_check_subscription(callback: CallbackQuery, state: FSMContext):
    """Obunani tekshirish"""
    try:
        if await check_subscription(callback.from_user.id):
            await callback.message.edit_text("✅ Obuna tasdiqlandi!")
            await asyncio.sleep(0.5)
            await callback.message.answer(text=TEXTS['welcome'])
            await state.set_state(SurveyStates.entering_search)
        else:
            await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)
    except Exception as e:
        logger.error(f"Error in check_subscription: {e}")


# ================= ORQAGA QAYTISH HANDLER =================
@router.callback_query(F.data.startswith("back_"))
async def process_back(callback: CallbackQuery, state: FSMContext):
    """Orqaga qaytish"""
    try:
        back_to = callback.data.replace("back_", "")
        
        if back_to == "q1":
            await callback.message.edit_text(text=TEXTS['q1_phone'], reply_markup=get_back_keyboard("back_search"))
            await state.set_state(SurveyStates.q1_phone)
        elif back_to == "q2":
            await callback.message.edit_text(text=TEXTS['q2_address'], reply_markup=get_back_keyboard("back_q1"))
            await state.set_state(SurveyStates.q2_address)
        elif back_to == "q4":
            await callback.message.edit_text(text=TEXTS['q4_previous_education'], reply_markup=get_back_keyboard("back_q3"))
            await state.set_state(SurveyStates.q4_previous_education)
        elif back_to == "q5":
            await callback.message.edit_text(text=TEXTS['q5_document'], reply_markup=get_back_keyboard("back_q4"))
            await state.set_state(SurveyStates.q5_document)
        elif back_to == "q6":
            await callback.message.edit_text(text=TEXTS['q6_achievements'], reply_markup=get_yes_no_keyboard("back_q5"))
            await state.set_state(SurveyStates.q6_achievements)
        elif back_to == "q7":
            await callback.message.edit_text(text=TEXTS['q7_certificate'], reply_markup=get_yes_no_keyboard("back_q6"))
            await state.set_state(SurveyStates.q7_certificate)
        elif back_to == "q9":
            await callback.message.edit_text(text=TEXTS['q9_grant'], reply_markup=get_yes_no_keyboard("back_q7"))
            await state.set_state(SurveyStates.q9_grant)
        elif back_to == "q10":
            await callback.message.edit_text(text=TEXTS['q10_social_protection'], reply_markup=get_yes_no_keyboard("back_q9"))
            await state.set_state(SurveyStates.q10_social_protection)
        elif back_to == "q11":
            await callback.message.edit_text(text=TEXTS['q11_iron_book'], reply_markup=get_yes_no_keyboard("back_q10"))
            await state.set_state(SurveyStates.q11_iron_book)
        elif back_to == "q12":
            await callback.message.edit_text(text=TEXTS['q12_youth_book'], reply_markup=get_yes_no_keyboard("back_q11"))
            await state.set_state(SurveyStates.q12_youth_book)
        elif back_to == "q14":  # Ota hayotdami
            await callback.message.edit_text(text=TEXTS['q14_father_alive'], reply_markup=get_yes_no_keyboard("back_q12"))
            await state.set_state(SurveyStates.q14_father_alive)
        elif back_to == "q13":  # Ota ismi
            await callback.message.edit_text(text=TEXTS['q13_father_name'], reply_markup=get_back_keyboard("back_q14"))
            await state.set_state(SurveyStates.q13_father_name)
        elif back_to == "q14_phone":  # Ota telefoni
            await callback.message.edit_text(text=TEXTS['q14_father_phone'], reply_markup=get_back_keyboard("back_q13"))
            await state.set_state(SurveyStates.q14_father_phone)
        elif back_to == "q16":  # Ona hayotdami
            data = await state.get_data()
            if data.get('father_alive') == "Ha":
                await callback.message.edit_text(text=TEXTS['q16_mother_alive'], reply_markup=get_yes_no_keyboard("back_q14_phone"))
            else:
                await callback.message.edit_text(text=TEXTS['q16_mother_alive'], reply_markup=get_yes_no_keyboard("back_q14"))
            await state.set_state(SurveyStates.q16_mother_alive)
        elif back_to == "q15":  # Ona ismi
            await callback.message.edit_text(text=TEXTS['q15_mother_name'], reply_markup=get_back_keyboard("back_q16"))
            await state.set_state(SurveyStates.q15_mother_name)
        elif back_to == "q16_phone":  # Ona telefoni
            await callback.message.edit_text(text=TEXTS['q16_mother_phone'], reply_markup=get_back_keyboard("back_q15"))
            await state.set_state(SurveyStates.q16_mother_phone)
        elif back_to == "q17":  # Ota-ona birgami
            data = await state.get_data()
            if data.get('mother_alive') == "Ha":
                await callback.message.edit_text(text=TEXTS['q17_parents_together'], reply_markup=get_yes_no_keyboard("back_q16_phone"))
            else:
                await callback.message.edit_text(text=TEXTS['q17_parents_together'], reply_markup=get_yes_no_keyboard("back_q16"))
            await state.set_state(SurveyStates.q17_parents_together)
        elif back_to == "q18":  # Yashash turi
            data = await state.get_data()
            if data.get('father_alive') == "Ha" and data.get('mother_alive') == "Ha":
                await callback.message.edit_text(text=TEXTS['q18_living_type'], reply_markup=get_living_type_keyboard("back_q17"))
            elif data.get('mother_alive') == "Ha":
                await callback.message.edit_text(text=TEXTS['q18_living_type'], reply_markup=get_living_type_keyboard("back_q16_phone"))
            elif data.get('father_alive') == "Ha":
                await callback.message.edit_text(text=TEXTS['q18_living_type'], reply_markup=get_living_type_keyboard("back_q16"))
            else:
                await callback.message.edit_text(text=TEXTS['q18_living_type'], reply_markup=get_living_type_keyboard("back_q16"))
            await state.set_state(SurveyStates.q18_living_type)
        elif back_to == "q18_ttj":  # TTJ tanlash
            await callback.message.edit_text(text="🏢 KUAF ga qayerdan qatnaysiz?", reply_markup=get_ttj_type_keyboard("back_q18"))
            await state.set_state(SurveyStates.q18_ttj_type)
        elif back_to == "q3":  # Lokatsiya
            # ReplyKeyboard uchun yangi xabar yuborish kerak
            await callback.message.delete()
            await callback.message.answer(text=TEXTS['q3_location'], reply_markup=get_location_keyboard("back_q2"))
            await state.set_state(SurveyStates.q3_location)
        elif back_to == "q19":  # Ijara manzili
            await callback.message.edit_text(text=TEXTS['q19_rent_address'], reply_markup=get_back_keyboard("back_q18"))
            await state.set_state(SurveyStates.q19_rent_address)
        elif back_to == "q20":  # Ijara lokatsiyasi
            # ReplyKeyboard uchun yangi xabar yuborish kerak
            await callback.message.delete()
            await callback.message.answer(text=TEXTS['q20_rent_location'], reply_markup=get_location_keyboard("back_q19"))
            await state.set_state(SurveyStates.q20_rent_location)
        elif back_to == "q21":  # Ijara egasi
            await callback.message.edit_text(text=TEXTS['q21_rent_owner'], reply_markup=get_back_keyboard("back_q20"))
            await state.set_state(SurveyStates.q21_rent_owner)
        elif back_to == "q22":  # Ishlaydimi
            data = await state.get_data()
            living_type = data.get('living_type', '')
            if "Ijaradan" in living_type:
                await callback.message.edit_text(text=TEXTS['q22_working'], reply_markup=get_yes_no_keyboard("back_q21"))
            elif "TTJ" in living_type:
                await callback.message.edit_text(text=TEXTS['q22_working'], reply_markup=get_yes_no_keyboard("back_q18_ttj"))
            else:
                await callback.message.edit_text(text=TEXTS['q22_working'], reply_markup=get_yes_no_keyboard("back_q18"))
            await state.set_state(SurveyStates.q22_working)
        elif back_to == "q23":  # Ish joyi
            data = await state.get_data()
            living_type = data.get('living_type', '')
            if "Ijaradan" in living_type:
                back_btn = "back_q21"
            elif "TTJ" in living_type:
                back_btn = "back_q18_ttj"
            else:
                back_btn = "back_q18"
            await callback.message.edit_text(text=TEXTS['q23_workplace'], reply_markup=get_back_keyboard(back_btn))
            await state.set_state(SurveyStates.q23_workplace)
        elif back_to == "q24":  # Oilalikmisiz
            data = await state.get_data()
            if data.get('is_working') == "Ha":
                await callback.message.edit_text(text=TEXTS['q24_married'], reply_markup=get_yes_no_keyboard("back_q23"))
            else:
                await callback.message.edit_text(text=TEXTS['q24_married'], reply_markup=get_yes_no_keyboard("back_q22"))
            await state.set_state(SurveyStates.q24_married)
        elif back_to == "q25":  # Xorijga chiqish pasporti
            await callback.message.edit_text(text=TEXTS['q25_foreign_passport'], reply_markup=get_yes_no_keyboard("back_q24"))
            await state.set_state(SurveyStates.q25_foreign_passport)
        elif back_to == "q26":  # Ijtimoiy tarmoqlar
            await callback.message.edit_text(text=TEXTS['q26_social_channels'], reply_markup=get_yes_no_keyboard("back_q25"))
            await state.set_state(SurveyStates.q26_social_channels)
        elif back_to == "search":
            await callback.message.edit_text(text=TEXTS['welcome'])
            await state.set_state(SurveyStates.entering_search)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in back handler: {e}")
        await callback.answer("Xatolik yuz berdi")


# Talaba qidirish
@router.message(StateFilter(SurveyStates.entering_search), ~F.text.startswith("/"))
async def process_student_search(message: Message, state: FSMContext):
    """Talaba qidirish"""
    try:
        search_value = message.text.strip()
        student = await db.find_student(search_value)
        
        if not student:
            await message.answer(text=TEXTS['student_not_found'])
            return
        
        # Talaba ma'lumotlarini saqlash
        await state.update_data(
            unique_id=student['unique_id'],
            fullname=student['fullname'],
            group_name=student.get('group_name') or student.get('group_number'),
            db_phone=student.get('phone')
        )
        
        # Talaba topildi
        await message.answer(
            text=TEXTS['student_found'].format(
                fullname=student['fullname'],
                phone=student.get('phone') or "Kiritilmagan",
                group=student.get('group_name') or student.get('group_number') or "Kiritilmagan"
            )
        )
        
        await asyncio.sleep(0.5)
        
        # Q1 - Telefon raqam
        await message.answer(text=TEXTS['q1_phone'], reply_markup=get_back_keyboard("back_search"))
        await state.set_state(SurveyStates.q1_phone)
    
    except Exception as e:
        logger.error(f"Error in process_student_search: {e}")
        await message.answer(TEXTS['error'])


# Q1 - Telefon
@router.message(StateFilter(SurveyStates.q1_phone))
async def process_q1_phone(message: Message, state: FSMContext):
    """Telefon raqam"""
    try:
        await state.update_data(phone=message.text.strip())
        await message.answer(text=TEXTS['q2_address'], reply_markup=get_back_keyboard("back_q1"))
        await state.set_state(SurveyStates.q2_address)
    except Exception as e:
        logger.error(f"Error in q1: {e}")


# Q2 - Manzil
@router.message(StateFilter(SurveyStates.q2_address))
async def process_q2_address(message: Message, state: FSMContext):
    """Doimiy manzil"""
    try:
        await state.update_data(permanent_address=message.text.strip())
        await message.answer(text=TEXTS['q3_location'], reply_markup=get_location_keyboard("back_q2"))
        await state.set_state(SurveyStates.q3_location)
    except Exception as e:
        logger.error(f"Error in q2: {e}")


# Q3 - Lokatsiya
@router.message(StateFilter(SurveyStates.q3_location))
async def process_q3_location(message: Message, state: FSMContext):
    """Doimiy manzil lokatsiyasi"""
    try:
        # Orqaga tugmasi bosildi
        if message.text == "⬅️ Orqaga":
            await message.answer(text=TEXTS['q2_address'], reply_markup=get_back_keyboard("back_q1"))
            await state.set_state(SurveyStates.q2_address)
            return
        
        if message.location:
            location = f"{message.location.latitude},{message.location.longitude}"
            await state.update_data(permanent_location=location)
        elif message.text == "⏭ O'tkazib yuborish":
            await state.update_data(permanent_location="")
        else:
            await state.update_data(permanent_location=message.text.strip())
        
        await message.answer(text=TEXTS['q4_previous_education'], reply_markup=get_back_keyboard("back_q3"))
        await state.set_state(SurveyStates.q4_previous_education)
    except Exception as e:
        logger.error(f"Error in q3: {e}")


# Q4 - Avvalgi ta'lim
@router.message(StateFilter(SurveyStates.q4_previous_education))
async def process_q4_education(message: Message, state: FSMContext):
    """Avvalgi ta'lim muassasasi"""
    try:
        await state.update_data(previous_education=message.text.strip())
        await message.answer(text=TEXTS['q5_document'], reply_markup=get_back_keyboard("back_q4"))
        await state.set_state(SurveyStates.q5_document)
    except Exception as e:
        logger.error(f"Error in q4: {e}")


# Q5 - Hujjat
@router.message(StateFilter(SurveyStates.q5_document))
async def process_q5_document(message: Message, state: FSMContext):
    """Hujjat seriya raqami"""
    try:
        await state.update_data(document_number=message.text.strip())
        await message.answer(text=TEXTS['q6_achievements'], reply_markup=get_yes_no_keyboard("back_q5"))
        await state.set_state(SurveyStates.q6_achievements)
    except Exception as e:
        logger.error(f"Error in q5: {e}")


# Q6 - Yutuqlar
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q6_achievements))
async def process_q6_achievements(callback: CallbackQuery, state: FSMContext):
    """Yutuqlar bormi"""
    try:
        answer = callback.data.split("_")[1]
        
        if answer == "yes":
            await state.update_data(has_achievements="Ha")
            await callback.message.edit_text(text=TEXTS['q6_achievements_details'], reply_markup=get_back_keyboard("back_q6"))
            await state.set_state(SurveyStates.q6_achievements_details)
        else:
            await state.update_data(has_achievements="Yo'q", achievements="")
            await callback.message.edit_text(text=TEXTS['q7_certificate'], reply_markup=get_yes_no_keyboard("back_q6"))
            await state.set_state(SurveyStates.q7_certificate)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q6: {e}")


# Q6 - Yutuqlar detallari
@router.message(StateFilter(SurveyStates.q6_achievements_details))
async def process_q6_details(message: Message, state: FSMContext):
    """Yutuqlar tafsilotlari"""
    try:
        await state.update_data(achievements=message.text.strip())
        await message.answer(text=TEXTS['q7_certificate'], reply_markup=get_yes_no_keyboard("back_q6"))
        await state.set_state(SurveyStates.q7_certificate)
    except Exception as e:
        logger.error(f"Error in q6 details: {e}")


# Q7 - Sertifikat
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q7_certificate))
async def process_q7_certificate(callback: CallbackQuery, state: FSMContext):
    """Til sertifikati bormi"""
    try:
        answer = callback.data.split("_")[1]
        
        if answer == "yes":
            await state.update_data(has_certificate="Ha")
            await callback.message.edit_text(text=TEXTS['q7_certificate_type'], reply_markup=get_certificate_type_keyboard("back_q7"))
            await state.set_state(SurveyStates.q7_certificate_type)
        else:
            await state.update_data(has_certificate="Yo'q", certificate_type="", certificate_details="", certificate_file="")
            await callback.message.edit_text(text=TEXTS['q9_grant'], reply_markup=get_yes_no_keyboard("back_q7"))
            await state.set_state(SurveyStates.q9_grant)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q7: {e}")


# Q7 - Sertifikat turi
@router.callback_query(F.data.startswith("cert_"), StateFilter(SurveyStates.q7_certificate_type))
async def process_q7_cert_type(callback: CallbackQuery, state: FSMContext):
    """Sertifikat turi"""
    try:
        cert_type = callback.data.replace("cert_", "").upper()
        await state.update_data(certificate_type=cert_type)
        await callback.message.edit_text(text=TEXTS['q7_certificate_details'])
        await state.set_state(SurveyStates.q7_certificate_details)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q7 type: {e}")


# Q7 - Sertifikat detallari
@router.message(StateFilter(SurveyStates.q7_certificate_details))
async def process_q7_cert_details(message: Message, state: FSMContext):
    """Sertifikat ma'lumotlari"""
    try:
        await state.update_data(certificate_details=message.text.strip(), certificate_file="")
        # To'g'ridan-to'g'ri Q9 ga o'tish
        await message.answer(text=TEXTS['q9_grant'], reply_markup=get_yes_no_keyboard("back_q7"))
        await state.set_state(SurveyStates.q9_grant)
    except Exception as e:
        logger.error(f"Error in q7 details: {e}")


# Q9 - Grant
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q9_grant))
async def process_q9_grant(callback: CallbackQuery, state: FSMContext):
    """Grant bormi"""
    try:
        answer = callback.data.split("_")[1]
        
        if answer == "yes":
            await state.update_data(has_grant="Ha")
            await callback.message.edit_text(text=TEXTS['q9_grant_details'], reply_markup=get_back_keyboard("back_q9"))
            await state.set_state(SurveyStates.q9_grant_details)
        else:
            await state.update_data(has_grant="Yo'q", grant_details="")
            await callback.message.edit_text(text=TEXTS['q10_social_protection'], reply_markup=get_yes_no_keyboard("back_q9"))
            await state.set_state(SurveyStates.q10_social_protection)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q9: {e}")


# Q9 - Grant detallari
@router.message(StateFilter(SurveyStates.q9_grant_details))
async def process_q9_details(message: Message, state: FSMContext):
    """Grant tafsilotlari"""
    try:
        await state.update_data(grant_details=message.text.strip())
        await message.answer(text=TEXTS['q10_social_protection'], reply_markup=get_yes_no_keyboard("back_q9"))
        await state.set_state(SurveyStates.q10_social_protection)
    except Exception as e:
        logger.error(f"Error in q9 details: {e}")


# Q10 - Ijtimoiy himoya
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q10_social_protection))
async def process_q10(callback: CallbackQuery, state: FSMContext):
    """Ijtimoiy himoya reestri"""
    try:
        answer = "Ha" if callback.data == "answer_yes" else "Yo'q"
        await state.update_data(social_protection=answer)
        await callback.message.edit_text(text=TEXTS['q11_iron_book'], reply_markup=get_yes_no_keyboard("back_q10"))
        await state.set_state(SurveyStates.q11_iron_book)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q10: {e}")


# Q11 - Temir daftar
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q11_iron_book))
async def process_q11(callback: CallbackQuery, state: FSMContext):
    """Temir daftar"""
    try:
        answer = "Ha" if callback.data == "answer_yes" else "Yo'q"
        await state.update_data(iron_book=answer)
        await callback.message.edit_text(text=TEXTS['q12_youth_book'], reply_markup=get_yes_no_keyboard("back_q11"))
        await state.set_state(SurveyStates.q12_youth_book)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q11: {e}")


# Q12 - Yoshlar daftari
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q12_youth_book))
async def process_q12(callback: CallbackQuery, state: FSMContext):
    """Yoshlar daftari"""
    try:
        answer = "Ha" if callback.data == "answer_yes" else "Yo'q"
        await state.update_data(youth_book=answer)
        # Avval ota hayotdami savolini so'rash
        await callback.message.edit_text(text=TEXTS['q14_father_alive'], reply_markup=get_yes_no_keyboard("back_q12"))
        await state.set_state(SurveyStates.q14_father_alive)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q12: {e}")


# Q14 - Ota hayotdami (avval shu so'raladi)
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q14_father_alive))
async def process_q14(callback: CallbackQuery, state: FSMContext):
    """Ota hayotdami"""
    try:
        answer = callback.data.split("_")[1]
        
        if answer == "yes":
            await state.update_data(father_alive="Ha")
            # Ha bo'lsa - ism so'raladi
            await callback.message.edit_text(text=TEXTS['q13_father_name'], reply_markup=get_back_keyboard("back_q14"))
            await state.set_state(SurveyStates.q13_father_name)
        else:
            # Yo'q bo'lsa - ona hayotdami savoliga o'tish
            await state.update_data(father_alive="Yo'q", father_name="", father_phone="")
            await callback.message.edit_text(text=TEXTS['q16_mother_alive'], reply_markup=get_yes_no_keyboard("back_q14"))
            await state.set_state(SurveyStates.q16_mother_alive)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q14: {e}")


# Q13 - Ota ismi (faqat hayot bo'lsa so'raladi)
@router.message(StateFilter(SurveyStates.q13_father_name))
async def process_q13(message: Message, state: FSMContext):
    """Ota ismi"""
    try:
        await state.update_data(father_name=message.text.strip())
        await message.answer(text=TEXTS['q14_father_phone'], reply_markup=get_back_keyboard("back_q13"))
        await state.set_state(SurveyStates.q14_father_phone)
    except Exception as e:
        logger.error(f"Error in q13: {e}")


# Q14 - Ota telefoni
@router.message(StateFilter(SurveyStates.q14_father_phone))
async def process_q14_phone(message: Message, state: FSMContext):
    """Ota telefoni"""
    try:
        await state.update_data(father_phone=message.text.strip())
        # Ona hayotdami savoliga o'tish
        await message.answer(text=TEXTS['q16_mother_alive'], reply_markup=get_yes_no_keyboard("back_q14_phone"))
        await state.set_state(SurveyStates.q16_mother_alive)
    except Exception as e:
        logger.error(f"Error in q14 phone: {e}")


# Q16 - Ona hayotdami (avval shu so'raladi)
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q16_mother_alive))
async def process_q16(callback: CallbackQuery, state: FSMContext):
    """Ona hayotdami"""
    try:
        answer = callback.data.split("_")[1]
        data = await state.get_data()
        
        if answer == "yes":
            await state.update_data(mother_alive="Ha")
            # Ha bo'lsa - ism so'raladi
            await callback.message.edit_text(text=TEXTS['q15_mother_name'], reply_markup=get_back_keyboard("back_q16"))
            await state.set_state(SurveyStates.q15_mother_name)
        else:
            # Yo'q bo'lsa - keyingi savolga o'tish
            await state.update_data(mother_alive="Yo'q", mother_name="", mother_phone="")
            # Ikkalasi ham vafot etgan bo'lsa, ota-ona birgami savolini o'tkazish
            if data.get('father_alive') == "Yo'q":
                await state.update_data(parents_together="")
                await callback.message.edit_text(text=TEXTS['q18_living_type'], reply_markup=get_living_type_keyboard("back_q16"))
                await state.set_state(SurveyStates.q18_living_type)
            else:
                await callback.message.edit_text(text=TEXTS['q17_parents_together'], reply_markup=get_yes_no_keyboard("back_q16"))
                await state.set_state(SurveyStates.q17_parents_together)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q16: {e}")


# Q15 - Ona ismi (faqat hayot bo'lsa so'raladi)
@router.message(StateFilter(SurveyStates.q15_mother_name))
async def process_q15(message: Message, state: FSMContext):
    """Ona ismi"""
    try:
        await state.update_data(mother_name=message.text.strip())
        await message.answer(text=TEXTS['q16_mother_phone'], reply_markup=get_back_keyboard("back_q15"))
        await state.set_state(SurveyStates.q16_mother_phone)
    except Exception as e:
        logger.error(f"Error in q15: {e}")


# Q16 - Ona telefoni
@router.message(StateFilter(SurveyStates.q16_mother_phone))
async def process_q16_phone(message: Message, state: FSMContext):
    """Ona telefoni"""
    try:
        await state.update_data(mother_phone=message.text.strip())
        
        # Ota ham tirik bo'lsa, ota-ona birgami savoli
        data = await state.get_data()
        if data.get('father_alive') == "Ha":
            await message.answer(text=TEXTS['q17_parents_together'], reply_markup=get_yes_no_keyboard("back_q16_phone"))
            await state.set_state(SurveyStates.q17_parents_together)
        else:
            await state.update_data(parents_together="")
            await message.answer(text=TEXTS['q18_living_type'], reply_markup=get_living_type_keyboard("back_q16_phone"))
            await state.set_state(SurveyStates.q18_living_type)
    except Exception as e:
        logger.error(f"Error in q16 phone: {e}")


# Q17 - Ota-ona birgami
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q17_parents_together))
async def process_q17(callback: CallbackQuery, state: FSMContext):
    """Ota-ona birga yashaydimi"""
    try:
        answer = "Ha" if callback.data == "answer_yes" else "Yo'q"
        await state.update_data(parents_together=answer)
        await callback.message.edit_text(text=TEXTS['q18_living_type'], reply_markup=get_living_type_keyboard("back_q17"))
        await state.set_state(SurveyStates.q18_living_type)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q17: {e}")


# Q18 - Yashash turi
@router.callback_query(F.data.startswith("living_"), StateFilter(SurveyStates.q18_living_type))
async def process_q18(callback: CallbackQuery, state: FSMContext):
    """Yashash turi"""
    try:
        living_type = callback.data.replace("living_", "")
        living_map = {
            'home': "Uydan (oila bilan)",
            'ttj': "TTJ",
            'rent': "Ijaradan",
            'relatives': "Qarindoshlarnikida"
        }
        await state.update_data(living_type=living_map.get(living_type, living_type))
        
        if living_type == "ttj":
            # TTJ tanlagan bo'lsa - qayerdan qatnaydi savoli
            await callback.message.edit_text(
                text="🏢 KUAF ga qayerdan qatnaysiz?",
                reply_markup=get_ttj_type_keyboard("back_q18")
            )
            await state.set_state(SurveyStates.q18_ttj_type)
        elif living_type == "rent":
            # Ijara savollari
            await callback.message.edit_text(text=TEXTS['q19_rent_address'], reply_markup=get_back_keyboard("back_q18"))
            await state.set_state(SurveyStates.q19_rent_address)
        else:
            # Ijaraga oid savollarni o'tkazish
            await state.update_data(rent_address="", rent_location="", rent_owner="", ttj_location="")
            await callback.message.edit_text(text=TEXTS['q22_working'], reply_markup=get_yes_no_keyboard("back_q18"))
            await state.set_state(SurveyStates.q22_working)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q18: {e}")


# Q18 TTJ - Qayerdan qatnaydi
@router.callback_query(F.data.startswith("ttj_"), StateFilter(SurveyStates.q18_ttj_type))
async def process_q18_ttj(callback: CallbackQuery, state: FSMContext):
    """TTJ dan qayerdan qatnaydi"""
    try:
        ttj_type = callback.data.replace("ttj_", "")
        ttj_map = {
            'uydan': "Uydan",
            'jevachi': "Jevachi TTJ dan",
            'kuaf': "KUAF TTJ dan",
            'texnika': "Texnika DXSH dan",
            'kamolot': "Kamolot Ko'cha TTJ dan",
            'family_med': "FAMILY MED TTJ dan",
            'ijara': "Ijaradan (kvartira)"
        }
        await state.update_data(ttj_location=ttj_map.get(ttj_type, ttj_type))
        
        # Ijaraga oid savollarni o'tkazish
        await state.update_data(rent_address="", rent_location="", rent_owner="")
        await callback.message.edit_text(text=TEXTS['q22_working'], reply_markup=get_yes_no_keyboard("back_q18_ttj"))
        await state.set_state(SurveyStates.q22_working)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q18_ttj: {e}")


# Q19 - Ijara manzili
@router.message(StateFilter(SurveyStates.q19_rent_address))
async def process_q19(message: Message, state: FSMContext):
    """Ijara manzili"""
    try:
        await state.update_data(rent_address=message.text.strip())
        await message.answer(text=TEXTS['q20_rent_location'], reply_markup=get_location_keyboard("back_q19"))
        await state.set_state(SurveyStates.q20_rent_location)
    except Exception as e:
        logger.error(f"Error in q19: {e}")


# Q20 - Ijara lokatsiyasi
@router.message(StateFilter(SurveyStates.q20_rent_location))
async def process_q20(message: Message, state: FSMContext):
    """Ijara lokatsiyasi"""
    try:
        # Orqaga tugmasi bosildi
        if message.text == "⬅️ Orqaga":
            await message.answer(text=TEXTS['q19_rent_address'], reply_markup=get_back_keyboard("back_q18"))
            await state.set_state(SurveyStates.q19_rent_address)
            return
        
        if message.location:
            location = f"{message.location.latitude},{message.location.longitude}"
            await state.update_data(rent_location=location)
        elif message.text == "⏭ O'tkazib yuborish":
            await state.update_data(rent_location="")
        else:
            await state.update_data(rent_location=message.text.strip())
        
        await message.answer(text=TEXTS['q21_rent_owner'], reply_markup=get_back_keyboard("back_q20"))
        await state.set_state(SurveyStates.q21_rent_owner)
    except Exception as e:
        logger.error(f"Error in q20: {e}")


# Q21 - Ijara egasi
@router.message(StateFilter(SurveyStates.q21_rent_owner))
async def process_q21(message: Message, state: FSMContext):
    """Ijara egasi"""
    try:
        await state.update_data(rent_owner=message.text.strip())
        await message.answer(text=TEXTS['q22_working'], reply_markup=get_yes_no_keyboard("back_q21"))
        await state.set_state(SurveyStates.q22_working)
    except Exception as e:
        logger.error(f"Error in q21: {e}")


# Q22 - Ishlaysizmi
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q22_working))
async def process_q22(callback: CallbackQuery, state: FSMContext):
    """Ishlaysizmi"""
    try:
        answer = callback.data.split("_")[1]
        
        if answer == "yes":
            await state.update_data(is_working="Ha")
            # Avvalgi savolga qarab back button
            data = await state.get_data()
            living_type = data.get('living_type', '')
            if "Ijaradan" in living_type:
                back_btn = "back_q21"
            elif "TTJ" in living_type:
                back_btn = "back_q18_ttj"
            else:
                back_btn = "back_q18"
            await callback.message.edit_text(text=TEXTS['q23_workplace'], reply_markup=get_back_keyboard(back_btn))
            await state.set_state(SurveyStates.q23_workplace)
        else:
            await state.update_data(is_working="Yo'q", workplace="")
            # Oilalikmisiz savoliga o'tish
            await callback.message.edit_text(text=TEXTS['q24_married'], reply_markup=get_yes_no_keyboard("back_q22"))
            await state.set_state(SurveyStates.q24_married)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q22: {e}")


# Q23 - Ish joyi
@router.message(StateFilter(SurveyStates.q23_workplace))
async def process_q23(message: Message, state: FSMContext):
    """Ish joyi"""
    try:
        await state.update_data(workplace=message.text.strip())
        # Oilalikmisiz savoliga o'tish
        await message.answer(text=TEXTS['q24_married'], reply_markup=get_yes_no_keyboard("back_q23"))
        await state.set_state(SurveyStates.q24_married)
    except Exception as e:
        logger.error(f"Error in q23: {e}")


# Q24 - Oilalikmisiz
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q24_married))
async def process_q24(callback: CallbackQuery, state: FSMContext):
    """Oilalikmisiz"""
    try:
        answer = callback.data.split("_")[1]
        
        if answer == "yes":
            await state.update_data(is_married="Ha")
        else:
            await state.update_data(is_married="Yo'q")
        
        # Q25 - Xorijga chiqish pasporti savoliga o'tish
        await callback.message.edit_text(text=TEXTS['q25_foreign_passport'], reply_markup=get_yes_no_keyboard("back_q24"))
        await state.set_state(SurveyStates.q25_foreign_passport)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q24: {e}")


# Q25 - Xorijga chiqish pasporti
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q25_foreign_passport))
async def process_q25(callback: CallbackQuery, state: FSMContext):
    """Xorijga chiqish pasporti"""
    try:
        answer = callback.data.split("_")[1]
        
        if answer == "yes":
            await state.update_data(has_foreign_passport="Ha")
        else:
            await state.update_data(has_foreign_passport="Yo'q")
        
        # Q26 - Ijtimoiy tarmoqlar savoliga o'tish
        await callback.message.edit_text(text=TEXTS['q26_social_channels'], reply_markup=get_yes_no_keyboard("back_q25"))
        await state.set_state(SurveyStates.q26_social_channels)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q25: {e}")


# Q26 - Ijtimoiy tarmoqlarda kanal/guruh
@router.callback_query(F.data.startswith("answer_"), StateFilter(SurveyStates.q26_social_channels))
async def process_q26(callback: CallbackQuery, state: FSMContext):
    """Ijtimoiy tarmoqlarda kanal/guruh bormi"""
    try:
        answer = callback.data.split("_")[1]
        
        if answer == "yes":
            await state.update_data(has_social_channels="Ha")
            await callback.message.edit_text(text=TEXTS['q26_social_links'], reply_markup=get_back_keyboard("back_q26"))
            await state.set_state(SurveyStates.q26_social_links)
        else:
            await state.update_data(has_social_channels="Yo'q", social_links="")
            # So'rovnomani yakunlash
            await finish_survey(callback.message, state, callback.from_user.id)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in q26: {e}")


# Q26 - Ijtimoiy tarmoq linklari
@router.message(StateFilter(SurveyStates.q26_social_links))
async def process_q26_links(message: Message, state: FSMContext):
    """Ijtimoiy tarmoq linklari"""
    try:
        await state.update_data(social_links=message.text.strip())
        # So'rovnomani yakunlash
        await finish_survey(message, state, message.from_user.id)
    except Exception as e:
        logger.error(f"Error in q26 links: {e}")


# So'rovnomani yakunlash
async def finish_survey(message: Message, state: FSMContext, user_id: int):
    """So'rovnomani saqlash va yakunlash"""
    try:
        data = await state.get_data()
        data['user_id'] = user_id
        
        success = await db.save_survey_response(data)
        
        if success:
            await message.answer(text=TEXTS['survey_completed'], reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer(text=TEXTS['error'])
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error in finish_survey: {e}")
        await message.answer(TEXTS['error'])


# ================= ADMIN HANDLERS =================

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Admin panel"""
    try:
        if not (await is_super_admin(message.from_user.id) or await is_staff_member(message.from_user.id)):
            await message.answer(TEXTS['access_denied'])
            return
        
        await state.clear()
        await message.answer(text=TEXTS['admin_panel'], reply_markup=get_admin_keyboard())
        await state.set_state(AdminStates.main_panel)
    except Exception as e:
        logger.error(f"Error in cmd_admin: {e}")


# Excel Export
@router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery, state: FSMContext):
    """Excel export"""
    try:
        if not (await is_super_admin(callback.from_user.id) or await is_staff_member(callback.from_user.id)):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return
        
        await callback.message.answer("📤 Excel fayl tayyorlanmoqda...")
        
        filepath = await excel_handler.export_survey_responses()
        
        if filepath:
            file = FSInputFile(filepath)
            await callback.message.answer_document(document=file, caption="✅ So'rovnoma natijalari")
            await asyncio.sleep(1)
            os.remove(filepath)
        else:
            await callback.message.answer("❌ Ma'lumot yo'q yoki xatolik yuz berdi")
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in admin_export: {e}")


# Excel Import
@router.callback_query(F.data == "admin_import")
async def admin_import(callback: CallbackQuery, state: FSMContext):
    """Excel import"""
    try:
        if not await is_super_admin(callback.from_user.id):
            await callback.answer("Faqat admin uchun", show_alert=True)
            return
        
        await callback.message.answer("📥 Excel faylni yuboring:")
        await state.set_state(AdminStates.waiting_excel_import)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in admin_import: {e}")


@router.message(StateFilter(AdminStates.waiting_excel_import), F.document)
async def process_excel_import(message: Message, state: FSMContext):
    """Excel import qilish"""
    try:
        if not await is_super_admin(message.from_user.id):
            return
        
        file = await bot.get_file(message.document.file_id)
        file_path = os.path.join(EXCEL_DIR, f"import_{message.from_user.id}_{datetime.now().timestamp()}.xlsx")
        await bot.download_file(file.file_path, file_path)
        
        await message.answer("⏳ Import boshlanmoqda...")
        result = await excel_handler.import_students(file_path)
        
        if result['success']:
            await message.answer(
                f"✅ Import yakunlandi!\n\n"
                f"➕ Qo'shildi: {result['added']}\n"
                f"🔄 Yangilandi: {result['updated']}\n"
                f"⚠️ Xatolar: {len(result['errors'])}"
            )
        else:
            await message.answer(f"❌ Import xatoligi:\n{result['errors'][:5]}")
        
        await state.set_state(AdminStates.main_panel)
    except Exception as e:
        logger.error(f"Error in process_excel_import: {e}")


# Statistika
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, state: FSMContext):
    """Statistika"""
    try:
        stats = await db.get_statistics()
        
        response = "📊 STATISTIKA\n\n"
        response += f"👥 Jami talabalar: {stats['total_students']}\n"
        response += f"✅ To'ldirilgan so'rovnomalar: {stats['completed_surveys']}\n"
        response += f"👨‍💼 Xodimlar: {stats['total_staff']}\n"
        response += f"\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        await callback.message.answer(response)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in admin_stats: {e}")


# So'rovnomalarni tozalash
@router.callback_query(F.data == "admin_clear_surveys")
async def admin_clear_surveys(callback: CallbackQuery, state: FSMContext):
    """So'rovnomalarni tozalash - tasdiqlash so'rash"""
    try:
        if not await is_super_admin(callback.from_user.id):
            await callback.answer("Faqat admin uchun", show_alert=True)
            return
        
        stats = await db.get_statistics()
        count = stats['completed_surveys']
        
        if count == 0:
            await callback.answer("So'rovnomalar mavjud emas", show_alert=True)
            return
        
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data="confirm_clear_yes"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_clear_no")
            ]
        ])
        
        await callback.message.edit_text(
            f"⚠️ DIQQAT!\n\n{count} ta so'rovnoma o'chiriladi.\n\nDavom etasizmi?",
            reply_markup=confirm_keyboard
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in admin_clear_surveys: {e}")


@router.callback_query(F.data == "confirm_clear_yes")
async def confirm_clear_yes(callback: CallbackQuery, state: FSMContext):
    """So'rovnomalarni o'chirishni tasdiqlash"""
    try:
        if not await is_super_admin(callback.from_user.id):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return
        
        count = await db.clear_all_surveys()
        await callback.message.edit_text(f"✅ {count} ta so'rovnoma o'chirildi!")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in confirm_clear_yes: {e}")


@router.callback_query(F.data == "confirm_clear_no")
async def confirm_clear_no(callback: CallbackQuery, state: FSMContext):
    """O'chirishni bekor qilish"""
    try:
        await callback.message.edit_text("❌ O'chirish bekor qilindi.")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in confirm_clear_no: {e}")


# Xodim qo'shish
@router.callback_query(F.data == "admin_add_staff")
async def admin_add_staff(callback: CallbackQuery, state: FSMContext):
    """Xodim qo'shish"""
    try:
        if not await is_super_admin(callback.from_user.id):
            await callback.answer("Faqat admin uchun", show_alert=True)
            return
        
        await callback.message.answer("👤 Xodim Telegram ID sini kiriting:")
        await state.set_state(AdminStates.waiting_staff_id)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error: {e}")


@router.message(StateFilter(AdminStates.waiting_staff_id))
async def process_staff_id(message: Message, state: FSMContext):
    """Xodim ID qabul qilish"""
    try:
        staff_id = int(message.text.strip())
        success = await db.add_staff(staff_id)
        
        if success:
            await message.answer(f"✅ Xodim qo'shildi: {staff_id}")
        else:
            await message.answer("❌ Xatolik yoki allaqachon mavjud")
        
        await state.set_state(AdminStates.main_panel)
        await message.answer(text=TEXTS['admin_panel'], reply_markup=get_admin_keyboard())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID format")
    except Exception as e:
        logger.error(f"Error: {e}")


# Xodim o'chirish
@router.callback_query(F.data == "admin_remove_staff")
async def admin_remove_staff(callback: CallbackQuery, state: FSMContext):
    """Xodim o'chirish"""
    try:
        if not await is_super_admin(callback.from_user.id):
            await callback.answer("Faqat admin uchun", show_alert=True)
            return
        
        await callback.message.answer("👤 O'chiriladigan xodim Telegram ID sini kiriting:")
        await state.set_state(AdminStates.waiting_announcement)  # Vaqtinchalik holat
        await state.update_data(action="remove_staff")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error: {e}")


# E'lon yuborish
@router.callback_query(F.data == "admin_announce")
async def admin_announce(callback: CallbackQuery, state: FSMContext):
    """E'lon yuborish"""
    try:
        if not await is_super_admin(callback.from_user.id):
            await callback.answer("Faqat admin uchun", show_alert=True)
            return
        
        await callback.message.answer("📢 E'lon matnini yuboring:")
        await state.set_state(AdminStates.waiting_announcement)
        await state.update_data(action="announce")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error: {e}")


@router.message(StateFilter(AdminStates.waiting_announcement))
async def process_announcement(message: Message, state: FSMContext):
    """E'lon yoki xodim o'chirish"""
    try:
        data = await state.get_data()
        action = data.get('action', 'announce')
        
        if action == "remove_staff":
            # Xodim o'chirish
            staff_id = int(message.text.strip())
            success = await db.remove_staff(staff_id)
            
            if success:
                await message.answer(f"✅ Xodim o'chirildi: {staff_id}")
            else:
                await message.answer("❌ Xodim topilmadi")
        else:
            # E'lon yuborish
            announcement = message.text.strip()
            # TODO: Barcha foydalanuvchilarga yuborish
            await message.answer(f"✅ E'lon saqlandi:\n\n{announcement}\n\n(Hozircha faqat saqlandi, yuborish funksiyasi keyinroq qo'shiladi)")
        
        await state.set_state(AdminStates.main_panel)
        await message.answer(text=TEXTS['admin_panel'], reply_markup=get_admin_keyboard())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID format")
    except Exception as e:
        logger.error(f"Error: {e}")


# ================= MAIN =================
async def main():
    """Botni ishga tushirish"""
    try:
        await db.init_db()
        logger.info("Database initialized")
        
        os.makedirs(EXCEL_DIR, exist_ok=True)
        os.makedirs(EXPORT_DIR, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        logger.info("Bot started")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(main())
