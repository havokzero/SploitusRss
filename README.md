# SploitusRss
Sploitus RSS feed to discord webhook

Sploitus RSS Exploit Watcher
Sploitus RSS Exploit Watcher is a Python script designed to automatically monitor the latest exploits posted on Sploitus via their RSS feed. It can be scheduled to run daily, automatically fetching new exploits and filtering them based on CVE scores. Additionally, you can search for specific exploits by name or by CVE score, with the results posted to a Discord webhook.

Features
Automated Fetching: Runs automatically at 8 AM daily to fetch the latest exploits from Sploitus.
CVE Filtering: Filters exploits based on a configurable minimum CVE score (default: 7.0).
Discord Integration: Posts exploit details to a Discord channel via a webhook, including title, CVE score, and link.
Manual Search: Search for specific exploits by name or filter by CVE score directly from the command line.
Beautiful Console Output: Color-coded and easy-to-read console output for better clarity during processing.
Usage
Clone the repository:

bash
Copy code
git clone https://github.com/havokzero/SploitusRss.git
cd SploitusRss
Install the required dependencies:

bash
Copy code
pip install -r requirements.txt
Configure the WEBHOOK_URL in the script with your Discord webhook URL.

Run the script:

bash
Copy code
python main.py
Commands
run: Manually fetch the latest exploits.
search <term>: Search for exploits by a specific term (e.g., "SQL Injection").
search-cve <score>: Search for exploits with a CVE score equal to or higher than the specified value.
exit: Exit the program.
Contributions
Contributions are welcome! Feel free to fork the repository and submit a pull request.
