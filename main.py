import requests
import time
import re
import logging
from bs4 import BeautifulSoup
from colorama import init, Fore, Style, Back
import schedule
from datetime import datetime

# Initialize colorama for Windows
init(autoreset=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Placeholder for Discord Webhook URL
WEBHOOK_URL = 'https://discord.com/api/webhooks/your_webhook_url_here'  # Replace with your actual webhook URL

# Sploitus RSS Feed URL
RSS_FEED_URL = 'https://sploitus.com/rss'

# Minimum CVE score to filter exploits
MIN_CVE_SCORE = 7.0

# Global counts for processed and skipped exploits
processed_count = 0
skipped_count = 0


# Function to send embeds to Discord
def send_to_discord(title, description, url, pub_date=None, cve_score=None, search_term=None, color=0x7289DA):
    if WEBHOOK_URL == 'https://discord.com/api/webhooks/your_webhook_url_here':
        logging.error(Fore.RED + "❌ Webhook URL not set. Please provide a valid Discord Webhook URL.")
        return

    embed = {
        "title": title,
        "description": description,
        "url": url,
        "color": color
    }

    if cve_score is not None:
        embed["fields"] = [
            {"name": "CVE Score", "value": str(cve_score), "inline": True},
            {"name": "Date", "value": pub_date, "inline": True}
        ]

    if search_term:
        embed["footer"] = {"text": f"Search term: {search_term}"}

    data = {"embeds": [embed]}

    try:
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()  # Raise an exception for any 4XX/5XX responses
        if response.status_code == 429:  # Rate limited
            retry_after = response.json().get("retry_after", 1000)
            logging.warning(Fore.YELLOW + f"Rate limited, retrying after {retry_after} milliseconds...")
            time.sleep(retry_after / 1000)
            send_to_discord(title, description, url, pub_date, cve_score, search_term, color)  # Retry the message
        else:
            logging.info(Fore.GREEN + Style.BRIGHT + f"✅ Successfully sent exploit: {title}")
    except requests.RequestException as e:
        logging.error(Fore.RED + f"❌ Error sending to Discord: {e}")


# Function to search for exploits on Sploitus by title or CVE score
def search_exploit(search_term=None, cve_score=None):
    try:
        logging.info(
            Fore.CYAN + Style.BRIGHT + f"\n🔍 Searching for exploits related to: {Fore.YELLOW + (search_term if search_term else f'CVE Score >= {cve_score}')}")

        response = requests.get(RSS_FEED_URL)
        response.raise_for_status()
        feed = BeautifulSoup(response.text, 'xml')

        entries = feed.find_all('item')
        found = False

        for entry in entries:
            title = entry.find('title').get_text(strip=True)
            link = entry.find('link').get_text(strip=True)
            pub_date = entry.find('pubDate').get_text(strip=True)
            score = extract_cve_score(title)

            if search_term and search_term.lower() in title.lower():
                description = f"Published on: {pub_date}\nCVE Score: {score if score else 'N/A'}\n[Read more here]({link})"
                send_to_discord(title, description, link, pub_date, score, search_term)
                found = True
            elif cve_score and score is not None and score >= cve_score:
                description = f"Published on: {pub_date}\nCVE Score: {score}\n[Read more here]({link})"
                send_to_discord(title, description, link, pub_date, score)
                found = True

        if not found:
            logging.info(Fore.YELLOW + f"⚠️ No results found for: {search_term or f'CVE Score >= {cve_score}'}")

    except requests.RequestException as e:
        logging.error(Fore.RED + f"❌ Error occurred while searching: {e}")


# Main loop to handle scheduling and manual execution
def main_loop():
    logging.info(Fore.CYAN + Back.BLACK + Style.BRIGHT + "\n===== Exploit Watcher =====")
    logging.info(Fore.CYAN + "This program will automatically fetch exploits every day at 8 AM.")
    logging.info(
        Fore.CYAN + "You can also run it manually by typing 'run'. Type 'search <term>' to search for specific exploits. Type 'search-cve <score>' to search by CVE score. Type 'exit' to stop the program.\n")

    # Schedule the fetch_exploits function to run at 8 AM every day
    schedule.every().day.at("08:00").do(fetch_exploits)

    while True:
        schedule.run_pending()

        # User prompt for manual execution or search
        user_input = input(
            Fore.YELLOW + Style.BRIGHT + "[Waiting for input] Type 'run' to fetch exploits now, 'search <term>' to search for a specific exploit, 'search-cve <score>' to search by CVE score, or 'exit' to quit: ").strip().lower()

        if user_input == "run":
            logging.info(
                Fore.CYAN + Style.BRIGHT + f"Manual run initiated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            fetch_exploits()

        elif user_input.startswith("search "):
            search_term = user_input.replace("search ", "").strip()
            if search_term:
                search_exploit(search_term=search_term)
            else:
                logging.info(Fore.RED + "Please provide a search term.")

        elif user_input.startswith("search-cve "):
            try:
                search_cve_score = float(user_input.replace("search-cve ", "").strip())
                search_exploit(cve_score=search_cve_score)
            except ValueError:
                logging.info(Fore.RED + "Please provide a valid CVE score.")

        elif user_input == "exit":
            logging.info(Fore.RED + Style.BRIGHT + "Exiting program.")
            break

        time.sleep(1)


# Fetch and parse the RSS feed
def fetch_exploits():
    global processed_count, skipped_count
    processed_count = 0
    skipped_count = 0
    logging.info(Fore.CYAN + "\n===== Starting Exploit Processing =====\n")

    try:
        response = requests.get(RSS_FEED_URL)
        response.raise_for_status()
        feed = BeautifulSoup(response.text, 'xml')

        entries = feed.find_all('item')

        for entry in entries:
            title = entry.find('title').get_text(strip=True)
            link = entry.find('link').get_text(strip=True)
            pub_date = entry.find('pubDate').get_text(strip=True)

            cve_score = extract_cve_score(title)

            if cve_score is not None and cve_score >= MIN_CVE_SCORE:
                description = f"Published on: {pub_date}\nCVE Score: {cve_score}\n[Read more here]({link})"

                logging.info(Fore.CYAN + f"🔄 Processing exploit: {Fore.GREEN + title}")
                logging.info(Fore.YELLOW + f"✅ Sending to Discord | CVE Score: {cve_score}\n")

                send_to_discord(title, description, link, pub_date, cve_score)
                processed_count += 1
                time.sleep(1)

            else:
                logging.info(Fore.YELLOW + f"⚠️ Skipping exploit: {title} | CVE Score: Not found or too low\n")
                skipped_count += 1

        logging.info(Fore.GREEN + "\n===== Exploit Processing Complete =====")
        logging.info(
            Fore.CYAN + f"Total Processed: {Fore.GREEN + str(processed_count)} | Total Skipped: {Fore.RED + str(skipped_count)}\n")

    except requests.RequestException as e:
        logging.error(Fore.RED + f"❌ An error occurred during RSS fetch or processing: {e}")


# Extract CVE score from the title or description
def extract_cve_score(title):
    match = re.search(r'CVE-\d{4}-\d{4,7}.*?(\d\.\d)', title)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            logging.error(Fore.RED + f"❌ Error converting CVE score in title: {title}")
            return None
    return None


if __name__ == "__main__":
    main_loop()
