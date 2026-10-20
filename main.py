import os
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
CHECK_URL = "https://testcisia.it/calendario.php?tolc=cents&lingua=inglese"  # Update with your target URL
KEYWORDS = ["CENT-S@HOME", "dates available", "book now"]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing Telegram credentials.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def check_website():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(CHECK_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text().lower()
        
        for keyword in KEYWORDS:
            if keyword.lower() in page_text:
                return True, keyword
        return False, None
    except Exception as e:
        print(f"Error scraping URL: {e}")
        return False, None

if __name__ == "__main__":
    print(f"Checking {CHECK_URL}...")
    found, keyword = check_website()
    if found:
        print(f"Match detected: {keyword}")
        alert_msg = f"🚨 *EXAM DATES DETECTED!* 🚨\n\nKeyword found: `{keyword}`\nURL: {CHECK_URL}"
        send_telegram_alert(alert_msg)
    else:
        print("No matching keywords found. Exiting normally.")
