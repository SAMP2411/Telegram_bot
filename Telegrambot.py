import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
import time
import threading
from flask import Flask

# Telegram bot token and chat ID
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"  # Replace with your Telegram chat ID

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
def send_message(bot, message):
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)


# Monitor function to check for updates
def monitor_website():
    bot = Bot(BOT_TOKEN)
    start_time = time.time()
    last_update_time = time.time()
    hourly_update_sent = False  # Tracks if an hourly update has been sent
    offers_detected = False  # Tracks if offers have been detected

    # Give some time for Flask to initialize before starting the monitoring loop
    time.sleep(5)  # Sleep for 5 seconds to ensure Flask is ready to handle requests

    while True:
        current_time = time.time()

        # Check if it's time for the initial "No offers" update (after 2 minutes)
        if not hourly_update_sent and current_time - start_time >= INITIAL_UPDATE_INTERVAL:
            send_message(bot, "No offers available at the moment.")
            hourly_update_sent = True  # Mark the initial update as sent

        # Check for offers every 5 minutes
        if current_time % CHECK_INTERVAL < 1:  # Ensures checks happen every 5 minutes
            current_offers = fetch_offers()

            if current_offers:
                offers_detected = True
                for offer in current_offers:
                    message = f"New Offer: <b>{offer['title']}</b>\n<a href='{offer['link']}'>View Offer</a>"
                    send_message(bot, message)

            else:
                if offers_detected:  # If offers were previously detected, send an update
                    send_message(bot, "No offers available at the moment.")
                else:
                    print("No new offers detected.")

            # Reset hourly update tracking
            last_update_time = time.time()

        # Send hourly updates if offers have been detected
        if offers_detected and current_time - last_update_time >= HOURLY_UPDATE_INTERVAL:
            current_offers = fetch_offers()

            if current_offers:
                send_message(bot, "Offers are still available.")
            else:
                send_message(bot, "No offers available at the moment.")

            last_update_time = time.time()  # Update the time for the last hourly update

        time.sleep(1)  # Avoid high CPU usage


# Flask app to run with Render
app = Flask(__name__)

# Start monitoring in a separate thread
def start_monitoring():
    thread = threading.Thread(target=monitor_website)
    thread.daemon = True
    thread.start()


@app.route('/')
def home():
    return "Bot is running."


if __name__ == '__main__':
    start_monitoring()  # Start the monitoring thread
    app.run(host="0.0.0.0", port=8080)  # Render expects the app to run on port 8080
