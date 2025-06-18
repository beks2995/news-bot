import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import asyncio

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

def get_investing_news(day_offset=0):
    url = 'https://ru.investing.com/economic-calendar/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, 'lxml')

    bishkek_tz = pytz.timezone('Asia/Bishkek')
    utc_tz = pytz.timezone('UTC')

    target_date = (datetime.now(bishkek_tz) + timedelta(days=day_offset)).date()
    news = []

    for ev in soup.find_all('tr', {'class': 'js-event-item'}):
        try:
            if ev.get('data-currency') != 'USD':
                continue

            dt_utc_str = ev.get('data-event-datetime')
            dt_utc = utc_tz.localize(datetime.strptime(dt_utc_str, '%Y-%m-%d %H:%M:%S'))
            dt_bishkek = dt_utc.astimezone(bishkek_tz)

            if dt_bishkek.date() != target_date:
                continue

            stars = len(ev.find('td', class_='sentiment').find_all('i', class_='grayFullBullishIcon'))
            if stars == 3:
                title = ev.find('td', class_='event').get_text(strip=True)
                tm = dt_bishkek.strftime('%H:%M')
                news.append(f"{tm} Бишкек – {title} (★★★)")
        except Exception as e:
            print("Ошибка при обработке события:", e)
            pass
    return news

async def send_news_manual(chat_id):
    news_today = get_investing_news(0)
    news_tomorrow = get_investing_news(1)

    msg = "📌 *События USD (★★★) на сегодня по Бишкеку (UTC+6):*\n\n"
    msg += "\n".join(news_today) if news_today else "Сегодня нет событий с важностью 3 звезды по USD."
    msg += "\n\n📌 *События USD (★★★) на завтра по Бишкеку (UTC+6):*\n\n"
    msg += "\n".join(news_tomorrow) if news_tomorrow else "Завтра нет событий с важностью 3 звезды по USD."

    await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_news_manual(update.effective_chat.id)

async def daily_task():
    bishkek_tz = pytz.timezone('Asia/Bishkek')
    while True:
        now = datetime.now(bishkek_tz)
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        await send_news_manual(CHAT_ID)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Сразу отправить при запуске
    await send_news_manual(CHAT_ID)

    # Запустить задачу авторассылки в фоне
    asyncio.create_task(daily_task())

    print("Бот запущен и ждёт команд...")
    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
