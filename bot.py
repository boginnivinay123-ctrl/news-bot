import os
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import re

# Configuration URLs
RSS_URL = "https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml"
HISTORY_FILE = "processed_urls.txt"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"


def load_processed_urls():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f.readlines())
    return set()


def save_processed_url(url):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{url}\n")


def scrape_full_article(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text_lines = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40]
        return text_lines
    except Exception as e:
        print(f"Failed to scrape article text: {e}")
        return []


def generate_brief_summary(paragraphs):
    """Creates a perfect 5-6 sentence summary from the article paragraphs."""
    try:
        # Filter out random tracking lines, headers, or social share text
        clean_paragraphs = [p for p in paragraphs if not p.startswith(("Also Read", "Follow us", "Read more"))]
        
        # Take the first 5-6 valid paragraphs of the article body
        summary_sentences = clean_paragraphs[:6]
        
        if not summary_sentences:
            return "Click the link below to read the article contents."
            
        return "\n\n".join(summary_sentences)
    except Exception as e:
        print(f"Summarization failed: {e}")
        return "Could not generate brief summary automatically."


def send_to_slack(title, summary, link):
    payload = {
        "text": f"📰 *NEW ARTICLE DETECTED: {title}*\n\n"
        f"📝 *Brief Summary:*\n> {summary}\n\n"
        f"👉 *Read Full Article:* {link}"
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("Successfully pushed to Slack!")
        else:
            print(f"Slack error: {response.status_code}")
    except Exception as e:
        print(f"Network error to Slack: {e}")


def fetch_news():
    print("Checking Firstpost feed...")
    try:
        response = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"Failed to fetch RSS. Status: {response.status_code}")
            return

        root = ET.fromstring(response.content)
        processed_urls = load_processed_urls()
        new_story_found = False

        for item in root.findall(".//item"):
            title = item.find("title").text
            link = item.find("link").text

            if link not in processed_urls:
                new_story_found = True
                print(f"\nProcessing New Story: {title}")

                # Gather article paragraphs
                article_paragraphs = scrape_full_article(link)

                if len(article_paragraphs) > 2:
                    ai_summary = generate_brief_summary(article_paragraphs)
                else:
                    ai_summary = "Full article text context couldn't be loaded directly."

                send_to_slack(title, ai_summary, link)
                save_processed_url(link)
                break

        if not new_story_found:
            print("No new updates found.")

    except Exception as e:
        print(f"Error executing fetch process: {e}")


if __name__ == "__main__":
    fetch_news()
