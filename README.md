# Sploitus RSS Exploit Watcher

**Sploitus RSS Exploit Watcher** is a Python script designed to automatically monitor the latest exploits posted on [Sploitus](https://sploitus.com) via their RSS feed. The script runs on a schedule, fetching new exploits, and posting details to a configured Discord webhook. It also allows manual searching by exploit name or CVE score.

## Features

- **Automated Fetching**: Automatically runs every day at 8 AM, fetching new exploits.
- **CVE Score Filtering**: Filters exploits based on a minimum CVE score (default: 7.0).
- **Discord Integration**: Posts detailed exploit information (title, CVE score, and link) to a Discord webhook.
- **Manual Searching**: Search for specific exploits by name or by CVE score directly from the command line.
- **Color-Coded Console Output**: Clear and color-coded output for better readability.

## Installation

Clone the repository:

```bash
git clone https://github.com/havokzero/SploitusRss.git
cd SploitusRss
pip install -r requirements.txt
```

Configure the `WEBHOOK_URL`:

Open `main.py` and replace the `WEBHOOK_URL` placeholder with your Discord webhook URL:

```python
WEBHOOK_URL = 'https://discord.com/api/webhooks/your_webhook_url_here'
```

Run the script:

```bash
python main.py
```

## Commands

- **Manually fetch the latest exploits from the RSS feed**:
  ```bash
  run
  ```

- **Search for exploits by a specific term, such as "SQL Injection"**:
  ```bash
  search <term>
  ```

- **Search for exploits with a CVE score equal to or greater than the specified value**:
  ```bash
  search-cve <score>
  ```

- **Exit the program**:
  ```bash
  exit
  ```

## Example Usage

```bash
[Waiting for input] Type 'run' to fetch exploits now, 'search <term>' to search for a specific exploit, 'search-cve <score>' to search by CVE score, or 'exit' to quit:
```

### Example Search:

```bash
search sql injection
```

The script will then search for exploits related to the term "SQL Injection" and post the results to the Discord webhook.

## Contribution

Contributions are welcome! Feel free to fork this repository, create a branch, and submit a pull request with your improvements or fixes.
