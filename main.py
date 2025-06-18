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
                
                # Определяем важность события по количеству "звёзд"
                impact_element = event.find('td', {'class': 'sentiment'})
                if impact_element:
                    stars = impact_element.find_all('i', {'class': 'grayFullBullishIcon'})
                    impact_level = len(stars)
                else:
                    impact_level = 0

                if impact_level == 3:  # Только события с 3 звездами
                    news_list.append(f"{time_str} - {title} (★★★)")
        except Exception as e:
            continue

    return news_list

def send_news():
    news = get_investing_news()
    if news:
        message = "📌 *Сегодня важные события по USD (Важность: 3 звезды):*\n\n" + "\n".join(news)
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        print("Сегодня нет событий с важностью 3 звезды.")

# Проверять каждый день в 08:00 утра
schedule.every().day.at("08:00").do(send_news)

print("Бот запущен...")

while True:
    schedule.run_pending()
    time.sleep(60)
