import os
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from dotenv import load_dotenv
import schedule
import time
from datetime import datetime

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TELEGRAM_TOKEN)

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
                
                impact_element = event.find('td', {'class': 'sentiment'})
                if impact_element:
                    stars = impact_element.find_all('i', {'class': 'grayFullBullishIcon'})
                    impact_level = len(stars)
                else:
                    impact_level = 0

                if impact_level == 3:
                    news_list.append(f"{time_str} - {title} (★★★)")
        except Exception:
            continue

    return news_list

def send_news():
    news = get_investing_news()
    if news:
        message = "📌 *Сегодня важные события по USD (Важность: 3 звезды):*\n\n" + "\n".join(news)
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
    else:
        bot.send_message(chat_id=CHAT_ID, text="Сегодня нет событий с важностью 3 звезды по USD.")

# 👉 Сразу отправляем новости при старте:
send_news()

# 👉 Планируем отправку каждый день в 08:00:
schedule.every().day.at("08:00").do(send_news)

print("Бот запущен и ждёт следующей проверки...")

while True:
    schedule.run_pending()
    time.sleep(60)
