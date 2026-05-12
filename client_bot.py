import asyncio
import os
import uuid
import random
from urllib.parse import quote

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from py3xui import AsyncApi, Client
from dotenv import load_dotenv

load_dotenv()

# --- Боты ---
BOT_TOKEN        = os.getenv("CLIENT_BOT_TOKEN")
ADMIN_BOT_TOKEN  = os.getenv("ADMIN_BOT_TOKEN")

bot       = AsyncTeleBot(BOT_TOKEN)       # клиентский бот
admin_bot = AsyncTeleBot(ADMIN_BOT_TOKEN) # пишет от имени админ-бота

# --- API серверов ---
api1 = AsyncApi(os.getenv("XUI_URL_1"), os.getenv("XUI_USER_1"), os.getenv("XUI_PASS_1"), use_tls_verify=False)
api2 = AsyncApi(os.getenv("XUI_URL_2"), os.getenv("XUI_USER_2"), os.getenv("XUI_PASS_2"), use_tls_verify=False)

# --- Данные inbound ---
INBOUND_DATA_1 = {
    "port":      os.getenv("SERVER_PORT_1", "443"),
    "server_ip": os.getenv("SERVER_IP_1"),
}
INBOUND_DATA_2 = {
    "port":      os.getenv("SERVER_PORT_2", "32739"),
    "server_ip": os.getenv("SERVER_IP_2"),
}

# ID администраторов
ADMIN_IDS = list(map(int, os.getenv("ALLOWED_IDS", "").split(","))) if os.getenv("ALLOWED_IDS") else []

# admin_chat_id -> client_id, ожидающих выбора сервера
PENDING_APPROVALS = {}


# --- Хэндлеры клиентского бота ---
@bot.message_handler(commands=["start"])
async def hello(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Получить доступ", callback_data="acces_button"),
        types.InlineKeyboardButton("Справочник",      callback_data="guide_button"),
    )
    await bot.send_message(
        message.chat.id,
        "👋 *Добро пожаловать!*\n\n"
        "🔐 Это бот для получения доступа к *VPN-сервису*.\n\n"
        "📋 *Как это работает:*\n"
        "├ Нажми «Получить доступ»\n"
        "├ Свяжись с администратором\n"
        "├ После оплаты получишь персональную ссылку\n"
        "└ Подключайся и пользуйся!\n\n"
        "⬇️ Выбери действие:",
        parse_mode="Markdown",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: True)
async def callback1(call):
    if call.data == "acces_button":
        admin_id = random.choice(ADMIN_IDS) if ADMIN_IDS else None
        admin_us = f"id {admin_id}"  # замени на реальные username в .env или хардкодом

        acces_markup = types.InlineKeyboardMarkup()
        acces_markup.add(types.InlineKeyboardButton("Назад", callback_data="start"))

        user_id  = call.from_user.id
        username = call.from_user.username or call.from_user.first_name

        await bot.edit_message_text(
            f"📩 Напиши администратору: <b>@{admin_us}</b>\n\n"
            f"После оплаты он пришлёт тебе ссылку для подключения.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=acces_markup,
        )

        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton("✅ Оплата подтверждена!", callback_data=f"admin_acces_{user_id}")
        )
        await admin_bot.send_message(
            admin_id,
            f"🔔 <b>Новый клиент хочет доступ!</b>\n\n"
            f"👤 Пользователь: @{username}\n"
            f"🆔 ID: <code>{user_id}</code>",
            parse_mode="HTML",
            reply_markup=admin_markup,
        )

    elif call.data == "guide_button":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📱 Установка и подключение", callback_data="guide_install"),
            types.InlineKeyboardButton("❓ Частые вопросы",           callback_data="guide_faq"),
            types.InlineKeyboardButton("📞 Поддержка",                callback_data="guide_support"),
            types.InlineKeyboardButton("◀️ Назад",                    callback_data="start"),
        )
        await bot.edit_message_text(
            "🌿 *Справочник*\n\nВыбери раздел:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup,
        )

    elif call.data == "guide_install":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="guide_button"))
        await bot.edit_message_text(
            "📱 *Установка и подключение*\n\n"
            "1️⃣ Скачай приложение:\n"
            "├ *iOS / Mac* — V2Box (App Store)\n"
            "├ *Android* — V2Box или NekoBox (Play Market)\n"
            "└ *Windows* — Hiddify (GitHub)\n\n"
            "2️⃣ Скопируй свой ключ `vless://...`\n"
            "3️⃣ В приложении нажми *«+»* → *«Из буфера»*\n"
            "4️⃣ Нажми *«Подключить»* ✅\n\n"
            "⚠️ Ключ персональный — не передавай другим.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup,
        )

    elif call.data == "guide_faq":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="guide_button"))
        await bot.edit_message_text(
            "❓ *Частые вопросы*\n\n"
            "⚡ *Не подключается?*\n"
            "Перезапусти приложение, удали конфиг и добавь ключ заново.\n\n"
            "🐢 *Медленно работает?*\n"
            "Попробуй другой сервер или перезапусти приложение.\n\n"
            "📵 *Не грузятся фото в TG?*\n"
            "Отключи прокси в настройках Telegram → перезапусти.\n\n"
            "🔑 *Нужен новый ключ?*\n"
            "Нажми «Получить доступ» на главном экране и свяжись с админом.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup,
        )

    elif call.data == "guide_support":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="guide_button"))
        await bot.edit_message_text(
            "📞 *Поддержка*\n\n"
            "Пиши нам — всегда ответим 💚\n\n"
            "📢 Новости и анонсы в нашем канале.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup,
        )

    elif call.data == "start":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Получить доступ", callback_data="acces_button"),
            types.InlineKeyboardButton("Справочник",      callback_data="guide_button"),
        )
        await bot.edit_message_text(
            "👋 *Добро пожаловать!*\n\n"
            "🔐 Это бот для получения доступа к *VPN-сервису*.\n\n"
            "📋 *Как это работает:*\n"
            "├ Нажми «Получить доступ»\n"
            "├ Свяжись с администратором\n"
            "├ После оплаты получишь персональную ссылку\n"
            "└ Подключайся и пользуйся!\n\n"
            "⬇️ Выбери действие:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup,
        )


