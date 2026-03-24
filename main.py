import os
import json
import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build

from scraper import search_partners

SHEET_ID = "1_wmTDmesy9PxZrKfey9BrCsIe5dMw_l_7uR5qTZaDSI"
TAB_NAME = "Partners"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Column order in the sheet
HEADERS = ["Company", "LinkedIn URL", "Country", "Specialization", "Date found"]


def _get_sheets_service():
    sa_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def _ensure_headers(service, existing_rows: list[list]) -> None:
    """Write header row if sheet is empty."""
    if not existing_rows:
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"{TAB_NAME}!A1",
            valueInputOption="RAW",
            body={"values": [HEADERS]},
        ).execute()


def _get_existing_urls(existing_rows: list[list]) -> set[str]:
    """Return set of LinkedIn URLs already present in the sheet (column B)."""
    urls = set()
    for row in existing_rows[1:]:  # skip header
        if len(row) >= 2 and row[1]:
            urls.add(row[1].strip().rstrip("/"))
    return urls


def _append_rows(service, rows: list[list]) -> None:
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{TAB_NAME}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


def main():
    api_key = os.environ["GOOGLE_CSE_API_KEY"]
    cse_id = os.environ["GOOGLE_CSE_ID"]

    print("=== meta-bi-partner-sourcing ===")
    print(f"Running scraper at {datetime.datetime.utcnow().isoformat()}Z\n")

    # 1. Scrape
    partners = search_partners(api_key, cse_id)

    if not partners:
        print("[INFO] No partners found — nothing to push.")
        return

    # 2. Connect to Sheets
    service = _get_sheets_service()

    # 3. Read existing data
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SHEET_ID, range=f"{TAB_NAME}!A:E")
        .execute()
    )
    existing_rows = result.get("values", [])

    _ensure_headers(service, existing_rows)
    existing_urls = _get_existing_urls(existing_rows)

    # 4. Filter out duplicates
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    new_rows = []
    for p in partners:
        url = p["linkedin_url"].rstrip("/")
        if url in existing_urls:
            print(f"  [SKIP] Already in sheet: {url}")
            continue
        new_rows.append(
            [
                p["company_name"],
                p["linkedin_url"],
                p["country"],
                p["specialization"],
                today,
            ]
        )
        existing_urls.add(url)  # prevent within-run duplicates

    # 5. Push new rows
    if new_rows:
        _append_rows(service, new_rows)
        print(f"\n[OK] Appended {len(new_rows)} new row(s) to '{TAB_NAME}'.")
    else:
        print("\n[INFO] All results already present in sheet — nothing appended.")


if __name__ == "__main__":
    main()
