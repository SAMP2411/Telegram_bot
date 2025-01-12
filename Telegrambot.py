import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
import asyncio
from flask import Flask
import threading

# Telegram bot credentials
BOT_TOKEN = "7971492257:AAGCOY0gtv6UrZ0cADBifYnhuGPLTRxdoS0"
CHAT_ID = "954847172"

# Monitoring URL
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"

UPDATE_INTERVAL = 120  # 2 minutes in seconds


def fetch_offers():
    """
    Fetch and parse the website for offers.
    Returns a list of offers or None if no offers are available.
    """
    try:
        response = requests.get(URL)
        soup = BeautifulSoup(response.text, "html.parser")

        # Detect "No offers" message
        no_offers_element = soup.find("header", class_="notification__header")
        if no_offers_element and "No offers" in no_offers_element.get_text():
            return None

        # Extract available offers
        offers = []
        offer_elements = soup.select(".your-offer-class")  # Replace with actual class for offers
        for offer in offer_elements:
            title = offer.select_one(".title-class").get_text(strip=True)  # Adjust selector
            link = offer.select_one("a")["href"]
            offers.append({"title": title, "link": link})

        return offers
    except Exception as e:
        print(f"Error fetching offers: {e}")
        return None


async def send_message(bot, message):
    """
    Send a message to the Telegram bot.
    """
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Error sending message: {e}")


async def monitor_website():
    """
    Monitor the website and send updates every 2 minutes.
    """
    bot = Bot(BOT_TOKEN)
    bot_info = await bot.get_me()
    print(f"Bot {bot_info['first_name']} connected successfully!")

    while True:
        # Fetch current offers
        current_offers = fetch_offers()

        if current_offers:
            for offer in current_offers:
                message = f"New Offer: <b>{offer['title']}</b>\n<a href='{offer['link']}'>View Offer</a>"
                await send_message(bot, message)
        else:
            await send_message(bot, "No offers available at the moment.")

        # Wait for the next interval
        await asyncio.sleep(UPDATE_INTERVAL)


# Flask application for Render
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running and monitoring offers!"


def start_monitoring():
    threading.Thread(target=lambda: asyncio.run(monitor_website())).start()


if __name__ == '__main__':
    start_monitoring()
    app.run(host="0.0.0.0", port=8080)
