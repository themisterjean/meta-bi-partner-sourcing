# meta-bi-partner-sourcing

Scrapes Microsoft Partner Directory (via Google Custom Search) to discover Power BI / Data Analytics partners in France, Germany, Austria, and Switzerland — and writes results to a Google Sheet.

---

## What it does

- Searches LinkedIn company pages using Google CSE with queries like:
  - `"Microsoft Solutions Partner" "Power BI" site:linkedin.com/company France`
  - `"Microsoft Gold Partner" "Data Analytics" site:linkedin.com/company Deutschland`
  - (12 queries total across FR / DE / AT / CH)
- Deduplicates results by LinkedIn URL
- Appends new rows only (skips companies already in the sheet)

**Output columns:** Company | LinkedIn URL | Country | Specialization | Date found

**Target sheet:** [Partners Sheet](https://docs.google.com/spreadsheets/d/1_wmTDmesy9PxZrKfey9BrCsIe5dMw_l_7uR5qTZaDSI)
**Tab name:** `Partners`

---

## Repository structure

```
meta-bi-partner-sourcing/
├── scraper.py                    # Google CSE search + result parsing
├── main.py                       # Orchestrator: runs scraper, pushes to Sheets
├── requirements.txt
├── .github/
│   └── workflows/
│       └── weekly.yml            # GitHub Actions: runs every Monday 07:00 UTC
└── README.md
```

---

## Secrets required

Add these in **GitHub → Settings → Secrets and variables → Actions**:

| Secret name                   | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| `GOOGLE_CSE_API_KEY`          | Google Cloud API key with Custom Search JSON API enabled                    |
| `GOOGLE_CSE_ID`               | Your Programmable Search Engine ID (cx)                                     |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full JSON key of the `meta-bi-bot` service account (paste entire JSON blob) |

---

## Google Sheet permissions

The service account `meta-bi-bot@<project>.iam.gserviceaccount.com` must have **Editor** access on the target Google Sheet.

---

## Local setup

```bash
# 1. Clone the repo
git clone https://github.com/<your-org>/meta-bi-partner-sourcing.git
cd meta-bi-partner-sourcing

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export GOOGLE_CSE_API_KEY="your_api_key"
export GOOGLE_CSE_ID="your_cse_id"
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

# 4. Run
python main.py
```

---

## Run manually via GitHub Actions

1. Go to **Actions** tab in this repository
2. Select **Weekly Partner Scrape**
3. Click **Run workflow**

---

## Google CSE setup notes

- Create a Programmable Search Engine at https://programmablesearchengine.google.com
- Enable **Search the entire web** (not just specific sites — the queries already include `site:` operators)
- Enable the **Custom Search JSON API** in Google Cloud Console
- Free tier: 100 queries/day. This workflow uses 12 queries per run.
