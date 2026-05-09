# 🤖 VPN Admin Bot

> Telegram-бот для управления VPN-инфраструктурой на базе [3x-ui](https://github.com/MHSanaei/3x-ui) — написан под реальный продакшн.

---

## ✨ Возможности

| Функция | Описание |
|---|---|
| 🔗 Генерация ссылок | VLESS Reality с поддержкой Post-Quantum (pqv) — параметры читаются с сервера динамически |
| 👥 Список клиентов | Активные пользователи по выбранному серверу |
| ✅ Включить / ❌ Отключить | Управление доступом клиентов в реальном времени |
| 📅 Даты окончания | Таблица подписок с датами истечения |
| 💳 Мониторинг оплаты | Проверка дней до оплаты сервера через Fornex API |
| 🔄 Авто-мониторинг | Уведомления каждые 24ч если осталось < 5 дней |
| 🖥 Мультисервер | Поддержка двух VPN-серверов, переключение из меню |
| 🔔 Клиентский флоу | Уведомление администратора → подтверждение → генерация ссылки → отправка клиенту |

---

## 🛠 Стек

- **Python 3.10+**
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) — синхронный telebot
- [py3xui](https://github.com/iwatkot/py3xui) — работа с 3x-ui API
- `asyncio` + `threading` — асинхронные операции внутри синхронного бота
- `python-dotenv` — конфигурация через `.env`
- `pytz`, `requests` — таймзоны и HTTP

---

## ⚙️ Установка

```bash
git clone https://github.com/Servios/vpn-bot-demo.git
cd vpn-bot-demo

python3 -m venv venv
source venv/bin/activate
pip install pytelegrambotapi py3xui python-dotenv requests pytz

cp .env.example .env
# заполни .env своими данными

nohup venv/bin/python3 link_bot.py >> link_bot.log 2>&1 &
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

FORNEX_API_KEY=...
FORNEX_ORDER_URL_1=https://fornex.com/api/orders/vps/your-order/
```

---

## 🏗 Архитектура

```
Клиент → client_bot → уведомление в admin_bot
                              ↓
                    Выбор сервера (Германия / Нидерланды)
                              ↓
                    3x-ui API → создание клиента
                              ↓
                    Генерация VLESS ссылки (с pqv из сервера)
                              ↓
                    Отправка ссылки клиенту
```

---

## 👨‍💻 Автор

Разработано **[@bkorolkowww](https://t.me/bkorolkowww)**

По вопросам разработки Telegram-ботов, автоматизации и VPN-инфраструктуры — пишите в личку.
