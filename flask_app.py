from flask import Flask
import requests
import datetime
import os

app = Flask(__name__)

webhook_url = os.environ.get("WEBHOOK_URL")
json_feed_url = os.environ.get("JSON_FEED_URL")
id_file = "last_post_id.txt"  # Renderはローカルファイル使える

@app.route("/notify")
def notify():
    try:
        last_id = None
        if os.path.exists(id_file):
            with open(id_file, "r") as f:
                last_id = f.read().strip()

        feed = requests.get(json_feed_url).json()
        items = feed["items"]

        new_items = []
        for item in items:
            if item["id"] == last_id:
                break
            new_items.append(item)
        new_items.reverse()

        if not new_items:
            return "🟡 新しい投稿はありません"

        for item in new_items:
            published = datetime.datetime.fromisoformat(item["date_published"].replace("Z", "+00:00"))
            jst = published.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
            embed = {
                "title": item["title"],
                "description": f"{item['content_text']}\n🕒 {jst.strftime('%Y-%m-%d %H:%M')}\n🔗 [元ポスト]({item['url']})",
                "color": 0x1DA1F2,
            }
            if "image" in item:
                embed["image"] = {"url": item["image"]}

            payload = {
                "username": "X通知Bot",
                "embeds": [embed]
            }
            requests.post(webhook_url, json=payload)

        with open(id_file, "w") as f:
            f.write(new_items[-1]["id"])

        return f"✅ {len(new_items)} 件送信しました！"

    except Exception as e:
        return f"❌ エラー: {str(e)}"
