import os
import time
import requests

# Google Custom Search API endpoint
CSE_URL = "https://www.googleapis.com/customsearch/v1"

# Search queries targeting LinkedIn company pages for Microsoft Power BI / Data Analytics partners
QUERIES = [
    # France
    '"Microsoft Solutions Partner" "Power BI" site:linkedin.com/company France',
    '"Microsoft Gold Partner" "Data Analytics" site:linkedin.com/company France',
    '"Microsoft Partner" "Power Platform" site:linkedin.com/company France',
    # Germany
    '"Microsoft Solutions Partner" "Power BI" site:linkedin.com/company Deutschland',
    '"Microsoft Gold Partner" "Data Analytics" site:linkedin.com/company Deutschland',
    '"Microsoft Partner" "Power Platform" site:linkedin.com/company Germany',
    # Austria
    '"Microsoft Solutions Partner" "Power BI" site:linkedin.com/company Österreich',
    '"Microsoft Gold Partner" "Data Analytics" site:linkedin.com/company Austria',
    '"Microsoft Partner" "Power Platform" site:linkedin.com/company Wien',
    # Switzerland
    '"Microsoft Solutions Partner" "Power BI" site:linkedin.com/company Schweiz',
    '"Microsoft Gold Partner" "Data Analytics" site:linkedin.com/company Switzerland',
    '"Microsoft Partner" "Power Platform" site:linkedin.com/company Zurich',
]

# Maps keywords in query to country label
COUNTRY_HINTS = {
    "france": "France",
    "deutschland": "Germany",
    "germany": "Germany",
    "österreich": "Austria",
    "austria": "Austria",
    "wien": "Austria",
    "schweiz": "Switzerland",
    "switzerland": "Switzerland",
    "zurich": "Switzerland",
}

SPECIALIZATION_HINTS = {
    "power bi": "Power BI",
    "power platform": "Power Platform",
    "data analytics": "Data Analytics",
}


def _detect_country(query: str) -> str:
    q = query.lower()
    for keyword, country in COUNTRY_HINTS.items():
        if keyword in q:
            return country
    return "Unknown"


def _detect_specialization(query: str) -> str:
    q = query.lower()
    for keyword, spec in SPECIALIZATION_HINTS.items():
        if keyword in q:
            return spec
    return "Microsoft Partner"


def _extract_company_name(title: str, url: str) -> str:
    """Best-effort extraction of company name from LinkedIn result title."""
    # LinkedIn titles are typically "Company Name | LinkedIn" or "Company Name - LinkedIn"
    for sep in [" | LinkedIn", " - LinkedIn", " | Overview", " - Overview"]:
        if sep in title:
            return title.split(sep)[0].strip()
    # Fallback: use slug from URL
    # URL pattern: linkedin.com/company/slug
    parts = url.rstrip("/").split("/")
    if "company" in parts:
        idx = parts.index("company")
        if idx + 1 < len(parts):
            slug = parts[idx + 1].split("?")[0]
            return slug.replace("-", " ").title()
    return title.strip()


def _normalize_linkedin_url(url: str) -> str:
    """Return a canonical linkedin.com/company/slug URL (no trailing params)."""
    parts = url.split("?")[0].rstrip("/")
    return parts


def search_partners(api_key: str, cse_id: str) -> list[dict]:
    """
    Run all search queries and return a deduplicated list of partner dicts.
    Each dict has: company_name, linkedin_url, country, specialization.
    """
    seen_urls: set[str] = set()
    results: list[dict] = []

    for query in QUERIES:
        country = _detect_country(query)
        specialization = _detect_specialization(query)

        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": 10,  # max per request
        }

        try:
            resp = requests.get(CSE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            print(f"[WARN] Request failed for query '{query}': {exc}")
            time.sleep(2)
            continue

        items = data.get("items", [])
        if not items:
            print(f"[INFO] No results for: {query}")
        for item in items:
            url = _normalize_linkedin_url(item.get("link", ""))
            if not url or "linkedin.com/company" not in url:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)

            company_name = _extract_company_name(item.get("title", ""), url)
            results.append(
                {
                    "company_name": company_name,
                    "linkedin_url": url,
                    "country": country,
                    "specialization": specialization,
                }
            )
            print(f"  [+] {company_name} | {country} | {url}")

        # Respect Google CSE rate limits (100 queries/day free tier)
        time.sleep(1)

    print(f"\n[INFO] Total unique partners found: {len(results)}")
    return results


if __name__ == "__main__":
    api_key = os.environ["GOOGLE_CSE_API_KEY"]
    cse_id = os.environ["GOOGLE_CSE_ID"]
    partners = search_partners(api_key, cse_id)
    for p in partners:
        print(p)
