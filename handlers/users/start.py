from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from states.states import FillStars
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import CallbackQuery
from loader import dp, bot
import logging
import datetime



ADMIN_ID = 7174828209
CHANNEL_USERNAME = "@N1TDMUZB"
CHANNEL_USERNAME1 = "@NitroDevChannel"
CHANNEL_USERNAME2 = "@python_programmerr"


users_data = {}  # user_id: {'stars': int, 'referrals': int, 'last_bonus': date}
pending_refs = {}


# Start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    # Obuna tekshiruvi — ikkala kanal uchun
    not_subscribed = False
    for channel in [CHANNEL_USERNAME, CHANNEL_USERNAME1, CHANNEL_USERNAME2]:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_subscribed = True
                break
        except:
            not_subscribed = True
            break

    if not_subscribed:
        if args.isdigit():
            pending_refs[user_id] = int(args)

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("🔔 Obuna bo'lish ", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            InlineKeyboardButton("🔔 Obuna bo'lish ", url=f"https://t.me/{CHANNEL_USERNAME1[1:]}"),
            InlineKeyboardButton("🔔 Obuna bo'lish ", url=f"https://t.me/{CHANNEL_USERNAME2[1:]}"),
            InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
        )
        await message.answer("👋 Botdan foydalanish uchun kanallarga obuna bo‘ling!", reply_markup=keyboard)
        return

    # Obuna bo‘lgan — davom ettiramiz
    await register_user(message, int(args) if args.isdigit() else None)



@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    not_subscribed = False
    for channel in [CHANNEL_USERNAME, CHANNEL_USERNAME1, CHANNEL_USERNAME2 ]:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed = True
                break
        except:
            not_subscribed = True
            break

    if not_subscribed:
        await call.answer("❌ Hali ham  kanallarga obuna bo‘lmagansiz!", show_alert=True)
        return

    await call.message.edit_text("✅ Obuna muvaffaqiyatli tasdiqlandi!")
    args = pending_refs.pop(user_id, None)
    await register_user(call.message, args)



async def register_user(message, referrer_id=None):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"stars": 0, "referrals": 0, "last_bonus": None}

        # REFERAL bo'lgan holatda
        if referrer_id and referrer_id != user_id and referrer_id in users_data:
            users_data[referrer_id]["stars"] += 3
            users_data[referrer_id]["referrals"] += 1

            # Referal yuborganga habar yuborish
            try:
                await bot.send_message(
                    referrer_id,
                    f"🆕 Sizga yangi referal keldi!\n"
                    f"💰 Balansingizga 3⭐ qo‘shildi.\n"
                    f"🔄 Yangi balans: {users_data[referrer_id]['stars']}⭐"
                )
            except:
                pass  # Bloklangan yoki xatolik bo'lsa — jim o'tiladi
    # Foydalanuvchiga menyuni yuborish
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🎁 Ежедневный бонус", "👥 Ваша ссылка")
    keyboard.add("👤 Профиль", "💸 Вывод")

    # Faqat ADMIN uchun tugma
    if message.from_user.id == ADMIN_ID:
        keyboard.add("⭐ Yulduz to‘ldirish")

    await message.answer("👋 Xush kelibsiz! Quyidagi menyudan foydalaning:", reply_markup=keyboard)


# Daily bonus
@dp.message_handler(lambda m: m.text == "🎁 Ежедневный бонус")
async def bonus(message: types.Message):
    user_id = message.from_user.id
    today = datetime.date.today()

    user = users_data.get(user_id)
    if user is None:
        return await message.answer("❌ Ro‘yxatdan o‘tmagansiz. /start bosing.")

    if user["last_bonus"] == today:
        await message.answer("📅 Siz bugun bonusni olib bo‘lgansiz!")
    else:
        user["stars"] += 1
        user["last_bonus"] = today
        await message.answer("⭐ Sizga 1 ta yulduz berildi! Ertaga yana keling.")


# Profil
@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def profil(message: types.Message):
    user = users_data.get(message.from_user.id)
    if not user:
        return await message.answer("Siz ro‘yxatdan o‘tmagansiz.")

    await message.answer(f"""
🧑‍💻 Profilingiz:

⭐ Yulduzlar: {user['stars']}
👥 Referallar: {user['referrals']}
""")


