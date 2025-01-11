import requests
from bs4 import BeautifulSoup
from telegram import Bot
import time
import os

# Telegram bot token and chat ID
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')  # Replace with your Telegram chat ID

# URL to monitor
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"

# Interval for checking updates (in seconds)
CHECK_INTERVAL = 300  # 5 minutes

# Function to fetch offers from the website
def fetch_offers():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check for the presence of the "No offers" or "Keine Angebote" message
    no_offers_element = soup.find("header", class_="notification__header")
    
    if no_offers_element:
        no_offers_text = no_offers_element.get_text()
        if "No offers" in no_offers_text or "Keine Angebote" in no_offers_text:
            print("No offers available.")
            return None  # No offers available

    # If no "No offers" message, extract available offers (replace with actual classes)
    offers = []
    offer_elements = soup.select(".your-offer-class")  # Adjust this to match the actual offer element class
    for offer in offer_elements:
        title = offer.select_one(".title-class").get_text(strip=True)  # Adjust this as needed
        link = offer.select_one("a")["href"]
        offers.append({"title": title, "link": link})

    return offers

# Function to send Telegram message
def send_message(bot, message):
    bot.send_message(chat_id=CHAT_ID, text=message)

# Monitor function to check for updates
def monitor_website(bot):
    while True:
        print("Checking for updates...")  # This line will be printed once each cycle
        current_offers = fetch_offers()

        if current_offers:
            for offer in current_offers:
                message = f"New Offer: {offer['title']}\n{offer['link']}"
                send_message(bot, message)
        
        time.sleep(CHECK_INTERVAL)

# Main function to run the bot
def main():
    bot = Bot(BOT_TOKEN)

    print("Starting bot...")
    monitor_website(bot)

if __name__ == "__main__":
    main()
