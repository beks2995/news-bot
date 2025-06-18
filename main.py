import os
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from dotenv import load_dotenv
import schedule
import time
from datetime import datetime
import asyncio

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
CHAT_ID = os.getenv("CHAT_ID")

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

async def send_news():
    news = get_investing_news()
    if news:
        msg = "📌 *Сегодня важные USD‑события (★★★):*\n\n" + "\n".join(news)
    else:
        msg = "Сегодня нет событий с важностью 3 звезды по USD."
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

def job():
    asyncio.run(send_news())

# 👉 Сразу отправляем новости при старте:
job()

# 👉 Планируем отправку каждый день в 08:00:
schedule.every().day.at("08:00").do(job)

print("Бот запущен и ждёт следующей проверки...")

while True:
    schedule.run_pending()
    time.sleep(60)
