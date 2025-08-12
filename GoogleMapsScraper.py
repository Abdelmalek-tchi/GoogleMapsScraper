"""
Google Maps Business Scraper
----------------------------
Scrapes business information from Google Maps for a given search term and list of locations.

Features:
- simple to use and modify
- Uses Playwright to interact with Google Maps and not been detected by any anti-scraping measures
- Supports multiple locations
- Navigates to Google Maps search page
- Scrolls until all results are loaded
- Extracts business name, rating, phone number, and location, more information will be added in the future
- Saves results per location as CSV
- Merges all CSVs into a single Excel file

Author: Aissaoui Abdelmalek
"""

'''
### run this terminal :
pip install playwright
playwright install
pip install openpyxl


another UI version will available soon


'''

from playwright.sync_api import sync_playwright
import csv
import time
import pandas as pd
import glob
import os
from places import custom  # list of places to search

# ===========================
# CONFIGURATION
# ===========================
custom = custom              # list of places to search.(eg: custom = ["Bab El Oued", "Kouba", "Bab Ezzouar","Sorical"])
STORE_TYPE = "phone store"   # change to your desired business type
OUTPUT_FOLDER = "output"     # folder to store CSVs
HEADLESS_MODE = False        # True = browser hidden, False = visible
SCROLL_DELAY = 0.5           # seconds between scrolls


def scrape_google_maps(search_query, location, output_file, headless=HEADLESS_MODE):
    """
    Scrapes Google Maps search results for a given query and location.

    Args:
        search_query (str): The search query (e.g., "phone store Paris")
        location (str): The location being searched (used in output)
        output_file (str): Path to save the CSV file
        headless (bool): Whether to run browser in headless mode
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        page.goto(url)
        print(f"\n🔍 Searching for: {search_query}")

        scrollable_div = page.locator("div[role='feed']")

        # Scroll until end of list or stable count
        prev_count = -1
        stable_rounds = 0
        MAX_STABLE = 5
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
            if stable_rounds >= MAX_STABLE:
                print("ℹ️ No new results, stopping scroll.")
                break

        # Extract business data
        store_cards = page.query_selector_all("div.Nv2PK.THOPZb.CpccDe")
        print(f"📦 Found {len(store_cards)} stores.")

        stores = []
        for card in store_cards:
            try:
                name = card.query_selector("div.qBF1Pd.fontHeadlineSmall").inner_text().strip() if card.query_selector("div.qBF1Pd.fontHeadlineSmall") else ""
                rating = card.query_selector("span.MW4etd").inner_text().strip() if card.query_selector("span.MW4etd") else ""
                phone = card.query_selector("span.UsdlK").inner_text().strip() if card.query_selector("span.UsdlK") else ""

                stores.append({
                    "name": name,
                    "place_id": location,
                    "rating": rating,
                    "phone": phone
                })
            except Exception as e:
                print(f"⚠️ Error parsing store card: {e}")

        # Save CSV
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "place_id", "rating", "phone"])
            writer.writeheader()
            writer.writerows(stores)

        print(f"💾 Saved {len(stores)} stores to '{output_file}'")
        browser.close()


def merge_csv_to_excel(output_folder, excel_filename="all_stores.xlsx"):
    """
    Merges all CSV files in a folder into a single Excel file.

    Args:
        output_folder (str): Folder containing CSV files
        excel_filename (str): Name of the output Excel file
    """
    csv_files = glob.glob(os.path.join(output_folder, "*.csv"))
    if not csv_files:
        print("⚠️ No CSV files found to merge.")
        return

    dfs = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(dfs, ignore_index=True)
    excel_path = os.path.join(output_folder, excel_filename)
    df.to_excel(excel_path, index=False)
    print(f"📊 Merged {len(csv_files)} CSV files into '{excel_path}'")


if __name__ == "__main__":
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for location in custom:
        query = f"{STORE_TYPE} {location}"
        output_path = os.path.join(OUTPUT_FOLDER, f"{STORE_TYPE}_{location}.csv")
        scrape_google_maps(query, location, output_path)

    merge_csv_to_excel(OUTPUT_FOLDER)



