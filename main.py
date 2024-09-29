import os
os.environ['MOZ_HEADLESS'] = '1'
import requests
import time
import re
import logging
from bs4 import BeautifulSoup
from colorama import init, Fore, Style, Back
import schedule
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


# Set up Selenium with Firefox in headless mode
def setup_firefox_driver():
    options = Options()
    options.headless = True  # Enable headless mode
    logging.info(Fore.CYAN + "Setting up Firefox WebDriver in headless mode...")

    try:
        service = FirefoxService(executable_path=GECKODRIVER_PATH)  # Specify the path to geckodriver
        driver = webdriver.Firefox(service=service, options=options)
        logging.info(Fore.CYAN + "Firefox WebDriver has been successfully initialized in headless mode.")
        return driver
    except Exception as e:
        logging.error(Fore.RED + f"❌ Error initializing Firefox WebDriver in headless mode: {e}")
        raise

# Initialize colorama for Windows
init(autoreset=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Your Discord Webhook URL
WEBHOOK_URL = 'https://discord.com/api/webhooks/{ADD_YOUR_WEBHOOK_HERE}'  # Add your Discord Webhook 

# Sploitus RSS Feed URL
RSS_FEED_URL = 'https://sploitus.com/rss'

# Minimum CVE score to filter exploits
MIN_CVE_SCORE = 7.0

# Global counts for processed and skipped exploits
processed_count = 0
skipped_count = 0

# Store processed exploits to avoid duplicates
processed_exploits = set()

# Path to the Firefox geckodriver
GECKODRIVER_PATH = './driver/geckodriver.exe'

# Function to send embeds to Discord
def send_to_discord(title, description, url, pub_date=None, cve_score=None, search_term=None, logo_url=None, color=0x7289DA):
    embed = {
        "title": title,
        "description": description,
        "url": url,
        "color": color
    }

    # Adding CVE score and publication date to the embed fields
    if cve_score is not None:
        embed["fields"] = [
            {"name": "CVE Score", "value": str(cve_score), "inline": True},
            {"name": "Date", "value": pub_date, "inline": True}
        ]

    # Adding search term as a footer
    if search_term:
        embed["footer"] = {"text": f"Search term: {search_term}"}

    # Adding the logo as a thumbnail if available
    if logo_url:
        embed["thumbnail"] = {"url": logo_url}

    data = {"embeds": [embed]}

    # Attempting to send the data to Discord
    while True:
        try:
            response = requests.post(WEBHOOK_URL, json=data)
            response.raise_for_status()  # Raise an exception for any 4XX/5XX responses

            if response.status_code == 429:  # Rate limited
                retry_after = response.json().get("retry_after", 1000)
                logging.warning(Fore.YELLOW + f"Rate limited, retrying after {retry_after} milliseconds...")
                time.sleep(retry_after / 1000)
            else:
                logging.info(Fore.GREEN + Style.BRIGHT + f"✅ Successfully sent exploit: {title}")
                break  # Exit the loop if the message was sent successfully
        except requests.RequestException as e:
            logging.error(Fore.RED + f"❌ Error sending to Discord: {e}")
            break

# Function to search for exploits on Sploitus by title or CVE score
def search_exploit(search_term=None, cve_score=None, title_only=False):
    try:
        # Log the type of search being performed
        search_scope = "Title only" if title_only else "Title and Description"
        logging.info(
            Fore.CYAN + Style.BRIGHT + f"\n🔍 Searching for exploits related to: {Fore.YELLOW + (search_term if search_term else f'CVE Score >= {cve_score}')}, Scope: {search_scope}")

        # Construct the search URL with the appropriate query parameters
        search_url = f"https://sploitus.com/?query={search_term.replace(' ', '%20')}&is-title={'true' if title_only else 'false'}#exploits"
        logging.info(Fore.CYAN + f"Using search URL: {search_url}")

        # Set up Selenium with Firefox
        driver = setup_firefox_driver()

        # Visit the search URL
        driver.get(search_url)

        # Allow the page to load
        time.sleep(3)  # Adjust based on network speed

        # Sort by score
        try:
            sort_button = driver.find_element(By.XPATH, "//span[@id='sort' and @data-id='score']")
            ActionChains(driver).move_to_element(sort_button).click(sort_button).perform()
            logging.info(Fore.GREEN + "✅ Sorted by CVE Score")
        except Exception as e:
            logging.error(Fore.RED + f"❌ Failed to sort by CVE Score: {e}")

        # Scroll down to load more results with a limit on iterations
        max_scrolls = 3
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Extract the exploit entries
        exploit_items = driver.find_elements(By.CSS_SELECTOR, 'label.tile.tile-centered')

        if not exploit_items:
            logging.info(Fore.YELLOW + f"⚠️ No results found for: {search_term}")
            driver.quit()
            return

        found = False

        for exploit in exploit_items:
            try:
                # Extract the title
                title_tag = exploit.find_element(By.CLASS_NAME, 'accordion-header')
                title = title_tag.text.strip()

                # Extract the publication date
                pub_date_tag = exploit.find_element(By.CLASS_NAME, 'tile-subtitle')
                pub_date = pub_date_tag.text.strip()

                # Extract the CVE score (if available)
                try:
                    cve_score_tag = exploit.find_element(By.CSS_SELECTOR, '.tile-icon.badge')
                    score = float(cve_score_tag.get_attribute('data-badge'))
                except:
                    score = None

                # Extract the logo class to be used as an icon
                try:
                    logo_tag = exploit.find_element(By.CLASS_NAME, 'avatar')
                    logo_class = logo_tag.get_attribute('class')
                    logo_url = f"https://sploitus.com/static/images/{logo_class.split()[-1]}.png"
                except:
                    logo_url = None

                # Extract the link (if available)
                try:
                    link_tag = exploit.find_element(By.TAG_NAME, 'a')
                    link = link_tag.get_attribute('href')
                except:
                    link = "https://sploitus.com"

                # Only process and send exploits with a CVE score between 7.0 and 10
                if score is not None and 7.0 <= score <= 10.0:
                    # Build the description
                    description = f"Published on: {pub_date}\nCVE Score: {score}\n[Read more here]({link})"

                    # Send the exploit data to Discord
                    logging.info(Fore.GREEN + f"✅ Preparing to send exploit: {title}")
                    send_to_discord(title, description, link, pub_date, score, search_term, logo_url)
                    found = True
                    logging.info(Fore.GREEN + f"✅ Sent exploit: {title}")

            except Exception as e:
                logging.error(Fore.RED + f"❌ Error processing exploit: {e}")

        if not found:
            logging.info(Fore.YELLOW + f"⚠️ No matching exploits found for: {search_term} with CVE Score >= 7.0")

        driver.quit()

    except Exception as e:
        logging.error(Fore.RED + f"❌ Unexpected error: {e}")

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
    start_time = time.time()  # Record start time
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

            # Check if the exploit has already been processed
            if title in processed_exploits:
                logging.info(Fore.YELLOW + f"⚠️ Skipping duplicate exploit: {title}")
                skipped_count += 1
                continue

            cve_score = extract_cve_score(title)

            # Process all exploits, regardless of whether a CVE score is found
            description = f"Published on: {pub_date}\nCVE Score: {cve_score if cve_score else 'N/A'}\n[Read more here]({link})"
            logging.info(Fore.CYAN + f"🔄 Processing exploit: {Fore.GREEN + title}")
            logging.info(Fore.YELLOW + f"✅ Sending to Discord | CVE Score: {cve_score if cve_score else 'N/A'}\n")

            send_to_discord(title, description, link, pub_date, cve_score)
            processed_exploits.add(title)
            processed_count += 1
            time.sleep(1)

        end_time = time.time()  # Record end time
        elapsed_time = end_time - start_time  # Calculate elapsed time
        logging.info(Fore.GREEN + "\n===== Exploit Processing Complete =====")
        logging.info(Fore.CYAN + f"Total Processed: {Fore.GREEN + str(processed_count)} | Total Skipped: {Fore.RED + str(skipped_count)}")
        logging.info(Fore.CYAN + f"Processing Time: {Fore.GREEN + str(round(elapsed_time, 2))} seconds\n")

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
