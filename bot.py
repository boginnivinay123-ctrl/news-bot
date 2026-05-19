import os
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from transformers import pipeline

# Configuration URLs
RSS_URL = "https://www.firstpost.com/commonfeeds/v1/mfp/rss/world.xml"
HISTORY_FILE = "processed_urls.txt"
SLACK_WEBHOOK_URL = "YOUR_SLACK_WEBHOOK_URL_HERE"
"https://hooks.slack.com/services/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"
print("Loading AI Summary Model...")
summarizer = pipeline(
    "summarization", model="facebook/bart-large-cnn", device=-1
)


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
        full_text = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 30])
        return full_text[:3000]
    except Exception as e:
        print(f"Failed to scrape article text: {e}")
        return ""


def generate_brief_summary(text):
    try:
        summary_result = summarizer(
            text, max_length=150, min_length=70, do_sample=False
        )
        return summary_result[0]["summary_text"]
    except Exception as e:
        print(f"AI Summarization failed: {e}")
        return "Could not generate brief summary automatically."


def send_to_slack(title, summary, link):
    payload = {
        "text": f"📰 *NEW ARTICLE DETECTED: {title}*\n\n"
        f"📝 *Brief Summary (AI Generated):*\n> {summary}\n\n"
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

                raw_article_text = scrape_full_article(link)

                if len(raw_article_text) > 200:
                    ai_summary = generate_brief_summary(raw_article_text)
                else:
                    ai_summary = "Full article content couldn't be loaded."

                send_to_slack(title, ai_summary, link)
                save_processed_url(link)
                break

        if not new_story_found:
            print("No new updates found.")

    except Exception as e:
        print(f"Error executing fetch process: {e}")


if __name__ == "__main__":
    fetch_news()
