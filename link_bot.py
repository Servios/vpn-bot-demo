
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import pytz
import telebot
from telebot import types
import time
import threading
from py3xui import AsyncApi, Client
import asyncio
import uuid

load_dotenv()

# --- Токен бота ---
key = os.getenv("ADMIN_BOT_TOKEN")

# --- Сервер 1 ---
api1 = AsyncApi(
    os.getenv("XUI_URL_1"),
    os.getenv("XUI_USER_1"),
    os.getenv("XUI_PASS_1"),
    use_tls_verify=False
)
ENABLED_USERS_1 = []
INBOUND_DATA_1 = {
    "port":      os.getenv("SERVER_PORT_1", "443"),
    "server_ip": os.getenv("SERVER_IP_1"),
}

# --- Сервер 2 ---
api2 = AsyncApi(
    os.getenv("XUI_URL_2"),
    os.getenv("XUI_USER_2"),
    os.getenv("XUI_PASS_2"),
    use_tls_verify=False
)
ENABLED_USERS_2 = []
INBOUND_DATA_2 = {
    "port":      os.getenv("SERVER_PORT_2", "32739"),
    "server_ip": os.getenv("SERVER_IP_2"),
}

ALLOWED_ID = list(map(int, os.getenv("ALLOWED_IDS", "").split(","))) if os.getenv("ALLOWED_IDS") else []
CLIENT_BOT_TOKEN = os.getenv("CLIENT_BOT_TOKEN")

SELECTED_SERVER = {}  # chat_id -> 1 или 2
bot = telebot.TeleBot(key)
loop_running = False


# --- Хелперы ---
def get_users(chat_id):
    return ENABLED_USERS_1 if SELECTED_SERVER.get(chat_id) == 1 else ENABLED_USERS_2

def get_inbound(chat_id):
    return INBOUND_DATA_1 if SELECTED_SERVER.get(chat_id) == 1 else INBOUND_DATA_2

def main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Запустить цикл проверки")
    btn2 = types.KeyboardButton("Проверить время до оплаты")
    btn3 = types.KeyboardButton("Получить ссылку пользователя")
    btn4 = types.KeyboardButton("Получить список пользователей")
    btn5 = types.KeyboardButton("◀️ Назад")
    btn6 = types.KeyboardButton("Отключить пользователя")
    btn7 = types.KeyboardButton("Включить пользователя")
    btn8 = types.KeyboardButton("📅 Даты окончания")
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn6, btn7)
    markup.row(btn8)
    markup.row(btn5)
    return markup

def client_select_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("🇳🇱 Нидерланды"),
        types.KeyboardButton("🇩🇪 Германия"),
    )
    return markup

def handle_all(message):
    if message.from_user.id not in ALLOWED_ID:
        bot.send_message(message.chat.id, "У вас нет доступа к этому боту")
        return False
    return True


# --- Хэндлеры ---
@bot.message_handler(commands=["start"])
def hello(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("Да"), types.KeyboardButton("Нет"))
    bot.send_message(
        message.chat.id,
        "👋 *Добро пожаловать, босс!*\n\n"
        "🛡 Я твой личный помощник по управлению VPN-серверами.\n\n"
        "📋 *Что я умею:*\n"
        "├ 📊 Проверять дни до оплаты сервера\n"
        "├ 🔄 Запускать автоматический мониторинг\n"
        "├ 🔗 Генерировать ссылки для клиентов\n"
        "└ 👥 Показывать список активных пользователей\n\n"
        "▶️ Начать работу?",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "Нет")
def decline(message):
    bot.send_message(message.chat.id, "👌 Окей, если понадоблюсь — жми /start")

@bot.message_handler(func=lambda m: m.text == "◀️ Назад")
def go_back(message):
    choose_server(message)

