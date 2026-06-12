import re
from datetime import datetime
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect


def renew_library_books(page, user_list, today):
    BOLTON_SPYDUS = "https://bolton.spydus.co.uk/cgi-bin/spydus.exe/MSGTRN/OPAC/HOME"

    page.goto(BOLTON_SPYDUS, wait_until="domcontentloaded", timeout=60000)

    try:
        accept_cookies = page.locator('#offcanvasCookie_all')
        accept_cookies.wait_for(state="visible", timeout=8000)
        accept_cookies.click()
        # wait for it to fully disappear before doing anything else
        accept_cookies.wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        pass

    page.screenshot(path="debug_bolton_1_after_cookies.png")

    page.wait_for_timeout(3000)

    results = []

    for user in user_list:

        # clicking login button to show login area
        login_button = page.locator('button[id="navbarLoginMenuLink1"]')
        login_button.wait_for(state='visible')
        login_button.click()
        page.screenshot(path="debug_bolton_after_login_click.png")

        with open("debug_after_login_click.html", "w", encoding="utf-8") as f:
            f.write(page.content())

        # inserting credentials (use :visible since the page has a hidden duplicate login form for mobile)
        user_name_area = page.locator("[placeholder='Borrower Id']:visible")

        # the login dropdown sometimes fails to open on the first click right after
        # the previous user's logout reloads the page (Bootstrap JS not yet attached) -
        # retry the click until the form actually becomes visible
        for attempt in range(3):
            try:
                user_name_area.wait_for(state="visible", timeout=5000)
                break
            except PlaywrightTimeoutError:
                login_button.click()
        else:
            user_name_area.wait_for(state="visible")

        user_name_area.click()
        user_name_area.fill(user[0])
        page.screenshot(path="user_name.png")
        password_area = page.locator("[placeholder='Password']:visible")
        password_area.click()
        password_area.fill(user[1])
        page.screenshot(path="password.png")
        page.locator(".btn-submit:visible").click()

        # find currently borrowed items
        try:
            page.locator(".brw-dashboard-item").first.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            message = (f"User: {user[0]}\n"
                       f"Library: Bolton\n"
                       f"No borrowed items found\n")
            print(message)
            results.append({
                "user": user[0],
                "library": "Bolton Library",
                "no_items": True,
            })
        else:
            page.locator(".brw-dashboard-item").first.click()

            # clicking the dashboard tile triggers an async load of the loans
            # table - wait for the "Showing X - Y of Z" summary and for that
            # many titles to render before scraping, otherwise we can catch
            # the table mid-load and miss rows
            try:
                showing_text = page.get_by_text(re.compile(r"Showing \d+\s*-\s*\d+ of \d+"))
                showing_text.wait_for(state="visible", timeout=10000)
                total_books = int(re.search(r"of (\d+)", showing_text.inner_text()).group(1))
                expect(page.locator("h3.card-title")).to_have_count(total_books, timeout=10000)
            except PlaywrightTimeoutError:
                pass

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
                if day_dfference <= 5:
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

            results.append({
                "user": user[0],
                "library": "Bolton Library",
                "no_items": False,
                "currently_borrowing": len(library_books),
                "renewed_count": len(renew_books),
                "must_return": [{"title": b["title"], "due_date": b["due_date"]} for b in must_return_books],
            })

        finally:
            try:
                page.get_by_role("link", name="Show account menu").wait_for(state="visible", timeout=10000)
                page.get_by_role("link", name="Show account menu").click()
                page.get_by_role("link", name="Logout").first.click()
            except PlaywrightTimeoutError:
                print(f"Could not log out user {user[0]} — login may have failed")

    return results
