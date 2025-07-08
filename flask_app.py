import requests
from bs4 import BeautifulSoup
import datetime
import os
import csv

from flask import Flask, jsonify

app = Flask(__name__)

USERNAME = "search?f=tweets&q=pon2325_vrc"  # ←リプライ含めた全投稿
NITTER_BASE = "https://nitter.net"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CSV_FILE = "sent_tweets.csv"

def load_sent_tweets():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return set(row[0] for row in csv.reader(f))

def save_sent_tweet(tweet_link):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([tweet_link])

def fetch_latest_tweets(limit=10):
    try:
        url = f"{NITTER_BASE}/{USERNAME}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        tweet_items = soup.select(".timeline-item")[:limit]

        tweets = []
        for tweet in tweet_items:
            content = tweet.select_one(".tweet-content")
            time_tag = tweet.select_one(".tweet-date a")
            image_tag = tweet.select_one(".attachment.image > a[href$='.jpg'], .attachment.image > a[href$='.png']")

            if not content or not time_tag:
                continue

            tweets.append({
                "content": content.get_text(strip=True),
                "link": f"{NITTER_BASE}{time_tag['href']}",
                "image": f"{NITTER_BASE}{image_tag['href']}" if image_tag else None
            })

        return tweets
    except Exception as e:
        print(f"⚠️ エラー発生: {e}")
        return []

def send_to_discord(tweet):
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL が設定されていません")
        return False

    embed = {
        "title": "📢 新しい投稿！",
        "description": tweet["content"],
        "url": tweet["link"],
        "color": 0x1DA1F2,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    if tweet["image"]:
        embed["image"] = {"url": tweet["image"]}

    payload = {
        "username": "X通知Bot",
        "embeds": [embed]
    }

    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code == 204:
        print(f"✅ 送信済み: {tweet['link']}")
        save_sent_tweet(tweet["link"])
        return True
    else:
        print(f"❌ 送信失敗: {res.status_code} - {res.text}")
        return False

# ========= Flaskルート =========
@app.route("/")
def notify_tweets():
    tweets = fetch_latest_tweets(limit=10)
    sent_links = load_sent_tweets()

    new_tweets = [tweet for tweet in tweets if tweet["link"] not in sent_links]

    if not new_tweets:
        return jsonify({"status": "no new tweets", "count": 0})

    sent_count = 0
    for tweet in reversed(new_tweets):
        if send_to_discord(tweet):
            sent_count += 1

    return jsonify({"status": "sent", "count": sent_count})
