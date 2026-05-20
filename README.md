# Hotel Trainer Bot

Telegram-бот тренажёр для персонала гостиниц по законам РФ о туризме и гостеприимстве.

## Возможности

- Тесты в трёх режимах:
  - **Быстрый тест** — 10 случайных вопросов.
  - **Экзамен** — 50 случайных вопросов.
  - **Работа над ошибками** — до 10 вопросов, в которых пользователь последний раз ошибся.
- После каждого ответа — разбор и ссылка на пункт закона.
- Кнопка «Сообщить об ошибке» под каждым вопросом — жалоба уходит админу.
- Раздел «Моя статистика»: общая точность и разбивка по темам.
- Дисклеймер «база актуальна на ДАТУ» из конфига.
- Админка `/admin`: общая статистика, рассылка по всем пользователям, разбор жалоб, деактивация плохих вопросов.

## Стек

- Python 3.11+ (тестировалось на 3.12)
- [aiogram](https://docs.aiogram.dev/) 3.13
- [aiosqlite](https://github.com/omnilib/aiosqlite) — SQLite в async-режиме
- python-dotenv — чтение `.env`

## Структура проекта

```
hotel-trainer-bot/
├── bot.py                       # точка входа
├── config.py                    # загрузка .env
├── requirements.txt
├── .env.example
├── data/
│   ├── questions_seed.json      # 5 демо-вопросов
│   └── bot.db                   # SQLite (создаётся автоматически, в .gitignore)
├── app/
│   ├── db/
│   │   ├── schema.sql           # все CREATE TABLE
│   │   ├── connection.py        # async-соединение
│   │   ├── init_db.py           # инициализация + сидинг
│   │   └── repositories/        # доступ к данным
│   ├── handlers/                # /start, /admin, тест, статистика, жалобы
│   ├── keyboards/               # inline-клавиатуры
│   ├── services/                # бизнес-логика (выбор вопросов, статистика)
│   ├── states/                  # FSM-состояния
│   ├── middlewares/             # авто-регистрация пользователя
│   └── utils/texts.py           # все тексты бота
└── scripts/
    └── import_questions.py      # CLI для загрузки боевой базы вопросов
```

## Запуск локально (Windows)

### 1. Установка зависимостей

```powershell
cd "c:\Project Bot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Заполнить `.env`

```powershell
copy .env.example .env
```

Открой `.env` в редакторе и заполни:

- `TELEGRAM_BOT_TOKEN` — токен из [@BotFather](https://t.me/BotFather).
- `ADMIN_TELEGRAM_ID` — твой Telegram ID (узнать у [@userinfobot](https://t.me/userinfobot)).
- `LAW_BASE_DATE` — дата актуальности правовой базы для дисклеймера.
- `PROXY_URL` *(опционально)* — HTTPS-прокси, если хостинг блокирует api.telegram.org (типично для VPS в РФ). Формат: `http://user:pass@host:port`. Оставь пустым, если прокси не нужен.

### 3. Запуск

```powershell
python bot.py
```

При первом запуске:
- создастся `data/bot.db`,
- применится схема,
- загрузятся 5 демо-вопросов из `data/questions_seed.json`.

Открой бота в Telegram, отправь `/start` — увидишь приветствие, дисклеймер и главное меню. Прогони быстрый тест на 5 демо-вопросах, чтобы убедиться, что всё работает.

Админ-команда: `/admin` (доступна только пользователю с `ADMIN_TELEGRAM_ID`).

## Загрузка боевой базы вопросов

Когда у тебя готов JSON-файл с реальными вопросами, положи его, например, в `data/real_questions.json` в формате:

```json
[
  {
    "topic": "Договор о реализации турпродукта",
    "text": "Текст вопроса…",
    "option_a": "…",
    "option_b": "…",
    "option_c": "…",
    "option_d": "…",
    "correct_option": "B",
    "explanation": "Разбор…",
    "law_reference": "ФЗ № 132-ФЗ, ст. 10",
    "difficulty": 1,
    "is_active": 1
  }
]
```

Запусти импорт. Чтобы заменить демо-вопросы реальными:

```powershell
python scripts\import_questions.py data\real_questions.json --replace-demo
```

Или мягче — просто отключить демо (останутся в БД, но не будут выбираться):

```powershell
python scripts\import_questions.py data\real_questions.json --deactivate-demo
```

Без флага — просто допишет в существующую базу.

## Деплой на сервер (настраиваем после рабочей локальной версии)

Сервер: `83.220.175.207` (Linux, далее — Ubuntu 22.04 как пример).

### Подключение

```bash
ssh root@83.220.175.207
```

(Перед боевым запуском смени пароль на сервере и/или настрой вход по SSH-ключу. Пароль, засвеченный в чате при старте проекта — ротируй.)

### Установка

```bash
apt update && apt install -y python3.12 python3.12-venv git
adduser --disabled-password --gecos "" botuser
su - botuser

git clone <URL_РЕПОЗИТОРИЯ> hotel-trainer-bot
cd hotel-trainer-bot
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env   # вписать TELEGRAM_BOT_TOKEN и ADMIN_TELEGRAM_ID
```

### Systemd-сервис

Файл `/etc/systemd/system/hotel-trainer-bot.service`:

```ini
[Unit]
Description=Hotel Trainer Telegram Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/hotel-trainer-bot
ExecStart=/home/botuser/hotel-trainer-bot/.venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hotel-trainer-bot
sudo systemctl start hotel-trainer-bot
sudo systemctl status hotel-trainer-bot
journalctl -u hotel-trainer-bot -f
```

### Обновление кода на сервере

```bash
su - botuser
cd hotel-trainer-bot
git pull
. .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart hotel-trainer-bot
```

## Безопасность

- Не коммить `.env` (в `.gitignore`).
- Если токен бота или пароль сервера засветились — ротируй их (`/revoke` у @BotFather, `passwd` на сервере).
- В админ-командах проверяется `ADMIN_TELEGRAM_ID` — никто кроме тебя не сможет вызвать `/admin`, рассылку или разбор жалоб.

## Дисклеймер

Бот — учебный тренажёр. Тесты не являются юридической консультацией. Реальную правовую базу актуализирует администратор, дата актуальности видна в `/start` (поле `LAW_BASE_DATE` в `.env`).
