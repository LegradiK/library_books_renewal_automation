import io
import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from bolton_library import renew_library_books
from borrowbox import renew_borrowbox_books
from email_report import build_html_report, build_text_report

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

results = []

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        results += renew_library_books(page, user_list, today)
        results += renew_borrowbox_books(page, user_list, today)
finally:
    sys.stdout = sys.__stdout__

print(buffer.getvalue())

msg = MIMEMultipart("alternative")
msg["Subject"] = f"Library Renewal Report – {today}"
msg["From"] = EMAIL_SENDER
msg["To"] = EMAIL_RECIPIENT
msg.attach(MIMEText(build_text_report(results, today), "plain"))
msg.attach(MIMEText(build_html_report(results, today), "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
    smtp.send_message(msg)
