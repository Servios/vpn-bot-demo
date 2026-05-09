# VPN Admin Bot

Telegram-бот для управления VPN-серверами на базе [3x-ui](https://github.com/MHSanaei/3x-ui).

## Возможности

- 🔗 Генерация VLESS Reality ссылок для клиентов (с поддержкой Post-Quantum)
- 👥 Просмотр списка активных пользователей
- ✅ / ❌ Включение и отключение пользователей
- 📅 Просмотр дат окончания подписок
- 💳 Проверка дней до оплаты сервера (Fornex API)
- 🔄 Автоматический мониторинг срока оплаты (раз в 24ч)
- 🖥 Поддержка двух серверов

## Установка

1. Клонируй репозиторий:
```bash
git clone https://github.com/Servios/vpn-bot-demo.git
cd vpn-bot-demo
```

2. Создай виртуальное окружение и установи зависимости:
```bash
python3 -m venv venv
source venv/bin/activate
pip install pytelegrambotapi py3xui python-dotenv requests pytz
```

3. Скопируй `.env.example` в `.env` и заполни переменные:
```bash
cp .env.example .env
```

4. Запусти бота:
```bash
nohup venv/bin/python3 link_bot.py >> link_bot.log 2>&1 &
```

## Конфигурация

Все настройки задаются через `.env` файл. Смотри `.env.example`.

| Переменная | Описание |
|---|---|
| `ADMIN_BOT_TOKEN` | Токен админ-бота |
| `CLIENT_BOT_TOKEN` | Токен клиентского бота |
| `ALLOWED_IDS` | Telegram ID администраторов через запятую |
| `XUI_URL_1/2` | URL панели 3x-ui |
| `XUI_USER_1/2` | Логин 3x-ui |
| `XUI_PASS_1/2` | Пароль 3x-ui |
| `SERVER_IP_1/2` | IP-адрес сервера |
| `SERVER_PORT_1/2` | Порт inbound |
| `FORNEX_API_KEY` | API-ключ Fornex |
| `FORNEX_ORDER_URL_1/2` | URL заказа VPS на Fornex |

## Стек

- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- [py3xui](https://github.com/iwatkot/py3xui)
- Python 3.10+
