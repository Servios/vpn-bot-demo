# 🤖 VPN Telegram Bot System

> Система из двух Telegram-ботов для продажи и управления VPN на базе [3x-ui](https://github.com/MHSanaei/3x-ui) — написана под реальный продакшн.

---

## 📦 Состав

| Файл | Роль | Для кого |
|---|---|---|
| `client_bot.py` | Клиентский бот — приём заявок, справочник | Покупатели VPN |
| `link_bot.py` | Админ-бот — управление серверами и клиентами | Администраторы |

---

## ✨ Возможности

### 👤 Клиентский бот (`client_bot.py`)
- Приём заявок на доступ → уведомление администратора
- Автоматическая балансировка между администраторами (round-robin)
- Справочник: установка на iOS / Android / Windows, FAQ, поддержка
- Получение VLESS ссылки после подтверждения оплаты

### 🛠 Админ-бот (`link_bot.py`)

| Функция | Описание |
|---|---|
| 🔗 Генерация ссылок | VLESS Reality + Post-Quantum (pqv) — параметры читаются с сервера динамически |
| 👥 Список клиентов | Активные пользователи по выбранному серверу |
| ✅ / ❌ Вкл / Откл | Управление доступом клиентов в реальном времени |
| 📅 Даты окончания | Таблица подписок с датами истечения |
| 💳 Мониторинг оплаты | Проверка дней до оплаты VPS через Fornex API |
| 🔄 Авто-мониторинг | Уведомления каждые 24ч если осталось < 5 дней |
| 🖥 Мультисервер | Поддержка двух VPN-серверов, переключение из меню |

---

## 🏗 Архитектура флоу

```
Клиент нажимает «Получить доступ»
        ↓
client_bot уведомляет администратора
        ↓
Администратор подтверждает оплату
        ↓
link_bot выбирает сервер (Германия / Нидерланды)
        ↓
3x-ui API → создаёт клиента → читает Reality-параметры
        ↓
Генерирует VLESS ссылку с pqv, spx, sni
        ↓
client_bot отправляет ссылку покупателю
```

---

## 🛠 Стек

- **Python 3.10+**
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) — sync + async telebot
- [py3xui](https://github.com/iwatkot/py3xui) — работа с 3x-ui панелью
- `asyncio` + `threading` — асинхронные вызовы внутри синхронного бота
- `python-dotenv` — конфигурация через `.env`

---

## ⚙️ Установка

```bash
git clone https://github.com/Servios/vpn-bot-demo.git
cd vpn-bot-demo

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# заполни .env своими данными
```

### Запуск

```bash
# Админ-бот
nohup venv/bin/python3 link_bot.py >> link_bot.log 2>&1 &

# Клиентский бот
nohup venv/bin/python3 client_bot.py >> client_bot.log 2>&1 &
```

---

## 🔐 Конфигурация

Все секреты задаются через `.env`. Смотри [`.env.example`](.env.example).

```env
ADMIN_BOT_TOKEN=...
CLIENT_BOT_TOKEN=...
ALLOWED_IDS=123456789,987654321

XUI_URL_1=https://your-server:port/path
XUI_USER_1=admin
XUI_PASS_1=password
SERVER_IP_1=1.2.3.4
SERVER_PORT_1=443

XUI_URL_2=https://your-server-2:port/path
XUI_USER_2=admin
XUI_PASS_2=password
SERVER_IP_2=5.6.7.8
SERVER_PORT_2=32739

FORNEX_API_KEY=...
FORNEX_ORDER_URL_1=https://fornex.com/api/orders/vps/xxxxx/
FORNEX_ORDER_URL_2=https://fornex.com/api/orders/vps/yyyyy/
```

---

## 👨‍💻 Автор

Разработано **[@bkorolkowww](https://t.me/bkorolkowww)**

По вопросам разработки Telegram-ботов, автоматизации и VPN-инфраструктуры — пишите в личку.
