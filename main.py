import os
import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import asyncio

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

def get_investing_news_api(day_offset=0):
    tz_offset = 6  # UTC+6 Бишкек
    date_target = datetime.now(timezone.utc) + timedelta(hours=tz_offset, days=day_offset)
    date_str = date_target.strftime('%Y-%m-%d')

    url = 'https://ru.investing.com/economic-calendar/Service/getCalendarFilteredData'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'  # <== важно!
    }
    data = {
        'timeZone': '18',  # UTC+6
        'country[]': '5',  # США
        'importance[]': '3',  # 3 звезды
        'dateFrom': date_str,
        'dateTo': date_str
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        print(f"Ошибка API: {response.status_code} {response.text}")
        return []

    try:
        json_data = response.json()
    except Exception as e:
        print("Ошибка JSON:", e)
        print("Ответ сервера:", response.text)
        return []

    html = json_data.get('data', '')
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')

    events = []
    for ev in soup.find_all('tr', {'event_row': True}):
        try:
            time = ev.find('td', {'class': 'time'}).get_text(strip=True)
            title = ev.find('td', {'class': 'event'}).get_text(strip=True)
            events.append(f"{time} Бишкек – {title} (★★★)")
        except Exception as e:
            print("Ошибка обработки события:", e)

    return events

async def send_news_manual(chat_id):
    news_today = get_investing_news_api(0)
    news_tomorrow = get_investing_news_api(1)

    msg = "📌 *События USD (★★★) на сегодня по Бишкеку (UTC+6):*\n\n"
    msg += "\n".join(news_today) if news_today else "Сегодня нет событий с важностью 3 звезды по USD."
    msg += "\n\n📌 *События USD (★★★) на завтра по Бишкеку (UTC+6):*\n\n"
    msg += "\n".join(news_tomorrow) if news_tomorrow else "Завтра нет событий с важностью 3 звезды по USD."

    await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_news_manual(update.effective_chat.id)

async def daily_task():
    while True:
        now = datetime.utcnow() + timedelta(hours=6)
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        await send_news_manual(CHAT_ID)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    await send_news_manual(CHAT_ID)
    asyncio.create_task(daily_task())

    print("Бот запущен и ждёт команд...")
    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())