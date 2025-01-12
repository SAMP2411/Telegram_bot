import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
import asyncio
import time
from flask import Flask

# Telegram bot token and chat ID
BOT_TOKEN = "7971492257:AAGCOY0gtv6UrZ0cADBifYnhuGPLTRxdoS0"
CHAT_ID = "954847172"  # Replace with your Telegram chat ID

# URL to monitor
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"

# Intervals for updates (in seconds)
CHECK_INTERVAL = 300  # 5 minutes for checking offers
HOURLY_UPDATE_INTERVAL = 3600  # 1 hour for hourly updates

# Create a Flask app
app = Flask(__name__)

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
async def monitor_website(bot):
    last_update_time = time.time()
    offers_last_state = None  # Tracks the last known state of offers (None if no offers)

    while True:
        current_time = time.time()

        # Check for offers every 5 minutes
        if current_time % CHECK_INTERVAL < 1:  # Ensures checks happen every 5 minutes
            current_offers = fetch_offers()

            if current_offers:
                if offers_last_state is None:  # If previously no offers, send a new offers update
                    for offer in current_offers:
                        message = f"New Offer: <b>{offer['title']}</b>\n<a href='{offer['link']}'>View Offer</a>"
                        await send_message(bot, message)

                offers_last_state = current_offers  # Update last state to current offers

            else:
                if offers_last_state is not None:  # If previously offers were detected, send "No offers" update
                    await send_message(bot, "No offers available at the moment.")

                offers_last_state = None  # Update last state to no offers

        # Send hourly updates regardless of changes
        if current_time - last_update_time >= HOURLY_UPDATE_INTERVAL:
            if offers_last_state:
                await send_message(bot, "Offers are still available.")
            else:
                await send_message(bot, "No offers available at the moment.")

            last_update_time = time.time()  # Update the time for the last hourly update

        await asyncio.sleep(1)  # Avoid high CPU usage

# Background task for monitoring
@app.before_first_request
def start_monitor():
    bot = Bot(BOT_TOKEN)
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_website(bot))

# Define a simple endpoint for health checks
@app.route("/")
def health_check():
    return "Bot is running."

# Main function to run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
