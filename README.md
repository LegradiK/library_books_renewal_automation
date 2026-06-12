# Library & BorrowBox Renewal Automation

Automates checking and renewing borrowed items across **Bolton Library (Spydus)** and **BorrowBox**, for multiple users, and emails a daily HTML/plain-text report summarising the results.

## What it does

For each configured user account, the script:

1. **Bolton Library (Spydus)**
   - Logs into the Bolton Spydus library catalogue.
   - Opens the "currently borrowing" dashboard and scrapes every loaned item (title, due date, renewal count).
   - For each book due within **5 days**:
     - If it has been renewed fewer than 2 times, ticks it for renewal and submits "Renew selections".
     - If it has already been renewed 2+ times, leaves it and flags it as "must return soon".
   - Logs out.

2. **BorrowBox**
   - Logs into the BorrowBox web app.
   - Opens "My Loans" and scrapes every loaned item (title, days until expiry).
   - For each item due within **5 days**:
     - If a "Renew" button is available, clicks it and confirms the renewal.
     - Otherwise, flags it as "must return soon".
   - Logs out.

3. **Reporting**
   - Collects results from both libraries for all users into a single list.
   - Sends one email containing:
     - A **plain-text** summary (fallback).
     - An **HTML** report with a grid (rows = libraries, columns = users), showing for each user/library combination:
       - "No items currently borrowed" (if nothing is on loan), or
       - Number of items currently borrowed, how many were renewed, and a table of items that must be returned soon (with title and due date).

## What is automated

- Runs on a daily schedule via **GitHub Actions** (`.github/workflows/renew.yml`, currently `09:00 UTC`), or on demand via `workflow_dispatch`.
- Headless Chromium (via Playwright) handles all browser interaction — login, navigation, scraping, and clicking renewal buttons.
- Debug screenshots and the post-login page HTML are captured during the run and uploaded as workflow artifacts (`debug-screenshots`) to help diagnose login/UI issues, without failing the run if the screenshot itself times out.
- A single email report (multipart `text/plain` + `text/html`) is sent automatically via Gmail SMTP at the end of each run.

## Technical specifications

- **Language**: Python 3.11
- **Browser automation**: [Playwright](https://playwright.dev/python/) (sync API), Chromium, headless, 1920×1080 viewport
- **Email**: `smtplib` + `email.mime.multipart` over Gmail SMTP (`smtp.gmail.com:465`, SSL)
- **Config**: [`python-dotenv`](https://pypi.org/project/python-dotenv/), loaded from `data.env` (local) / GitHub Actions secrets (CI)

### Project structure

| File | Purpose |
|---|---|
| `main.py` | Entry point — loads config, runs both scrapers for all users, builds and sends the email report |
| `bolton_library.py` | Login, scrape, and renew logic for Bolton Library (Spydus) |
| `borrowbox.py` | Login, scrape, and renew logic for BorrowBox |
| `email_report.py` | Builds the HTML and plain-text email report from the collected results |
| `data.env` | Local environment variables (not committed — see `.gitignore`) |
| `.github/workflows/renew.yml` | GitHub Actions workflow that runs the automation daily |

### Local setup

```bash
python -m venv venv
source venv/bin/activate
pip install playwright python-dotenv
playwright install chromium
playwright install-deps chromium
```

Create a `data.env` file in the project root (see [Environment variables](#environment-variables) below), then run:

```bash
python main.py
```

## Environment variables

The script reads the following environment variables (from `data.env` locally, or from GitHub Actions secrets in CI):

| Variable | Description |
|---|---|
| `USER1_USERNAME` | Bolton Library / BorrowBox borrower ID for user 1 (same credentials are used for both services) |
| `USER1_PASSWORD` | Password / PIN for user 1 |
| `USER2_USERNAME` | Borrower ID for user 2 |
| `USER2_PASSWORD` | Password / PIN for user 2 |
| `EMAIL_SENDER` | Gmail address the report is sent **from** |
| `EMAIL_PASSWORD` | Gmail [App Password](https://support.google.com/accounts/answer/185833) for `EMAIL_SENDER` (not your normal Gmail password — requires 2FA enabled on the account) |
| `EMAIL_RECIPIENT` | Email address the report is sent **to** |

### Setting up secrets for GitHub Actions automation

In the GitHub repo, go to **Settings → Secrets and variables → Actions** and add each of the following as an individual **repository secret** (exact names, one secret per value):

- `USER1_USERNAME`
- `USER1_PASSWORD`
- `USER2_USERNAME`
- `USER2_PASSWORD`
- `EMAIL_SENDER`
- `EMAIL_PASSWORD`
- `EMAIL_RECIPIENT`

The workflow runs automatically every day at 09:00 UTC, or can be triggered manually from the **Actions** tab via "Run workflow" (`workflow_dispatch`).

## Notes / limitations

- Both user accounts must use the **same login flow** for each service (borrower ID + password/PIN).
- The renewal window (items due within 5 days) is hard-coded in `bolton_library.py` and `borrowbox.py`.
- If a Bolton Library item has already hit its renewal limit (2 renewals), it is **not** renewed and is instead listed under "must return soon" in the report.
- Debug screenshots (`*.png`) and `debug_after_login_click.html` are written to the working directory during each run and uploaded as CI artifacts; they are git-ignored locally.
