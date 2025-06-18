import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from datetime import datetime, time as dtime
import asyncio

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

def get_investing_news():
    url = 'https://ru.investing.com/economic-calendar/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, 'lxml')
    today = datetime.now().strftime('%Y-%m-%d')
    news = []
    for ev in soup.find_all('tr', {'class': 'js-event-item'}):
        try:
            if ev.get('data-currency') != 'USD': continue
            if ev.get('data-event-datetime').split()[0] != today: continue
            stars = len(ev.find('td', class_='sentiment').find_all('i', class_='grayFullBullishIcon'))
            if stars == 3:
                title = ev.find('td', class_='event').get_text(strip=True)
                tm = ev.find('td', class_='time').get_text(strip=True)
                news.append(f"{tm} – {title} (★★★)")
        except: pass
    return news

async def send_news_manual(chat_id):
    news = get_investing_news()
    if news:
        msg = "📌 *Сегодня важные USD‑события (★★★):*\n\n" + "\n".join(news)
    else:
        msg = "Сегодня нет событий с важностью 3 звезды по USD."
    await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_news_manual(update.effective_chat.id)

async def daily_task():
    while True:
        now = datetime.now()
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now > target:
            target = target.replace(day=now.day + 1)
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

# 🛠️ Исправление здесь:
if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()   # 👈 добавляем поддержку вложенных event loops (важно для Railway)
    asyncio.get_event_loop().run_until_complete(main())
