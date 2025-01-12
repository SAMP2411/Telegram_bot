import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
import time
import threading
import asyncio
from flask import Flask

# Telegram bot token and chat ID
BOT_TOKEN = "7971492257:AAGCOY0gtv6UrZ0cADBifYnhuGPLTRxdoS0"
CHAT_ID = "954847172"

# URL to monitor
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"

# Timed intervals for updates
UPDATE_SCHEDULE = [0, 120, 300, 600, 1800, 3600]  # Immediate, 2m, 5m, 10m, 30m, 1h
THREE_HOUR_INTERVAL = 10800  # 3 hours


# Function to fetch offers from the website
def fetch_offers():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check for the presence of the "No offers" message
    no_offers_element = soup.find("header", class_="notification__header")
    if no_offers_element and "No offers" in no_offers_element.get_text():
        return None  # No offers available

    # If offers are available, extract available offers (replace with actual classes)
    offers = []
    offer_elements = soup.select(".your-offer-class")  # Adjust this to match the actual offer element class
    for offer in offer_elements:
        title = offer.select_one(".title-class").get_text(strip=True)  # Adjust this as needed
        link = offer.select_one("a")["href"]
        offers.append({"title": title, "link": link})

    return offers


# Function to send Telegram message
async def send_message(bot, message):
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)


# Monitor function to check for updates
async def monitor_website():
    bot = Bot(BOT_TOKEN)
    bot_info = await bot.get_me()
    print(f"Bot {bot_info['first_name']} connected successfully!")

    start_time = time.time()
    schedule_index = 0
    last_update_time = start_time

    while True:
        current_time = time.time()

        # Check for offers
        current_offers = fetch_offers()

        # Send an update message
        if current_offers:
            for offer in current_offers:
                message = f"New Offer: <b>{offer['title']}</b>\n<a href='{offer['link']}'>View Offer</a>"
                await send_message(bot, message)
        else:
            await send_message(bot, "No offers available at the moment.")

        # Determine the next update interval
        if schedule_index < len(UPDATE_SCHEDULE) - 1:
            next_interval = UPDATE_SCHEDULE[schedule_index + 1]
            schedule_index += 1
        else:
            next_interval = THREE_HOUR_INTERVAL

        last_update_time = current_time
        await asyncio.sleep(next_interval)


# Flask app to run with Render
app = Flask(__name__)

# Start monitoring in a separate thread
def start_monitoring():
    threading.Thread(target=lambda: asyncio.run(monitor_website())).start()


@app.route('/')
def home():
    return "Bot is running."


if __name__ == '__main__':
    start_monitoring()
    app.run(host="0.0