# --- Хэндлеры админ-бота (встроен в client_bot) ---
@admin_bot.callback_query_handler(func=lambda call: True)
async def admincallback1(call):
    if call.data.startswith("admin_acces_"):
        client_id = int(call.data.split("_")[-1])
        PENDING_APPROVALS[call.message.chat.id] = client_id

        await admin_bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None,
        )
        await admin_bot.answer_callback_query(call.id, "Выбери сервер")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🇩🇪 Германия"), types.KeyboardButton("🇳🇱 Нидерланды"))
        await admin_bot.send_message(
            call.message.chat.id,
            f"🖥 <b>Выбери сервер для клиента</b> <code>{client_id}</code>:",
            parse_mode="HTML",
            reply_markup=markup,
        )


@admin_bot.message_handler(func=lambda m: m.chat.id in PENDING_APPROVALS)
async def handle_server_choice(message):
    admin_chat_id = message.chat.id
    client_id     = PENDING_APPROVALS.pop(admin_chat_id)
    client_email  = f"user_{client_id}"
    remove_markup = types.ReplyKeyboardRemove()

    if message.text == "🇩🇪 Германия":
        result = await create_link(client_email, api1, INBOUND_DATA_1, inbound_id=1)
    elif message.text == "🇳🇱 Нидерланды":
        result = await create_link(client_email, api2, INBOUND_DATA_2, inbound_id=1)
    else:
        await admin_bot.send_message(admin_chat_id, "⚠️ Неверный выбор, попробуй ещё раз", reply_markup=remove_markup)
        return

    await admin_bot.send_message(
        admin_chat_id,
        "✅ *Готово!* Ссылка отправлена клиенту." if result.get("success") else f"❌ *Ошибка:* {result.get('error')}",
        parse_mode="Markdown",
        reply_markup=remove_markup,
    )

    if result.get("success"):
        text = (
            f"✅ *Оплата подтверждена!*\n\n"
            f"🔐 Твоя персональная ссылка для подключения:\n\n"
            f"`{result['link']}`\n\n"
            f"📱 Скопируй ссылку и добавь в приложение."
        )
    else:
        text = f"✅ *Оплата подтверждена!*\n\n⚠️ Ошибка генерации ссылки: {result.get('error')}"

    await bot.send_message(client_id, text, parse_mode="Markdown")


# --- Генерация VLESS ссылки ---
async def create_link(client_email: str, api_instance, inbound_data: dict, inbound_id: int = 1, flow: str = "xtls-rprx-vision"):
    try:
        await api_instance.login()
        inbound = await api_instance.inbound.get_by_id(inbound_id)

        if not inbound:
            return {"error": f"Inbound {inbound_id} не найден"}

        for client in inbound.settings.clients:
            if client.email == client_email:
                return {"error": f"Клиент '{client_email}' уже существует"}

        client_id  = str(uuid.uuid4())
        new_client = Client(id=client_id, email=client_email, enable=True, flow=flow)
        inbound.settings.clients.append(new_client)
        await api_instance.inbound.update(inbound_id, inbound)

        rs  = inbound.stream_settings.reality_settings
        pbk = rs["settings"]["publicKey"]
        fp  = rs["settings"]["fingerprint"]
        pqv = rs["settings"].get("mldsa65Verify", "")
        spx = rs["settings"].get("spiderX", "/")
        sni = rs["target"].split(":")[0]
        sid = rs["shortIds"][0]

        link = (
            f"vless://{client_id}@{inbound_data['server_ip']}:{inbound_data['port']}"
            f"?type=tcp&encryption=none&security=reality"
            f"&pbk={pbk}&fp={fp}&sni={sni}&sid={sid}"
            f"&spx={quote(spx, safe='')}"
        )
        if pqv:
            link += f"&pqv={pqv}"
        link += f"&flow={flow}#{client_email}"

        return {"success": True, "link": link, "client_id": client_id}

    except Exception as e:
        return {"error": str(e)}


# --- Запуск ---
if __name__ == "__main__":
    asyncio.run(bot.polling(non_stop=True, timeout=60))
