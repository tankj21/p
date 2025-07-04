import requests
from bs4 import BeautifulSoup
import datetime
import os

# ========= 設定 =========
USERNAME = "pon2325_vrc"
NITTER_BASE = "https://nitter.net"  # 他のミラーでもOK
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Discord Webhook

def fetch_latest_tweet():
    url = f"{NITTER_BASE}/{USERNAME}"
    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    tweet = soup.select_one(".timeline-item")  # 最新の1件
    if not tweet:
        return None

    content = tweet.select_one(".tweet-content").get_text(strip=True)

    time_tag = tweet.select_one(".tweet-date a")
    tweet_link = f"{NITTER_BASE}{time_tag['href']}" if time_tag else "リンクなし"

<<<<<<< HEAD
    image_tag = tweet.select_one(".attachment.image > a[href$='.jpg'], .attachment.image > a[href$='.png']")
    image_url = f"{NITTER_BASE}{image_tag['href']}" if image_tag else None

    return {
        "content": content,
        "link": tweet_link,
        "image": image_url
    }
=======
                payload = {
                    "username": "ぽんちゃん見守り隊",
                    "embeds": [embed]
                }
                requests.post(webhook_url, json=payload)
            message = f"✅ {len(new_items)} 件の新着投稿を送信しました！"

        # 定期実行ログもDiscordに送る
        
>>>>>>> 21d0086251737669871e6cba26af087466dda355

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
    print("✅ Discordに送信しました" if res.status_code == 204 else f"❌ 失敗: {res.text}")

# ========= 実行 =========
if __name__ == "__main__":
    tweet = fetch_latest_tweet()
    if tweet:
        send_to_discord(tweet)
    else:
        print("🔍 投稿が見つかりませんでした")
