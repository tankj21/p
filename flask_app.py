import requests
from bs4 import BeautifulSoup
import datetime
import os
import csv

# ========= 設定 =========
USERNAME = "search?f=tweets&q=pon2325_vrc"
NITTER_BASE = "https://nitter.net"  # 他のミラーでもOK
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Discord Webhook
CSV_FILE = "sent_tweets.csv"

# ========= ツイート履歴管理 =========
def load_sent_tweets():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return set(row[0] for row in csv.reader(f))

def save_sent_tweet(tweet_link):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([tweet_link])

# ========= ツイート取得 =========
def fetch_latest_tweet():
    try:
        url = f"{NITTER_BASE}/{USERNAME}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        tweet = soup.select_one(".timeline-item")
        if not tweet:
            return None

        content = tweet.select_one(".tweet-content").get_text(strip=True)
        time_tag = tweet.select_one(".tweet-date a")
        tweet_link = f"{NITTER_BASE}{time_tag['href']}" if time_tag else "リンクなし"

        image_tag = tweet.select_one(".attachment.image > a[href$='.jpg'], .attachment.image > a[href$='.png']")
        image_url = f"{NITTER_BASE}{image_tag['href']}" if image_tag else None

        return {
            "content": content,
            "link": tweet_link,
            "image": image_url
        }
    except Exception as e:
        print(f"⚠️ エラー発生: {e}")
        return None

# ========= Discord送信 =========
def send_to_discord(tweet):
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL が設定されていません")
        return

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
        print("✅ Discordに送信しました")
        save_sent_tweet(tweet["link"])
    else:
        print(f"❌ 送信失敗: {res.text}")

# ========= 実行 =========
if __name__ == "__main__":
    tweet = fetch_latest_tweet()
    if tweet:
        sent_links = load_sent_tweets()
        if tweet["link"] in sent_links:
            print("⏭️ このツイートはすでに送信済みです")
        else:
            send_to_discord(tweet)
    else:
        print("🔍 投稿が見つかりませんでした")
