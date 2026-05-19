import os
import xml.etree.ElementTree as ET
import requests

# URL for Firstpost RSS feed (World News section)
RSS_URL = "https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml"
HISTORY_FILE = "processed_urls.txt"


def load_processed_urls():
    """Load previously scraped URLs so we don't duplicate efforts."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f.readlines())
    return set()


def save_processed_url(url):
    """Append a newly scraped URL to our history tracking file."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{url}\n")


def fetch_news():
    print("Fetching news from Firstpost...")
    try:
        # Fetch data from Firstpost RSS feed
        response = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return

        # Parse the XML data from the RSS feed
        root = ET.fromstring(response.content)
        processed_urls = load_processed_urls()
        new_stories_found = False

        # Loop through all news items inside the RSS XML structure
        for item in root.findall(".//item"):
            title = item.find("title").text
            link = item.find("link").text
            pub_date = (
                item.find("pubDate").text if item.find("pubDate") is not None else ""
            )

            # Check if we have seen this article before
            if link not in processed_urls:
                new_stories_found = True
                print("\n--- NEW ARTICLE FOUND ---")
                print(f"Title: {title}")
                print(f"Link: {link}")
                print(f"Published: {pub_date}")

                # Save to history so it won't trigger next time
                save_processed_url(link)

        if not new_stories_found:
            print("No new articles since the last check.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    fetch_news()
