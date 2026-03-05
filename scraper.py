"""
Trade Me Property pricing scraper — uses Playwright.

The Trade Me help centre (Zendesk) returns 403 to plain requests.
Playwright with a real browser context loads the page correctly.

Source: https://help.trademe.co.nz/hc/en-us/articles/360032007872-Property-fees

Two listing fee tiers based on rateable value (RV):
  - Standard: NZD $99  for properties with rateable value ≤ $450,000
  - Premium:  NZD $159 for properties with rateable value > $450,000

fee_period = per_listing
"""

import re
from datetime import date

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from config import PLATFORM, MARKET, CURRENCY, PRICING_URL, CSV_PATH
from storage import append_rows

PLAYWRIGHT_TIMEOUT = 30_000

KNOWN_TIERS = [
    {
        "tier_name": "Standard (≤$450k RV)",
        "fee_amount": 99,
        "prop_value_min": "",
        "prop_value_max": 450000,
        "hybrid_note": "Rateable value threshold",
    },
    {
        "tier_name": "Premium (>$450k RV)",
        "fee_amount": 159,
        "prop_value_min": 450001,
        "prop_value_max": "",
        "hybrid_note": "Rateable value threshold",
    },
]


def fetch_page_text(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-NZ",
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)
        except PlaywrightTimeout:
            page.goto(url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)

        # Wait for article content to appear
        try:
            page.wait_for_selector("article, .article-body, main", timeout=10_000)
        except PlaywrightTimeout:
            pass

        text = page.inner_text("body")
        browser.close()
    return text


def parse_fees(text: str) -> list[dict]:
    today = date.today().isoformat()

    found_99  = bool(re.search(r"\$\s*99\b|99\s*(?:NZD|\$)", text))
    found_159 = bool(re.search(r"\$\s*159\b|159\s*(?:NZD|\$)", text))
    verified  = found_99 and found_159

    if verified:
        print("Confirmed $99 and $159 from live page.")
    else:
        print(
            f"WARNING: could not confirm prices (found_99={found_99}, "
            f"found_159={found_159}). Using last-known values."
        )

    rows = []
    for tier in KNOWN_TIERS:
        note = tier["hybrid_note"]
        if not verified:
            note += " [UNVERIFIED — page content changed]"
        rows.append({
            "scrape_date":    today,
            "platform":       PLATFORM,
            "market":         MARKET,
            "currency":       CURRENCY,
            "tier_name":      tier["tier_name"],
            "fee_amount":     tier["fee_amount"],
            "fee_period":     "per_listing",
            "prop_value_min": tier["prop_value_min"],
            "prop_value_max": tier["prop_value_max"],
            "location_note":  "",
            "hybrid_note":    note,
        })
    return rows


def main():
    print(f"Fetching Trade Me pricing via Playwright: {PRICING_URL}")
    try:
        text = fetch_page_text(PRICING_URL)
        rows = parse_fees(text)
    except Exception as e:
        print(f"WARNING: Playwright fetch failed ({e}). Using last-known values.")
        today = date.today().isoformat()
        rows = [
            {
                "scrape_date":    today,
                "platform":       PLATFORM,
                "market":         MARKET,
                "currency":       CURRENCY,
                "tier_name":      tier["tier_name"],
                "fee_amount":     tier["fee_amount"],
                "fee_period":     "per_listing",
                "prop_value_min": tier["prop_value_min"],
                "prop_value_max": tier["prop_value_max"],
                "location_note":  "",
                "hybrid_note":    tier["hybrid_note"] + " [UNVERIFIED — fetch failed]",
            }
            for tier in KNOWN_TIERS
        ]
    append_rows(CSV_PATH, rows)


if __name__ == "__main__":
    main()
