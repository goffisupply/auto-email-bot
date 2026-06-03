import os
import re
import time
import logging
import smtplib
from email.message import EmailMessage

import gspread
from google.oauth2.service_account import Credentials

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- Config from environment variables ---
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "launchpad.ignitex@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Store in .env or environment
SHEET_ID = os.environ.get("SHEET_ID")              # Your Google Sheet ID
SHEET_NAME = os.environ.get("SHEET_NAME", "Form Responses 1")
CREDS_FILE = os.environ.get("CREDS_FILE", "credentials.json")
SENT_LOG = "sent_log.txt"
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", 15))  # seconds
MAX_RETRIES = 3

# --- Google Sheets Auth (modern google-auth) ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

def get_sheet():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# --- Email validation ---
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return re.match(pattern, str(email)) is not None

# --- Send email with retry logic ---
def send_email(name, to_email, retries=MAX_RETRIES):
    if not EMAIL_PASSWORD:
        logger.error("EMAIL_PASSWORD environment variable is not set.")
        return False

    msg = EmailMessage()
    msg["Subject"] = "Thank You for Registering!"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(
        f"Hi {name},\n\n"
        f"Thanks for registering!\n"
        f"We're glad to have you on board.\n\n"
        f"Best regards,\nIGNITEX"
    )

    for attempt in range(1, retries + 1):
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)
            logger.info(f"✅ Email sent to {name} <{to_email}>")
            return True
        except Exception as e:
            logger.warning(f"Attempt {attempt}/{retries} failed for {to_email}: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)  # exponential-ish backoff

    logger.error(f"❌ All {retries} attempts failed for {to_email}")
    return False

# --- Load sent log ---
def load_sent_log():
    try:
        with open(SENT_LOG, "r") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

# --- Save to sent log ---
def mark_sent(email):
    with open(SENT_LOG, "a") as f:
        f.write(email.strip() + "\n")

# --- Main loop ---
def main():
    if not SHEET_ID:
        logger.error("SHEET_ID environment variable is not set. Exiting.")
        return

    logger.info("🚀 Auto Email Bot started.")

    while True:
        try:
            sheet = get_sheet()
            sent_log = load_sent_log()
            data = sheet.get_all_records()

            for row in data:
                name = row.get("Full Name", "").strip()
                email = row.get("Email", "").strip()

                if not email or not is_valid_email(email):
                    continue

                if email in sent_log:
                    continue

                success = send_email(name or "there", email)
                if success:
                    mark_sent(email)

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")

        logger.info(f"⏳ Sleeping {POLL_INTERVAL}s before next check...")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
