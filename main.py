import os
from datetime import date
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from bolton_library import renew_library_books
from borrowbox import renew_borrowbox_books

load_dotenv("data.env")

USER1_USERNAME = os.getenv("USER1_USERNAME")
USER1_PASSWORD = os.getenv("USER1_PASSWORD")
USER2_USERNAME = os.getenv("USER2_USERNAME")
USER2_PASSWORD = os.getenv("USER2_PASSWORD")
user_list = [[USER1_USERNAME, USER1_PASSWORD], [USER2_USERNAME, USER2_PASSWORD]]

today = date.today()

with sync_playwright() as pw:
    # create browser instance
    browser = pw.chromium.launch(
        # we can choose either a Headful (With GUI) or Headless mode:
        headless=False,
    )
    # create context
    # using context we can define page properties like viewport dimensions
    context = browser.new_context(
        # most common desktop viewport is 1920x1080
        viewport={"width": 1920, "height": 1080}
    )
    # create page aka browser tab which we'll be using to do everything
    page = context.new_page()

    # renew_library_books(page, user_list, today)
    renew_borrowbox_books(page, user_list, today)

    # here to not to close the screen
    input("Press Enter to close the browser...")
