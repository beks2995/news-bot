import os
import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import asyncio
from bs4 import BeautifulSoup

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APP_URL = os.getenv("APP_URL")  # Railway URL

bot = Bot(token=TELEGRAM_TOKEN)

def get_investing_news_api():
    server_now = datetime.now(timezone.utc)
    date_today = server_now.strftime('%Y-%m-%d')
    date_tomorrow = (server_now + timedelta(days=1)).strftime('%Y-%m-%d')

    url = 'https://ru.investing.com/economic-calendar/Service/getCalendarFilteredData'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
    }
    data = {
        'timeZone': '18',  # UTC+6 Бишкек
        'country[]': '5',  # США
        'importance[]': '3',  # 3 звезды
        'dateFrom': date_today,
        'dateTo': date_tomorrow
    }

    response = requests.post(url, headers=headers, data=data)
    json_data = response.json()
    html = json_data.get('data', '')
    soup = BeautifulSoup(html, 'lxml')

    today_events = []
    tomorrow_events = []

    for ev in soup.find_all('tr', {'event_row': True}):
        date_attr = ev.get('data-event-datetime')[:10]  # 'YYYY-MM-DD'
        time = ev.find('td', {'class': 'time'}).get_text(strip=True)
        title = ev.find('td', {'class': 'event'}).get_text(strip=True)

        if date_attr == date_today:
            today_events.append(f"{time} Бишкек – {title} (★★★)")
        elif date_attr == date_tomorrow:
            tomorrow_events.append(f"{time} Бишкек – {title} (★★★)")

    return today_events, tomorrow_events

async def send_news_manual(chat_id):
    news_today, news_tomorrow = get_investing_news_api()

    msg = "📌 *События USD (★★★) на сегодня по Бишкеку (UTC+6):*\n\n"
    msg += "\n".join(news_today) if news_today else "Сегодня нет событий с важностью 3 звезды по USD."
    msg += "\n\n📌 *События USD (★★★) на завтра по Бишкеку (UTC+6):*\n\n"
    msg += "\n".join(news_tomorrow) if news_tomorrow else "Завтра нет событий с важностью 3 звезды по USD."

    await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_news_manual(update.effective_chat.id)

async def daily_task():
    while True:
        now = datetime.now(timezone.utc) + timedelta(hours=6)  # Бишкек
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        await send_news_manual(CHAT_ID)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    webhook_url = f"{APP_URL}/webhook"
    await app.bot.set_webhook(webhook_url)
    print(f"Webhook установлен: {webhook_url}")

    asyncio.create_task(daily_task())

    await app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        path="/webhook"
    )

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
