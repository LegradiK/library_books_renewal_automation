import re
from datetime import timedelta
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


BOLTON_BORROWBOX_LOGIN = "https://bolton.borrowbox.com/login"


def _accept_cookies(page):
    try:
        page.locator("button.button-white.size-large", has_text="Accept").click(timeout=5000)
    except PlaywrightTimeoutError:
        pass


def _sign_in(page, user):
    page.goto(BOLTON_BORROWBOX_LOGIN, wait_until="domcontentloaded", timeout=60000)
    _accept_cookies(page)

    barcode = page.locator("input[name='barcode']:visible")
    try:
        barcode.wait_for(state="visible", timeout=15000)
    except PlaywrightTimeoutError:
        # save evidence of what the page actually showed
        safe_id = re.sub(r"\W", "", str(user[0]))[-4:] or "user"
        shot = f"borrowbox_login_fail_{safe_id}.png"
        page.screenshot(path=shot, full_page=True)
        print(f"BorrowBox login form not found. URL: {page.url} | screenshot: {shot}")
        raise

    barcode.fill(user[0])
    page.locator("input[name='password']:visible").fill(user[1])
    page.locator("button.signin-button[type='submit']:visible").click()


def renew_borrowbox_books(page, user_list, today):
    results = []
    browser = page.context.browser

    for user in user_list:
        # a brand-new context per user = no cookies, localStorage or sessionStorage
        # carried over from the previous user, so the login form always appears
        context = browser.new_context()
        page = context.new_page()

        try:
            _sign_in(page, user)

            # open currently borrowing books page
            my_loans = page.get_by_role("link", name="My Loans")
            my_loans.wait_for(state="visible", timeout=15000)
            my_loans.click()

            # find loaned products
            try:
                page.locator(".products").first.wait_for(state="visible", timeout=10000)
            except PlaywrightTimeoutError:
                message = (f"User: {user[0]}\n"
                           f"Library: Borrow Box\n"
                           f"No borrowed items found\n")
                print(message)
                results.append({
                    "user": user[0],
                    "library": "BorrowBox",
                    "no_items": True,
                })
                continue

            rows = page.locator(".loaned-product-tile").all()

            borrowbox_books = {}
            book_num = 1
            renew_books = []
            return_books = []

            for row in rows:
                if row.locator("a[href*='/product/']").count() == 0:
                    continue
                title = row.locator("a[href*='/product/']").first.inner_text()

                status = row.locator("div.action-status")
                if status.count() == 0:
                    print(f"Skipping '{title}' - no due status found. Tile text: {row.inner_text()!r}")
                    continue
                extracted_expiry_date_text = status.first.inner_text()

                match = re.search(r"\d+", extracted_expiry_date_text)
                if match:
                    due_in_days = int(match.group())
                elif "today" in extracted_expiry_date_text.lower():
                    due_in_days = 0
                else:
                    print(f"Skipping '{title}' - unrecognised status: {extracted_expiry_date_text!r}")
                    continue

                borrowbox_books[book_num] = {
                    "title": title,
                    "expiry_date": today + timedelta(days=due_in_days),
                    "due_in_days": due_in_days,
                    "row": row,
                }
                book_num += 1

            for book in borrowbox_books.values():
                if book["due_in_days"] > 5:
                    continue

                renew_btn = book["row"].locator("button", has_text="Renew")
                if renew_btn.count() == 0:
                    return_books.append(book)
                    continue

                renew_btn.first.click()
                confirm_renewal = page.locator("button.button-warning", has_text="Confirm Renewal")
                confirm_renewal.wait_for(state="visible", timeout=10000)
                confirm_renewal.click()

                ok_btn = page.locator("button.button-neutral", has_text="OK")
                close_btn = page.locator("button.button-neutral", has_text="Close")
                try:
                    ok_btn.wait_for(state="visible", timeout=3000)
                except PlaywrightTimeoutError:
                    pass
                if ok_btn.is_visible():
                    ok_btn.click()
                else:
                    close_btn.wait_for(state="visible", timeout=10000)
                    close_btn.click()
                renew_books.append(book)

            due_lines = "".join(f"  - {b['title']} (Due: {b['expiry_date']})\n" for b in return_books) if return_books else "None"
            book_word = "book" if len(renew_books) == 1 else "books"
            message = (
                f"User: {user[0]}\n"
                f"Library: Borrow Box\n"
                f"Currently Borrowing: {len(borrowbox_books)}\n"
                f"Must return: {due_lines}\n"
                f"*{len(renew_books)} {book_word} got renewed.*\n"
            )
            print(message)

            results.append({
                "user": user[0],
                "library": "BorrowBox",
                "no_items": False,
                "currently_borrowing": len(borrowbox_books),
                "renewed_count": len(renew_books),
                "must_return": [{"title": b["title"], "due_date": b["expiry_date"]} for b in return_books],
            })

        finally:
            # discarding the context signs the user out locally - no UI sign-out needed
            context.close()

    return results