import io
import os
import smtplib
import sys
from datetime import date
from email.mime.text import MIMEText

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from bolton_library import renew_library_books
from borrowbox import renew_borrowbox_books

sys.stdout.reconfigure(line_buffering=True)

load_dotenv("data.env")

USER1_USERNAME = os.getenv("USER1_USERNAME")
USER1_PASSWORD = os.getenv("USER1_PASSWORD")
USER2_USERNAME = os.getenv("USER2_USERNAME")
USER2_PASSWORD = os.getenv("USER2_PASSWORD")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

user_list = [[USER1_USERNAME, USER1_PASSWORD], [USER2_USERNAME, USER2_PASSWORD]]

today = date.today()

buffer = io.StringIO()
sys.stdout = buffer

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        renew_library_books(page, user_list, today)
        # renew_borrowbox_books(page, user_list, today)
finally:
    sys.stdout = sys.__stdout__

output = buffer.getvalue()
print(output)

msg = MIMEText(output)
msg["Subject"] = f"Library Renewal Report – {today}"
msg["From"] = EMAIL_SENDER
msg["To"] = EMAIL_RECIPIENT

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
    smtp.send_message(msg)