# Referal
@dp.message_handler(lambda m: m.text == "👥 Ваша ссылка")
async def ref_link(message: types.Message):
    user_id = message.from_user.id
    user = users_data.get(user_id)
    if not user:
        return await message.answer("❌ Ro‘yxatdan o‘tmagansiz.")

    await message.answer(f"""
👥 Do‘stlaringizni taklif qiling!

🔗 Sizning havolangiz:
https://t.me/{(await bot.get_me()).username}?start={user_id}

💰 Har bir do‘st uchun: 3⭐
Takliflar soni: {user["referrals"]}
""")


# Вывод
@dp.message_handler(lambda m: m.text == "💸 Вывод")
async def vyvod(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("💳 15⭐", "💳 25⭐", "💳 50⭐", "💳 100⭐")
    keyboard.add("🔙 Orqaga")
    await message.answer("💸 Nechta yulduzni yechmoqchisiz?", reply_markup=keyboard)


from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@dp.message_handler(lambda m: m.text in ["💳 15⭐", "💳 25⭐", "💳 50⭐", "💳 100⭐"])
async def handle_withdraw(message: types.Message):
    user_id = message.from_user.id
    user = users_data.get(user_id)
    if not user:
        return await message.answer("Ro‘yxatdan o‘tmagansiz.")

    amount = int(message.text.replace("💳 ", "").replace("⭐", ""))
    if user["stars"] >= amount:
        user["stars"] -= amount
        await message.answer(f"✅ {amount}⭐ yulduz uchun yechib olish so‘rovingiz yuborildi!")

        # Adminga xabar yuborish
        username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
        admin_msg = (
            f"💸 Yangi yechib olish so‘rovi!\n"
            f"👤 Foydalanuvchi: {username}\n"
            f"🆔 ID: {user_id}\n"
            f"⭐ Miqdor: {amount}\n"
        )

        # Tugma: To‘landi
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ To‘landi", callback_data=f"paid:{user_id}"))

        await bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)

    else:
        await message.answer(f"❌ Yetarli yulduz yo‘q. Sizda: {user['stars']}⭐")


@dp.callback_query_handler(lambda c: c.data.startswith("paid:"))
async def paid_handler(call: types.CallbackQuery):
    user_id = int(call.data.split(":")[1])

    try:
        await bot.send_message(user_id, "✅ Sizning yechib olish so‘rovingiz to‘landi! ✅")
        await call.message.edit_reply_markup()  # Tugmani olib tashlash
        await call.answer("Foydalanuvchiga to‘langanligi haqida xabar yuborildi.")
    except:
        await call.answer("❌ Foydalanuvchiga xabar yuborib bo‘lmadi!", show_alert=True)



# Orqaga
@dp.message_handler(lambda m: m.text == "🔙 Orqaga")
async def back_menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🎁 Ежедневный бонус", "👥 Ваша ссылка")
    keyboard.add("👤 Профиль", "💸 Вывод")
    await message.answer("⬅️ Asosiy menyuga qaytdingiz.", reply_markup=keyboard)

@dp.message_handler(lambda m: m.text == "⭐ Yulduz to‘ldirish")
async def start_fill_stars(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🆔 Qaysi foydalanuvchining ID sini kiriting:")
    await FillStars.waiting_for_user_id.set()


@dp.message_handler(state=FillStars.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, to‘g‘ri raqamli ID kiriting.")

    await state.update_data(user_id=int(message.text))
    await message.answer("⭐ Nechta yulduz qo‘shmoqchisiz?")
    await FillStars.waiting_for_amount.set()


@dp.message_handler(state=FillStars.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Faqat raqam kiriting.")

    data = await state.get_data()
    user_id = data["user_id"]
    amount = int(message.text)

    # Foydalanuvchini tekshiramiz
    if user_id not in users_data:
        users_data[user_id] = {"stars": 0, "referrals": 0, "last_bonus": None}

    users_data[user_id]["stars"] += amount
    await message.answer(f"✅ {user_id} foydalanuvchiga {amount}⭐ qo‘shildi!")

    try:
        await bot.send_message(user_id,
                               f"🎁 Sizning balansingizga {amount}⭐ qo‘shildi!\n🔄 Yangi balans: {users_data[user_id]['stars']}⭐")
    except:
        await message.answer("⚠️ Foydalanuvchiga xabar yuborib bo‘lmadi (bloklangan bo‘lishi mumkin).")

    await state.finish()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
