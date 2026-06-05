import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv("data.env")

USER1_USERNAME = os.getenv("USER1_USERNAME")
USER1_PASSWORD = os.getenv("USER1_PASSWORD")
USER2_USERNAME = os.getenv("USER2_USERNAME")
USER2_PASSWORD = os.getenv("USER2_PASSWORD")

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

    BOLTON_SPYDUS = "https://bolton.spydus.co.uk/cgi-bin/spydus.exe/MSGTRN/OPAC/HOME"

    page.goto(BOLTON_SPYDUS)

    # clicking login button to show login area
    login_button = page.locator('button[id="navbarLoginMenuLink1"]')
    login_button.wait_for(state='visible')
    login_button.click()

    # inserting credentials
    page.locator("#user_name").wait_for(state="visible")
    page.locator("#user_name").fill(USER2_USERNAME)
    page.locator("#user_password").fill(USER2_PASSWORD)
    page.locator(".btn-submit").click()

    # find currently borrowed items
    page.locator(".brw-dashboard-item").first.wait_for(state="visible")
    page.locator(".brw-dashboard-item").first.click()

    # check borrowed books
    library_books = {}
    rows = page.locator("tr").all()
    book_num = 1

    for row in rows:
        if row.locator("h3.card-title").count() == 0:
            continue
        title = row.locator("h3.card-title").first.inner_text()
        extracted_date = row.locator('td[data-caption="Due"] span').first.inner_text()
        due_date_obj = datetime.strptime(extracted_date, "%A, %d %B %Y").date()
        due_date = due_date_obj.strftime("%Y-%m-%d")
        status_loc = row.locator('td[data-caption="Status"] span')
        status_text = status_loc.first.inner_text() if status_loc.count() > 0 else ""
        renewed = int(status_text.replace("Renewed", "").replace(" times", "").replace(" time", "").strip()) if status_text else 0
        library_books[book_num] = {"title": title, "due_date": due_date_obj, "renewed": renewed}   
        book_num += 1

    print(library_books)
    print(f"{len(library_books)} books borrowed")

    # go through each borrowed book
    for book_num, book in library_books.items():
        # give alert if it's already renewed twice
        if book["renewed"] >= 2:
            print(f"{book['title']} must be returned before {book['due_date']}. Cannot be renewed")
        # check if due date is closer than x days and check the tickbox
        day_dfference = (book["due_date"] - today).days
        if day_dfference <= 10:
            page.locator(f"#selCheck{book_num}").click()
    # renew all the books that got ticked in checkbox
    page.get_by_role("link", name="Renew selections").click()

    # # clicking user menu and logout
    # page.locator("#navbarLoginMenuLinkName").click()
    # page.get_by_role("link", name="Logout").first.click()

    # here to not to close the screen
    input("Press Enter to close the browser...")