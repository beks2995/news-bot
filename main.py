import os
import requests
from bs4 import BeautifulSoup
import telegram
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

KEYWORDS = ['FOMC', 'CPI', 'GDP', 'Nonfarm', 'Non-Farm']

def get_investing_news():
    url = 'https://ru.investing.com/economic-calendar/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')

    today = datetime.now().strftime('%Y-%m-%d')

    events = soup.find_all('tr', {'class': 'js-event-item'})

    news_list = []

    for event in events:
        try:
            currency = event.get('data-currency')
            date = event.get('data-event-datetime').split(' ')[0]

            if currency == 'USD' and date == today:
                title = event.find('td', {'class': 'event'}).get_text(strip=True)
                time_str = event.find('td', {'class': 'time'}).get_text(strip=True)
                
                if any(keyword in title for keyword in KEYWORDS):
                    news_list.append(f"{time_str} - {title}")
        except Exception:
            continue

    return news_list

def send_news():
    news = get_investing_news()
    if news:
        message = "📌 *Сегодня важные события по USD:*\n\n" + "\n".join(news)
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        print("Сегодня нет важных событий.")

# Проверять каждый день в 08:00 утра
schedule.every().day.at("08:00").do(send_news)

print("Бот запущен...")

while True:
    schedule.run_pending()
    time.sleep(60)
