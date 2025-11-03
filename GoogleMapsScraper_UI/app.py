# ...existing code...
import streamlit as st
import os
import tempfile
import pandas as pd
from google_maps_scraper import scrape_google_maps

OUTPUT_FOLDER = "output"

st.title("📍 Google Maps Business Scraper")

# Input fields
store_type = st.text_input("Type of store/business", "phone store")
places_input = st.text_area("Places to search (comma-separated)", "Bab El Oued, Kouba, Bab Ezzouar, Sorical")
headless_mode = st.checkbox("Run headless browser", value=True)

if st.button("Start Scraping"):
    if not store_type.strip() or not places_input.strip():
        st.error("⚠️ Please fill in all fields before running.")
    else:
        places = [p.strip() for p in places_input.split(",") if p.strip()]
        for location in places:
            query = f"{store_type} {location}"
            st.write(f"🔍 Scraping: {query}")

            # Use a temporary file so we don't keep CSVs on disk
            tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
            tmp_path = tmp.name
            tmp.close()  # allow the scraper to write to this file on Windows

            # Call existing scraper (which writes CSV to the provided path)
            scrape_google_maps(query, location, tmp_path, headless=headless_mode)

            # Read and display the results, then delete the temp file
            try:
                df = pd.read_csv(tmp_path)
                if df.empty:
                    st.info(f"No results for: {query}")
                else:
                    st.subheader(f"Results — {query}")
                    st.dataframe(df)
            except Exception as e:
                st.error(f"Failed to read results for {query}: {e}")
            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        st.success("✅ Scraping completed! Results shown above.")
# ...existing code...