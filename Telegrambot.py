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

# Intervals for updates (in seconds)
INITIAL_UPDATE_INTERVAL = 120  # 2 minutes for the initial update
CHECK_INTERVAL = 300  # 5 minutes for checking offers
HOURLY_UPDATE_INTERVAL = 3600  # 1 hour for regular updates


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
    
    # Await bot connection and display bot name
    bot_info = await bot.get_me()
    print(f"Bot {bot_info['first_name']} connected successfully!")
    
    start_time = time.time()
    last_hourly_update_time = 0
    initial_message_sent = False

    while True:
        current_time = time.time()

        # Check for offers
        current_offers = fetch_offers()

        if current_offers:
            for offer in current_offers:
                message = f"New Offer: <b>{offer['title']}</b>\n<a href='{offer['link']}'>View Offer</a>"
                await send_message(bot, message)
        else:
            if not initial_message_sent and current_time - start_time >= INITIAL_UPDATE_INTERVAL:
                await send_message(bot, "No offers available at the moment.")
                initial_message_sent = True

        # Hourly updates regardless of offers
        if current_time - last_hourly_update_time >= HOURLY_UPDATE_INTERVAL:
            if current_offers:
                await send_message(bot, "Offers are still available.")
            else:
                await send_message(bot, "No offers available at the moment.")
            last_hourly_update_time = current_time

        await asyncio.sleep(CHECK_INTERVAL)  # Check every 5 minutes


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
    app.run(host="0.0.0.0", port=8080)  # Render expects the app to run on port 8080
