# google_maps_scraper.py
import sys
import asyncio

# ✅ Fix for Playwright NotImplementedError on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright
import csv
import time
import pandas as pd
import glob
import os

SCROLL_DELAY = 0.5  # seconds between scrolls


def scrape_google_maps(search_query, location, output_file, headless=True):
    """
    Scrapes Google Maps search results for a given query and location.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        page.goto(url)
        print(f"🔍 Searching for: {search_query}")

        scrollable_div = page.locator("div[role='feed']")

        # Scroll until results stop loading
        prev_count = -1
        stable_rounds = 0
        MAX_STABLE = 50
        while True:
            scrollable_div.evaluate("el => el.scrollBy(0, el.scrollHeight)")
            time.sleep(SCROLL_DELAY)

            store_count = page.locator("div.Nv2PK.THOPZb.CpccDe").count()
            if store_count == prev_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
                prev_count = store_count

            if page.locator("text=Vous êtes arrivé à la fin de la liste.").count() > 0:
                print("✅ End of list reached.")
                break
                '''
            if stable_rounds >= MAX_STABLE:
                print("ℹ️ No new results, stopping scroll.")
                break
                '''
        # Extract business data
        store_cards = page.query_selector_all("div.Nv2PK.THOPZb.CpccDe")
        print(f"📦 Found {len(store_cards)} stores.")

        stores = []
        for card in store_cards:
            try:
                name = card.query_selector("div.qBF1Pd.fontHeadlineSmall").inner_text().strip() if card.query_selector("div.qBF1Pd.fontHeadlineSmall") else ""
                phone = card.query_selector("span.UsdlK").inner_text().strip() if card.query_selector("span.UsdlK") else ""

                stores.append({
                    "name": name,
                    "place_id": location,
                    "phone": phone
                })
            except Exception as e:
                print(f"⚠️ Error parsing store card: {e}")

        # Save CSV
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "place_id", "phone"])
            writer.writeheader()
            writer.writerows(stores)

        print(f"💾 Saved {len(stores)} stores to '{output_file}'")
        browser.close()

