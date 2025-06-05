import time
import smtplib
from email.message import EmailMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"
SHEET_NAME = "Form Responses 1"  # Replace with your sheet tab name

# Email sending account
EMAIL_ADDRESS = "launchpad.ignitex@gmail.com"  # Replace with your sender Gmail
EMAIL_PASSWORD = "launchpad2025"   # Use an app password

def send_email(name, to_email):
    msg = EmailMessage()
    msg["Subject"] = "Thank You for Registering!"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(f"Hi {name},\n\nThanks for registering!\nWe're glad to have you on board.\n\nBest regards,\nIGNITEX")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print(f"✅ Email sent to {name} <{to_email}>")

def main():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE").worksheet(SHEET_NAME)

    sent_log = set()
    try:
        with open("sent_log.txt", "r") as f:
            sent_log = set(line.strip() for line in f)
    except FileNotFoundError:
        pass

    while True:
        data = sheet.get_all_records()
        for row in data:
            name = row.get("Full Name")
            email = row.get("Email")

            if email and email not in sent_log:
                try:
                    send_email(name, email)
                    with open("sent_log.txt", "a") as f:
                        f.write(email + "\n")
                    sent_log.add(email)
                except Exception as e:
                    print(f"❌ Failed to send to {email}: {e}")

        time.sleep(15)  # Wait 15 seconds and check again

if __name__ == "__main__":
    main()
