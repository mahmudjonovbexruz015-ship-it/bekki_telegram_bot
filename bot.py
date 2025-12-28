from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
import sqlite3
import re

# ================= CONFIG =================
TOKEN = "8340831049:AAGqteRjvR01aC8S6QQAaf_qvk7s3gUk9yA"
ADMIN_ID = 5384141707
STREAM_LINK = "https://youtube.com/@bekki_pubgm1?si=aBCJBfsJmK623huC"

# ================= BOT =================
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# ================= DATABASE =================
db = sqlite3.connect("users.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    invited_by INTEGER,
    approved INTEGER DEFAULT 0,
    order_number INTEGER,
    contact TEXT,
    referrals INTEGER DEFAULT 0,
    bonus_numbers INTEGER DEFAULT 0
)
""")
db.commit()

def next_order():
    cursor.execute("SELECT MAX(order_number) FROM users")
    r = cursor.fetchone()[0]
    return 1 if r is None else r + 1

# ================= CHANNELS =================
channels = [
    ("1-KANAL", "https://t.me/X4_PUBGM"),
    ("2-KANAL", "https://t.me/sertturner"),
    ("3-KANAL", "https://t.me/BEKKI_PUBGM"),
    ("4-KANAL", "https://youtube.com/@paxan_030"),
    ("5-KANAL", "https://youtube.com/@bekki_pubgm1"),
    ("6-KANAL", "https://www.youtube.com/@ZIYO5K_PUBGM"),
]

def channels_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    for name, link in channels:
        kb.add(InlineKeyboardButton(name, url=link))
    kb.add(InlineKeyboardButton("✅ OBUNA BO‘LDIM", callback_data="sub_done"))
    return kb

# ================= MENU =================
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("📜 KONKURS SHARTLARI")
menu.add("📆 KONKURS TUGASH SANASI")
menu.add("🔥 YUTISH IMKONINI OSHIRISH")
menu.add("🔢 MENING TARTIB RAQAMIM")

# ================= START =================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id

    args = message.get_args()
    invited_by = int(args) if args.isdigit() and int(args) != user_id else None

    cursor.execute("SELECT approved FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if row and row[0] == 1:
        await message.answer(
            "🎉 Siz allaqachon konkurs qatnashchisiz!\n\n"
            "⬇️ Quyidagi menyudan foydalaning",
            reply_markup=menu
        )
        return

    cursor.execute("INSERT OR IGNORE INTO users (user_id, invited_by) VALUES (?,?)",
                   (user_id, invited_by))
    db.commit()

    await message.answer(
        "🎯 <b>KONKURSDA QATNASHISH UCHUN</b>\n\n"
        "Quyidagi kanallarga obuna bo‘ling 👇",
        reply_markup=channels_kb()
    )

# ================= SUB BUTTON =================
@dp.callback_query_handler(text="sub_done")
async def sub_done(call: types.CallbackQuery):
    await call.message.answer(
        "📸 Iltimos, obuna bo‘lganingizni tasdiqlovchi "
        "<b>SKRINSHOT</b> yuboring.\n\n"
        "❗️Faqat rasm qabul qilinadi!"
    )

# ================= SCREENSHOT =================
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def screenshot(message: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ O‘TKAZILSIN", callback_data=f"ok_{message.from_user.id}"),
        InlineKeyboardButton("❌ O‘TKAZILMASIN", callback_data=f"no_{message.from_user.id}")
    )

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"👤 User ID: {message.from_user.id}",
        reply_markup=kb
    )

# ================= ADMIN DECISION =================
@dp.callback_query_handler(lambda c: c.data.startswith("ok_"))
async def approve(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📲 TELEFON RAQAMNI YUBORISH", request_contact=True))

    await bot.send_message(
        user_id,
        "🎉 <b>Tabriklaymiz!</b>\n\n"
        "Siz konkursga <b>o‘tkazildingiz</b> ✅\n\n"
        "📲 Iltimos, telefon raqamingizni yuboring",
        reply_markup=kb
    )
    await call.message.edit_caption("✅ O‘TKAZILDI")

@dp.callback_query_handler(lambda c: c.data.startswith("no_"))
async def reject(call: types.CallbackQuery):
    await call.message.edit_caption("❌ RAD ETILDI")

# ================= CONTACT (FINAL ENTRY) =================
@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact(message: types.Message):
    user_id = message.from_user.id

    cursor.execute("SELECT approved, invited_by FROM users WHERE user_id=?", (user_id,))
    approved, inviter = cursor.fetchone()

    if approved == 1:
        await message.answer("ℹ️ Siz allaqachon ro‘yxatdan o‘tgansiz", reply_markup=menu)
        return

    order = next_order()

    cursor.execute("""
        UPDATE users SET approved=1, contact=?, order_number=?
        WHERE user_id=?
    """, (message.contact.phone_number, order, user_id))
    db.commit()

    # ===== REFERAL (TO‘G‘RI JOY) =====
    if inviter:
        cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (inviter,))
        cursor.execute("SELECT referrals, bonus_numbers FROM users WHERE user_id=?", (inviter,))
        refs, bonus = cursor.fetchone()

        if refs % 2 == 0:
            cursor.execute("UPDATE users SET bonus_numbers = bonus_numbers + 1 WHERE user_id=?", (inviter,))
            db.commit()
            await bot.send_message(
                inviter,
                "🎉 <b>Tabriklaymiz!</b>\n\n"
                "Siz 2 ta do‘st taklif qildingiz!\n"
                "➕ Sizga 1 ta qo‘shimcha tartib raqam berildi!"
            )
        else:
            await bot.send_message(
                inviter,
                f"👥 Siz orqali 1 kishi konkursga qo‘shildi!\n"
                f"📊 Jami referallar: {refs}\n\n"
                "⏳ Yana 1 ta bo‘lsa — bonus raqam olasiz!"
            )

    await message.answer(
        f"🎉 <b>Siz konkurs qatnashchisiga aylandingiz!</b>\n\n"
        f"🆔 Tartib raqamingiz: <b>{order}</b>\n\n"
        f"🎥 G‘oliblar YouTube strimda:\n{STREAM_LINK}",
        reply_markup=menu
    )

# ================= MENU HANDLERS =================
@dp.message_handler(text="📜 KONKURS SHARTLARI")
async def rules(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    for name, link in channels:
        kb.add(InlineKeyboardButton(name, url=link))

    await message.answer(
        "📜 <b>KONKURS SHARTLARI</b>\n\n"
        "• Kanallardan chiqib ketsangiz — yutuq bekor qilinadi\n"
        "• G‘olib strimda aniqlanadi\n"
        "• Admin qarori yakuniy\n\n"
        "⬇️ <b>OBUNA BO‘LISH KERAK BO‘LGAN KANALLAR:</b>",
        reply_markup=kb
    )

@dp.message_handler(text="📆 KONKURS TUGASH SANASI")
async def date(message: types.Message):
    await message.answer(
        "📆 <b>Konkurs 4-yanvar kuni tugaydi</b> 🔥\n\n"
        "🏆 G‘oliblar YouTube strimda aniqlanadi:\n"
        f"{STREAM_LINK}"
    )

@dp.message_handler(text="🔥 YUTISH IMKONINI OSHIRISH")
async def referral(message: types.Message):
    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (message.from_user.id,))
    refs = cursor.fetchone()[0]

    link = f"https://t.me/BEKKI_SHERTOY_KONKURSbot?start={message.from_user.id}"

    await message.answer(
        "🔥 <b>YUTISH IMKONINI OSHIRISH</b>\n\n"
        "👥 Har 2 ta do‘st uchun +1 qo‘shimcha raqam\n\n"
        f"📊 Sizning referallaringiz: <b>{refs}</b>\n\n"
        f"🔗 Referal linkingiz:\n{link}"
    )

@dp.message_handler(text="🔢 MENING TARTIB RAQAMIM")
async def my_number(message: types.Message):
    cursor.execute("""
        SELECT order_number, referrals, bonus_numbers
        FROM users WHERE user_id=?
    """, (message.from_user.id,))
    o, r, b = cursor.fetchone()

    await message.answer(
        f"🆔 Asosiy tartib raqam: <b>{o}</b>\n"
        f"➕ Bonus raqamlar: <b>{b}</b>\n"
        f"👥 Referallar: <b>{r}</b>"
    )

# ================= WINNER =================
@dp.message_handler(commands=["winner"])
async def winner(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.get_args()
    if not args.isdigit():
        await message.answer("❗️ /winner 123 ko‘rinishida yozing")
        return

    num = int(args)
    cursor.execute("""
        SELECT user_id, contact FROM users
        WHERE order_number=? AND approved=1
    """, (num,))
    r = cursor.fetchone()

    if not r:
        await message.answer("❌ Bunday tartib raqam yo‘q")
        return

    uid, phone = r
    await message.answer(
        "🏆 <b>G‘OLIB MA’LUMOTLARI</b>\n\n"
        f"🆔 Tartib raqam: {num}\n"
        f"👤 User ID: {uid}\n"
        f"📞 Telefon: {phone}\n"
        f"🔗 Profil: https://t.me/user?id={uid}"
    )

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
