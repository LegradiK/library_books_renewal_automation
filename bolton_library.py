from datetime import datetime
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def renew_library_books(page, user_list, today):
    BOLTON_SPYDUS = "https://bolton.spydus.co.uk/cgi-bin/spydus.exe/MSGTRN/OPAC/HOME"

    page.goto(BOLTON_SPYDUS, wait_until="domcontentloaded", timeout=60000)

    try:
        page.locator('button.btn-close[data-bs-dismiss="offcanvas"]').click(timeout=8000)
    except PlaywrightTimeoutError:
        pass

    page.wait_for_timeout(3000)

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
            page.locator(".brw-dashboard-item").first.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            message = (f"User: {user[0]}\n"
                       f"No borrowed items found\n")
            print(message)
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
                if day_dfference <= 20:
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

            due_lines = "".join(f"  - {b['title']} (Due: {b['due_date']})\n" for b in must_return_books) if must_return_books else "None"
            book_word = "book" if len(renew_books) == 1 else "books"
            message = (
                f"User: {user[0]}\n"
                f"Library:Bolton\n"
                f"Currently Borrowing: {len(library_books)}\n"
                f"Must return:{due_lines}\n"
                f"*{len(renew_books)} {book_word} got renewed.*\n"
            )
            print(message)

        finally:
            try:
                page.locator("#navbarLoginMenuLinkName").wait_for(state="visible", timeout=10000)
                page.locator("#navbarLoginMenuLinkName").click()
                page.get_by_role("link", name="Logout").first.click()
            except PlaywrightTimeoutError:
                print(f"Could not log out user {user[0]} — login may have failed")



