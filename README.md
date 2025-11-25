# Trading bot + dashboard (ready project)

project/
│── bot.py            # торговий бот
│── db.py             # робота з SQLite (створює trades.db)
│── api.py            # FastAPI бекенд для отримання угод
│── trades.db         # база даних (створюється автоматично)
│
└── web/
    └── index.html    # простий дашборд (Chart.js)


1. Створення віртуального середовища та встановлення залежностей:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

2. Додайте Binance API ключі (рекомендується тестнет):
export BINANCE_API_KEY=your_key
export BINANCE_API_SECRET=your_secret

3. Запустіть бекенд (API):
uvicorn api:app --reload --port 8000

4. Запуск торгового бота (приклад):
python bot.py \
    --symbol BTCUSDT \
    --long_tp 1 \
    --long_to_short 0.5 \
    --short_tp 1 \
    --short_to_long 0.5 \
    --start 1 \
    --lev 10

5. Відкрийте дашборд:

В браузері відкрийте файл:

web/index.html

Він автоматично підтягує дані з:

http://localhost:8000/trades

Важливі примітки та безпека

У клієнта Binance використовується testnet=True, тому бот призначений для тестових угод.

Не використовуйте реальні API-ключі, доки повністю не розумієте, як працює бот.

Перевіряйте:

розмір лоту

кредитне плече

маржинальні параметри
— перш ніж запускати бота у реальні торги.