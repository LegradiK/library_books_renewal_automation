import re
from datetime import timedelta
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def renew_borrowbox_books(page, user_list, today):
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
            page.locator(".products").first.wait_for(state="visible")
        except PlaywrightTimeoutError:
            print(f"User: {user[0]}\n"
                  f"No borrowed items found")
        else:
            rows = page.locator(".loaned-product-tile").all()

            borrowbox_books = {}
            book_num = 1
            renew_books = []
            return_books = []

            for row in rows:
                if row.locator("a[href*='/product/']").count() == 0:
                    continue
                title = row.locator("a[href*='/product/']").first.inner_text()
                extracted_expiry_date_text = row.locator("div.action-status.right").inner_text()
                due_in_days = int(re.search(r"\d+", extracted_expiry_date_text).group())
                expiry_date = today + timedelta(days=due_in_days)
                borrowbox_books[book_num] = {
                    "title": title,
                    "expiry_date": expiry_date,
                    "due_in_days": due_in_days,  
                    "row": row                 
                }
                book_num += 1

            for book_num, book in borrowbox_books.items():
                if book["due_in_days"] <= 10:
                    if book["row"].locator("button", has_text="Renew").count() > 0:
                        book["row"].locator("button", has_text="Renew").click()
                        renew_books.append(book)
                        if page.get_by_text("Confirm Renewal", exact=True).wait_for(state="visible"):
                            page.get_by_text("Confirm Renewal", exact=True).click()
                    else:
                        return_books.append(book)
                        # print(must_return_books)
                        # print(renew_books)

            due_lines = "".join(f"  - {b['title']} (Due: {b['expiry_date']})\n" for b in return_books)
            book_word = "book" if len(renew_books) == 1 else "books"
            message = (
                f"User: {user[0]}\n"
                f"Library:Borrow Box\n"
                f"Currently Borrowing: {len(borrowbox_books)}\n"
                f"Must return:\n{due_lines}"
                f"*{len(renew_books)} {book_word} got renewed.*\n"
            )
            print(message)

        finally:
            # clicking user menu and logout
            # print("Log out")
            page.get_by_role("button", name="Account status").click()
            page.get_by_text("Sign Out", exact=True).click()