@bot.message_handler(func=lambda m: m.text == "Да")
def choose_server(message):
    if not handle_all(message):
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("🖥 Сервер 1"),
        types.KeyboardButton("🖥 Сервер 2")
    )
    bot.send_message(message.chat.id, "🖥 *Выбери сервер для работы:*", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🖥 Сервер 1")
def select_server_1(message):
    if not handle_all(message):
        return
    SELECTED_SERVER[message.chat.id] = 1
    response = requests.get(
        os.getenv("FORNEX_ORDER_URL_1"),
        headers={"Authorization": f"Api-Key {os.getenv('FORNEX_API_KEY')}"}
    )
    tz_moscow = pytz.timezone('Europe/Moscow')
    today = datetime.now(tz_moscow).date()
    if response.status_code == 200:
        data = response.json()
        external_date = datetime.strptime(data["expiration_date"], "%Y-%m-%dT%H:%M:%SZ").date()
        days_left = (external_date - today).days
        bot.send_message(message.chat.id, f"✅ *Сервер 1 — Германия* выбран\n💳 До оплаты: *{days_left} дн.*", parse_mode="Markdown", reply_markup=main_markup())
    else:
        bot.send_message(message.chat.id, "✅ *Сервер 1 — Германия* выбран", parse_mode="Markdown", reply_markup=main_markup())

@bot.message_handler(func=lambda m: m.text == "🖥 Сервер 2")
def select_server_2(message):
    if not handle_all(message):
        return
    SELECTED_SERVER[message.chat.id] = 2
    response = requests.get(
        os.getenv("FORNEX_ORDER_URL_2"),
        headers={"Authorization": f"Api-Key {os.getenv('FORNEX_API_KEY')}"}
    )
    tz_moscow = pytz.timezone('Europe/Moscow')
    today = datetime.now(tz_moscow).date()
    if response.status_code == 200:
        data = response.json()
        external_date = datetime.strptime(data["expiration_date"], "%Y-%m-%dT%H:%M:%SZ").date()
        days_left = (external_date - today).days
        bot.send_message(message.chat.id, f"✅ *Сервер 2 — Нидерланды* выбран\n💳 До оплаты: *{days_left} дн.*", parse_mode="Markdown", reply_markup=main_markup())
    else:
        bot.send_message(message.chat.id, "✅ *Сервер 2 — Нидерланды* выбран", parse_mode="Markdown", reply_markup=main_markup())

@bot.message_handler(func=lambda m: m.text == "Проверить время до оплаты")
def check_payment(message):
    if not handle_all(message):
        return
    response = requests.get(
        os.getenv("FORNEX_ORDER_URL_2"),
        headers={"Authorization": f"Api-Key {os.getenv('FORNEX_API_KEY')}"}
    )
    tz_moscow = pytz.timezone('Europe/Moscow')
    today = datetime.now(tz_moscow).date()
    if response.status_code == 200:
        data = response.json()
        external_date = datetime.strptime(data["expiration_date"], "%Y-%m-%dT%H:%M:%SZ").date()
        days_left = (external_date - today).days
        bot.send_message(message.chat.id, f"💳 До оплаты {days_left} дней", reply_markup=main_markup())
    else:
        bot.send_message(message.chat.id, f"❌ Ошибка API: {response.status_code}")


def check_loop(message):
    global loop_running
    loop_running = True
    while True:
        response = requests.get(
            os.getenv("FORNEX_ORDER_URL_2"),
            headers={"Authorization": f"Api-Key {os.getenv('FORNEX_API_KEY')}"}
        )
        tz_moscow = pytz.timezone('Europe/Moscow')
        today = datetime.now(tz_moscow).date()
        if response.status_code != 200:
            print(f"Ошибка API: {response.status_code}")
            time.sleep(10)
            continue
        data = response.json()
        external_date = datetime.strptime(data["expiration_date"], "%Y-%m-%dT%H:%M:%SZ").date()
        days_left = (external_date - today).days
        if days_left < 5:
            bot.send_message(message.chat.id, f"⚠️ До оплаты {days_left} дней!")
        else:
            bot.send_message(message.chat.id, f"✅ Пока можешь не платить, ещё {days_left} дней")
        time.sleep(86400)
        loop_running = False

@bot.message_handler(func=lambda m: m.text == "Запустить цикл проверки")
def infinite_check(message):
    global loop_running
    if not handle_all(message):
        return
    if loop_running:
        bot.send_message(message.chat.id, "⚠️ Мониторинг уже запущен!")
        return
    bot.send_message(message.chat.id, "🔄 Запускаю мониторинг серверов...")
    thread = threading.Thread(target=check_loop, args=(message,))
    thread.daemon = True
    thread.start()
    bot.send_message(message.chat.id, "✅ Мониторинг запущен! Буду присылать уведомления каждые 24ч.")


async def refresh_server(api_instance, users_list: list, inbound_id: int = 1):
    try:
        await api_instance.login()
        ind = await api_instance.inbound.get_by_id(inbound_id)
        if ind:
            new_clients = []
            for client in ind.settings.clients:
                if client.enable:
                    new_clients.append({
                        "email": client.email,
                        "id":    client.id,
                        "flow":  getattr(client, "flow", None) or "xtls-rprx-vision",
                    })
            users_list.clear()
            users_list.extend(new_clients)
        else:
            print(f"Inbound {inbound_id} не найден!")
    except Exception as e:
        print(f"Ошибка при обновлении пользователей: {e}")

def users_refresh_loop():
    while True:
        asyncio.run(refresh_server(api1, ENABLED_USERS_1))
        asyncio.run(refresh_server(api2, ENABLED_USERS_2))
        time.sleep(60)


@bot.message_handler(func=lambda m: m.text == "Получить ссылку пользователя")
def get_link(message):
    if not handle_all(message):
        return
    if message.chat.id not in SELECTED_SERVER:
        bot.send_message(message.chat.id, "⚠️ Сначала выбери сервер — нажми /start")
        return
    msg = bot.send_message(message.chat.id, "📧 Введи email пользователя:")
    bot.register_next_step_handler(msg, share_link)

@bot.message_handler(func=lambda m: m.text == "Отключить пользователя")
def get_unabled(message):
    if not handle_all(message):
        return
    if message.chat.id not in SELECTED_SERVER:
        bot.send_message(message.chat.id, "⚠️ Сначала выбери сервер — нажми /start")
        return
    msg = bot.send_message(message.chat.id, "📧 Введи email пользователя:")
    if SELECTED_SERVER.get(message.chat.id) == 1:
        bot.register_next_step_handler(msg, unable_user1)
    elif SELECTED_SERVER.get(message.chat.id) == 2:
        bot.register_next_step_handler(msg, unable_user2)

@bot.message_handler(func=lambda m: m.text == "Включить пользователя")
def get_enabled(message):
    if not handle_all(message):
        return
    if message.chat.id not in SELECTED_SERVER:
        bot.send_message(message.chat.id, "⚠️ Сначала выбери сервер — нажми /start")
        return
    msg = bot.send_message(message.chat.id, "📧 Введи email пользователя:")
    if SELECTED_SERVER.get(message.chat.id) == 1:
        bot.register_next_step_handler(msg, enable_user1)
    elif SELECTED_SERVER.get(message.chat.id) == 2:
        bot.register_next_step_handler(msg, enable_user2)

@bot.message_handler(func=lambda m: m.text == "📅 Даты окончания")
def get_expiration_dates(message):
    if not handle_all(message):
        return
    if message.chat.id not in SELECTED_SERVER:
        bot.send_message(message.chat.id, "⚠️ Сначала выбери сервер — нажми /start")
        return
    if SELECTED_SERVER.get(message.chat.id) == 1:
        check_expiration_date1(message)
    elif SELECTED_SERVER.get(message.chat.id) == 2:
        check_expiration_date2(message)


def enable_user1(message):
    target = message.text
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def _run():
        fresh_api = AsyncApi(os.getenv("XUI_URL_1"), os.getenv("XUI_USER_1"), os.getenv("XUI_PASS_1"), use_tls_verify=False)
        await fresh_api.login()
        ind = await fresh_api.inbound.get_by_id(1)
        for client in ind.settings.clients:
            if client.email == target:
                client.enable = True
                await fresh_api.inbound.update(1, ind)
                return True
        return False
    found = loop.run_until_complete(_run())
    loop.close()
    if found:
        bot.send_message(message.chat.id, f"✅ Пользователь `{target}` включён.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ Пользователь `{target}` не найден.", parse_mode="Markdown")

def enable_user2(message):
    target = message.text
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def _run():
        fresh_api = AsyncApi(os.getenv("XUI_URL_2"), os.getenv("XUI_USER_2"), os.getenv("XUI_PASS_2"), use_tls_verify=False)
        await fresh_api.login()
        ind = await fresh_api.inbound.get_by_id(1)
        for client in ind.settings.clients:
            if client.email == target:
                client.enable = True
                await fresh_api.inbound.update(1, ind)
                return True
        return False
    found = loop.run_until_complete(_run())
    loop.close()
    if found:
        bot.send_message(message.chat.id, f"✅ Пользователь `{target}` включён.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ Пользователь `{target}` не найден.", parse_mode="Markdown")

def unable_user1(message):
    target = message.text
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def _run():
        fresh_api = AsyncApi(os.getenv("XUI_URL_1"), os.getenv("XUI_USER_1"), os.getenv("XUI_PASS_1"), use_tls_verify=False)
        await fresh_api.login()
        ind = await fresh_api.inbound.get_by_id(1)
        for client in ind.settings.clients:
            if client.email == target:
                client.enable = False
                await fresh_api.inbound.update(1, ind)
                return True
        return False
    found = loop.run_until_complete(_run())
    loop.close()
    if found:
        bot.send_message(message.chat.id, f"✅ Пользователь `{target}` отключён.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ Пользователь `{target}` не найден.", parse_mode="Markdown")

def unable_user2(message):
    target = message.text
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def _run():
        fresh_api = AsyncApi(os.getenv("XUI_URL_2"), os.getenv("XUI_USER_2"), os.getenv("XUI_PASS_2"), use_tls_verify=False)
        await fresh_api.login()
        ind = await fresh_api.inbound.get_by_id(1)
        for client in ind.settings.clients:
            if client.email == target:
                client.enable = False
                await fresh_api.inbound.update(1, ind)
                return True
        return False
    found = loop.run_until_complete(_run())
    loop.close()
    if found:
        bot.send_message(message.chat.id, f"✅ Пользователь `{target}` отключён.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ Пользователь `{target}` не найден.", parse_mode="Markdown")

def share_link(message):
    target = message.text
    chat_id = message.chat.id
    users = get_users(chat_id)
    d = get_inbound(chat_id)
    user_to_link = None
    for item in users:
        if item["email"] == target:
            user_to_link = item
            break
    if user_to_link:
        link = (
            f"vless://{user_to_link['id']}@{d['server_ip']}:{d['port']}"
            f"?type=tcp&encryption=none&security=reality"
            f"&flow={user_to_link['flow']}"
            f"#{user_to_link['email']}"
        )
        bot.send_message(chat_id,
            f"🔗 *Ссылка для* `{user_to_link['email']}`:\n\n`{link}`",
            parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ Пользователь не найден. Проверь email и попробуй снова.")

@bot.message_handler(func=lambda m: m.text == "Получить список пользователей")
def get_users_list(message):
    if not handle_all(message):
        return
    if message.chat.id not in SELECTED_SERVER:
        bot.send_message(message.chat.id, "⚠️ Сначала выбери сервер — нажми /start")
        return
    users = get_users(message.chat.id)
    if not users:
        bot.send_message(message.chat.id, "⏳ Список ещё не загружен, подожди немного")
        return
    server_num = SELECTED_SERVER[message.chat.id]
    server_name = "Германия 🇩🇪" if server_num == 1 else "Нидерланды 🇳🇱"
    users_list = "\n".join(f"├ `{item['email']}`" for item in users[:-1])
    users_list += f"\n└ `{users[-1]['email']}`" if users else ""
    bot.send_message(message.chat.id,
        f"👥 *Активные пользователи — {server_name}*\n"
        f"📊 Всего: *{len(users)}*\n\n"
        f"{users_list}",
        parse_mode="Markdown")


async def create_link_for_client(client_email: str):
    try:
        from urllib.parse import quote
        fresh_api = AsyncApi(os.getenv("XUI_URL_1"), os.getenv("XUI_USER_1"), os.getenv("XUI_PASS_1"), use_tls_verify=False)
        await fresh_api.login()
        inbound = await fresh_api.inbound.get_by_id(1)
        if not inbound:
            return {"error": "Inbound не найден"}
        for client in inbound.settings.clients:
            if client.email == client_email:
                return {"error": f"Клиент '{client_email}' уже существует"}
        client_id = str(uuid.uuid4())
        new_client = Client(id=client_id, email=client_email, enable=True, flow="xtls-rprx-vision")
        inbound.settings.clients.append(new_client)
        await fresh_api.inbound.update(1, inbound)
        rs  = inbound.stream_settings.reality_settings
        pbk = rs["settings"]["publicKey"]
        fp  = rs["settings"]["fingerprint"]
        pqv = rs["settings"].get("mldsa65Verify", "")
        spx = rs["settings"].get("spiderX", "/")
        sni = rs["target"].split(":")[0]
        sid = rs["shortIds"][0]
        link = (
            f"vless://{client_id}@{INBOUND_DATA_1['server_ip']}:{INBOUND_DATA_1['port']}"
            f"?type=tcp&encryption=none&security=reality"
            f"&pbk={pbk}&fp={fp}&sni={sni}&sid={sid}"
            f"&spx={quote(spx, safe='')}"
        )
        if pqv:
            link += f"&pqv={pqv}"
        link += f"&flow=xtls-rprx-vision#{client_email}"
        return {"success": True, "link": link}
    except Exception as e:
        return {"error": str(e)}


async def create_link_for_client2(client_email: str):
    try:
        from urllib.parse import quote
        fresh_api = AsyncApi(os.getenv("XUI_URL_2"), os.getenv("XUI_USER_2"), os.getenv("XUI_PASS_2"), use_tls_verify=False)
        await fresh_api.login()
        inbound = await fresh_api.inbound.get_by_id(1)
        if not inbound:
            return {"error": "Inbound не найден"}
        for client in inbound.settings.clients:
            if client.email == client_email:
                return {"error": f"Клиент '{client_email}' уже существует"}
        client_id = str(uuid.uuid4())
        new_client = Client(id=client_id, email=client_email, enable=True, flow="xtls-rprx-vision")
        inbound.settings.clients.append(new_client)
        await fresh_api.inbound.update(1, inbound)
        rs  = inbound.stream_settings.reality_settings
        pbk = rs["settings"]["publicKey"]
        fp  = rs["settings"]["fingerprint"]
        pqv = rs["settings"].get("mldsa65Verify", "")
        spx = rs["settings"].get("spiderX", "/")
        sni = rs["target"].split(":")[0]
        sid = rs["shortIds"][0]
        link = (
            f"vless://{client_id}@{INBOUND_DATA_2['server_ip']}:{INBOUND_DATA_2['port']}"
            f"?type=tcp&encryption=none&security=reality"
            f"&pbk={pbk}&fp={fp}&sni={sni}&sid={sid}"
            f"&spx={quote(spx, safe='')}"
        )
        if pqv:
            link += f"&pqv={pqv}"
        link += f"&flow=xtls-rprx-vision#{client_email}"
        return {"success": True, "link": link}
    except Exception as e:
        return {"error": str(e)}


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_acces_"))
def approve_client(call):
    client_id = call.data.split("_")[-1]
    client_email = f"user_{client_id}"

    def selected_country(message):
        bot.send_message(message.chat.id, "⏳ Создаю ссылку...", reply_markup=types.ReplyKeyboardRemove())
        if message.text == "🇩🇪 Германия":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(create_link_for_client(client_email))
            loop.close()
        elif message.text == "🇳🇱 Нидерланды":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(create_link_for_client2(client_email))
            loop.close()
        else:
            return
        if result.get("success"):
            text = f"✅ Оплата подтверждена!\n\n🔗 Твоя ссылка:\n`{result['link']}`"
        else:
            text = f"✅ Оплата подтверждена!\n⚠️ Ошибка генерации ссылки: {result.get('error')}"
        bot.send_message(message.chat.id, f"Ссылка отправлена клиенту: {result.get('error', 'OK')}", reply_markup=main_markup())
        requests.post(
            f"https://api.telegram.org/bot{CLIENT_BOT_TOKEN}/sendMessage",
            json={"chat_id": client_id, "text": text, "parse_mode": "Markdown"},
        )

    msg = bot.send_message(call.message.chat.id, "Выбери сервер для клиента:", reply_markup=client_select_markup())
    bot.register_next_step_handler(msg, selected_country)
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=None
    )
    bot.answer_callback_query(call.id, "Выбери сервер")


def check_expiration_date1(message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def _run():
        fresh_api = AsyncApi(os.getenv("XUI_URL_1"), os.getenv("XUI_USER_1"), os.getenv("XUI_PASS_1"), use_tls_verify=False)
        await fresh_api.login()
        ind = await fresh_api.inbound.get_by_id(1)
        lines = []
        for client in ind.settings.clients:
            exp = client.expiry_time
            if exp and exp > 0:
                dt = datetime.fromtimestamp(exp / 1000).strftime("%d.%m.%Y")
                lines.append(f"├ `{client.email}` → {dt}")
            else:
                lines.append(f"├ `{client.email}` → бессрочно")
        return "\n".join(lines)
    result = loop.run_until_complete(_run())
    loop.close()
    bot.send_message(message.chat.id,
        f"📅 *Даты окончания — Германия 🇩🇪*\n\n{result}",
        parse_mode="Markdown")


def check_expiration_date2(message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def _run():
        fresh_api = AsyncApi(os.getenv("XUI_URL_2"), os.getenv("XUI_USER_2"), os.getenv("XUI_PASS_2"), use_tls_verify=False)
        await fresh_api.login()
        ind = await fresh_api.inbound.get_by_id(1)
        lines = []
        for client in ind.settings.clients:
            exp = client.expiry_time
            if exp and exp > 0:
                dt = datetime.fromtimestamp(exp / 1000).strftime("%d.%m.%Y")
                lines.append(f"├ `{client.email}` → {dt}")
            else:
                lines.append(f"├ `{client.email}` → бессрочно")
        return "\n".join(lines)
    result = loop.run_until_complete(_run())
    loop.close()
    bot.send_message(message.chat.id,
        f"📅 *Даты окончания — Нидерланды 🇳🇱*\n\n{result}",
        parse_mode="Markdown")


refresh_thread = threading.Thread(target=users_refresh_loop, daemon=True)
refresh_thread.start()

bot.infinity_polling(timeout=60, long_polling_timeout=30)
