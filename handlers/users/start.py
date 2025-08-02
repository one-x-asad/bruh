from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from states.states import FillStars
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from loader import dp, bot
import logging
import datetime

ADMIN_ID = 7174828209
CHANNEL_USERNAME = "@N1TDMUZB"
CHANNEL_USERNAME1 = "@NitroDevChannel"
CHANNEL_USERNAME2 = "@python_programmerr"

users_data = {}
pending_refs = {}

# Start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

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
            InlineKeyboardButton("🔔 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            InlineKeyboardButton("🔔 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME1[1:]}"),
            InlineKeyboardButton("🔔 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME2[1:]}"),
            InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")
        )
        await message.answer("👋 Чтобы использовать бота, подпишитесь на все каналы!", reply_markup=keyboard)
        return

    await register_user(message, int(args) if args.isdigit() else None)

@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    not_subscribed = False
    for channel in [CHANNEL_USERNAME, CHANNEL_USERNAME1, CHANNEL_USERNAME2]:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed = True
                break
        except:
            not_subscribed = True
            break

    if not_subscribed:
        await call.answer("❌ Вы ещё не подписались на все каналы!", show_alert=True)
        return

    await call.message.edit_text("✅ Подписка успешно подтверждена!")
    args = pending_refs.pop(user_id, None)
    await register_user(call.message, args)

async def register_user(message, referrer_id=None):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"stars": 0, "referrals": 0, "last_bonus": None}

        if referrer_id and referrer_id != user_id and referrer_id in users_data:
            users_data[referrer_id]["stars"] += 3
            users_data[referrer_id]["referrals"] += 1

            try:
                await bot.send_message(
                    referrer_id,
                    f"🆕 У вас новый реферал!\n"
                    f"💰 На ваш баланс начислено 3⭐.\n"
                    f"🔄 Новый баланс: {users_data[referrer_id]['stars']}⭐"
                )
            except:
                pass

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🎁 Ежедневный бонус", "👥 Ваша ссылка")
    keyboard.add("👤 Профиль", "💸 Вывод")

    if message.from_user.id == ADMIN_ID:
        keyboard.add("⭐ Начислить звезды")

    await message.answer("👋 Добро пожаловать! Выберите пункт меню:", reply_markup=keyboard)

@dp.message_handler(lambda m: m.text == "🎁 Ежедневный бонус")
async def bonus(message: types.Message):
    user_id = message.from_user.id
    today = datetime.date.today()
    user = users_data.get(user_id)
    if user is None:
        return await message.answer("❌ Вы не зарегистрированы. Нажмите /start.")

    if user["last_bonus"] == today:
        await message.answer("📅 Вы уже получили бонус сегодня!")
    else:
        user["stars"] += 1
        user["last_bonus"] = today
        await message.answer("⭐ Вам начислена 1 звезда! Приходите завтра за следующей.")

@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def profil(message: types.Message):
    user = users_data.get(message.from_user.id)
    if not user:
        return await message.answer("❌ Вы не зарегистрированы.")
    await message.answer(f"""
🧑‍💻 Ваш профиль:

⭐ Звезды: {user['stars']}
👥 Рефералы: {user['referrals']}
""")

@dp.message_handler(lambda m: m.text == "👥 Ваша ссылка")
async def ref_link(message: types.Message):
    user_id = message.from_user.id
    user = users_data.get(user_id)
    if not user:
        return await message.answer("❌ Вы не зарегистрированы.")

    await message.answer(f"""
👥 Приглашайте друзей!

🔗 Ваша реферальная ссылка:
https://t.me/{(await bot.get_me()).username}?start={user_id}

💰 За каждого друга: 3⭐
Общее количество: {user["referrals"]}
""")

@dp.message_handler(lambda m: m.text == "💸 Вывод")
async def vyvod(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("💳 15⭐", "💳 25⭐", "💳 50⭐", "💳 100⭐")
    keyboard.add("🔙 Назад")
    await message.answer("💸 Выберите сумму для вывода:", reply_markup=keyboard)

@dp.message_handler(lambda m: m.text in ["💳 15⭐", "💳 25⭐", "💳 50⭐", "💳 100⭐"])
async def handle_withdraw(message: types.Message):
    user_id = message.from_user.id
    user = users_data.get(user_id)
    if not user:
        return await message.answer("❌ Вы не зарегистрированы.")

    amount = int(message.text.replace("💳 ", "").replace("⭐", ""))
    if user["stars"] >= amount:
        user["stars"] -= amount
        await message.answer(f"✅ Запрос на вывод {amount}⭐ успешно отправлен!")

        username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
        admin_msg = (
            f"💸 Новый запрос на вывод!\n"
            f"👤 Пользователь: {username}\n"
            f"🆔 ID: {user_id}\n"
            f"⭐ Сумма: {amount}\n"
        )

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Выплачено", callback_data=f"paid:{user_id}"))

        await bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
    else:
        await message.answer(f"❌ Недостаточно звёзд. У вас: {user['stars']}⭐")

@dp.callback_query_handler(lambda c: c.data.startswith("paid:"))
async def paid_handler(call: types.CallbackQuery):
    user_id = int(call.data.split(":")[1])
    try:
        await bot.send_message(user_id, "✅ Ваш запрос на вывод был выполнен!")
        await call.message.edit_reply_markup()
        await call.answer("Пользователь уведомлен о выплате.")
    except:
        await call.answer("❌ Не удалось отправить сообщение пользователю!", show_alert=True)

@dp.message_handler(lambda m: m.text == "🔙 Назад")
async def back_menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🎁 Ежедневный бонус", "👥 Ваша ссылка")
    keyboard.add("👤 Профиль", "💸 Вывод")
    await message.answer("⬅️ Вы вернулись в главное меню.", reply_markup=keyboard)

@dp.message_handler(lambda m: m.text == "⭐ Начислить звезды")
async def start_fill_stars(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🆔 Введите ID пользователя:")
    await FillStars.waiting_for_user_id.set()

@dp.message_handler(state=FillStars.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Введите корректный числовой ID.")
    await state.update_data(user_id=int(message.text))
    await message.answer("⭐ Сколько звёзд добавить?")
    await FillStars.waiting_for_amount.set()

@dp.message_handler(state=FillStars.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Введите только число.")
    data = await state.get_data()
    user_id = data["user_id"]
    amount = int(message.text)

    if user_id not in users_data:
        users_data[user_id] = {"stars": 0, "referrals": 0, "last_bonus": None}

    users_data[user_id]["stars"] += amount
    await message.answer(f"✅ Пользователю {user_id} добавлено {amount}⭐")

    try:
        await bot.send_message(
            user_id,
            f"🎁 Вам начислено {amount}⭐\n🔄 Новый баланс: {users_data[user_id]['stars']}⭐"
        )
    except:
        await message.answer("⚠️ Не удалось отправить сообщение пользователю (возможно, заблокировал бота).")

    await state.finish()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
