import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv("data.env")

USER1_USERNAME = os.getenv("USER1_USERNAME")
USER1_PASSWORD = os.getenv("USER1_PASSWORD")
USER2_USERNAME = os.getenv("USER2_USERNAME")
USER2_PASSWORD = os.getenv("USER2_PASSWORD")
user_list = [[USER1_USERNAME, USER1_PASSWORD], [USER2_USERNAME, USER2_PASSWORD]]

today = date.today()

def renew_library_books():
    BOLTON_SPYDUS = "https://bolton.spydus.co.uk/cgi-bin/spydus.exe/MSGTRN/OPAC/HOME"

    page.goto(BOLTON_SPYDUS)

    for user in user_list:

        # clicking login button to show login area
        login_button = page.locator('button[id="navbarLoginMenuLink1"]')
        login_button.wait_for(state='visible')
        login_button.click()

        # inserting credentials
        page.locator("#user_name").wait_for(state="visible")
        page.locator("#user_name").fill(user[0])
        page.locator("#user_password").fill(user[1])
        page.locator(".btn-submit").click()

        # find currently borrowed items
        try:
            page.locator(".brw-dashboard-item").first.wait_for(state="visible")
        except PlaywrightTimeoutError:
            print(f"User: {user[0]}\n"
                  f"No borrowed items found")
        else:
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
                status_loc = row.locator('td[data-caption="Status"] span')
                status_text = status_loc.first.inner_text() if status_loc.count() > 0 else ""
                renewed = int(status_text.replace("Renewed", "").replace(" times", "").replace(" time", "").strip()) if status_text else 0
                library_books[book_num] = {"title": title, "due_date": due_date_obj, "renewed": renewed}   
                book_num += 1

            # print(library_books)
            # print(f"{len(library_books)} books borrowed")

            renew_books = []
            must_return_books = []

            # go through each borrowed book
            for book_num, book in library_books.items():
                # check if due date is closer than x days and check the tickbox
                day_dfference = (book["due_date"] - today).days
                if day_dfference <= 3:
                    if book["renewed"] >= 2:
                        must_return_books.append(book)
                    else:
                        page.locator(f"#selCheck{book_num}").click()
                        renew_books.append(book)
            # renew all the books that got ticked in checkbox
            if renew_books:
                page.get_by_role("link", name="Renew selections").click()

            # print(must_return_books)
            # print(renew_books)

            due_lines = "".join(f"  - {b['title']} (Due: {b['due_date']})\n" for b in must_return_books)
            message = (
                f"User: {user[0]}\n"
                f"Library:Bolton\n"
                f"Currently Borrowing: {len(library_books)}\n"
                f"Must return:\n{due_lines}"
                f"{len(renew_books)} books got renewed\n"
            )   
            print(message)

        finally:
            # clicking user menu and logout
            # print("Log out")
            page.locator("#navbarLoginMenuLinkName").click()
            page.get_by_role("link", name="Logout").first.click()

def renew_borrowbox_books():
    BOLTON_BORROWBOX = "https://bolton.borrowbox.com/"

    page.goto(BOLTON_BORROWBOX)

    for user in user_list:
        # click login button
        login_button = page.get_by_role("link", name="Sign In")
        login_button.wait_for(state='visible')
        login_button.click()

        #insert credentials to login
        page.locator("input[name='barcode']").wait_for(state="visible")
        page.locator("input[name='barcode']").fill(user[0])
        page.locator("input[name='password']").fill(user[1])
        login_button = page.get_by_role("button", name="Sign In").first.click()

        # open currently borrowing books page
        page.get_by_role("link", name="My Loans").click()

        # find loaned products
        try:
            page.locator(".loaned_products_group").first.wait_for(state="visible")
        except PlaywrightTimeoutError:
            print(f"User: {user[0]}\n"
                  f"No borrowed items found")
        else:
            page.locator(".loaned_product_title")

            borrowbox_books = {}
            rows = page.locator("products").all()
            book_num = 1

# make sure that i can extract all the dates etc
            for row in rows:
                if row.locator("a[href*='/product/']").count() == 0:
                    continue
                title = row.locator("a[href*='/product/']").all_inner_texts()
                extracted_date = row.locator("div.action-status.right").inner_text()
                due_date_obj = datetime.strptime(extracted_date, "%A, %d %B %Y").date()
                renewed = int(status_text.replace("Renewed", "").replace(" times", "").replace(" time", "").strip()) if status_text else 0
                borrowbox_books[book_num] = {"title": title, "due_date": due_date_obj, "renewed": renewed}   
                book_num += 1



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

    # renew_library_books()
    renew_borrowbox_books()

    # here to not to close the screen
    input("Press Enter to close the browser...")