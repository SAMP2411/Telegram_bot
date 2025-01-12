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
INITIAL_UPDATE_INTERVAL = 120  # 2 minutes for the initial "No offers" update
CHECK_INTERVAL = 300  # 5 minutes for checking offers
HOURLY_UPDATE_INTERVAL = 3600  # 1 hour for updates after detecting offers


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
    last_hourly_update_time = 0  # Tracks the last time an hourly update was sent
    offers_detected = False  # Tracks if offers have been detected
    no_offer_message_sent = False  # Tracks if the initial "No offers" message has been sent

    while True:
        current_time = time.time()

        # Check for offers every 5 minutes
        if current_time % CHECK_INTERVAL < 1:  # Ensures checks happen every 5 minutes
            current_offers = fetch_offers()

            if current_offers:
                offers_detected = True
                no_offer_message_sent = True  # Prevent further "No offers" messages
                for offer in current_offers:
                    message = f"New Offer: <b>{offer['title']}</b>\n<a href='{offer['link']}'>View Offer</a>"
                    await send_message(bot, message)
                last_hourly_update_time = current_time  # Reset hourly update timer on new offers
            elif not no_offer_message_sent:
                # Initial "No offers" update after 2 minutes
                if current_time - start_time >= INITIAL_UPDATE_INTERVAL:
                    await send_message(bot, "No offers available at the moment.")
                    no_offer_message_sent = True  # Mark as sent to avoid repeated messages

        # Send hourly updates if offers were detected
        if offers_detected and current_time - last_hourly_update_time >= HOURLY_UPDATE_INTERVAL:
            await send_message(bot, "Offers are still available.")
            last_hourly_update_time = current_time  # Update hourly update time

        await asyncio.sleep(1)  # Avoid high CPU usage


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
