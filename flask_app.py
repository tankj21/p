from flask import Flask
import requests
import datetime
import os

app = Flask(__name__)

webhook_url = os.environ.get("WEBHOOK_URL")
json_feed_url = os.environ.get("JSON_FEED_URL")
id_file = "last_post_id.txt"

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

        # 投稿がなければ「新着なし」だけ送る
        if not new_items:
            message = "🟡 新しい投稿はありませんでした。"
        else:
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
            message = f"✅ {len(new_items)} 件の新着投稿を送信しました！"

        # 定期実行ログもDiscordに送る
        requests.post(webhook_url, json={
            "username": "ぽんちゃん見守り隊",
            "content": f"⏰ 定期実行が正常に完了しました！ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        })

        # 最後にID保存
        if new_items:
            with open(id_file, "w") as f:
                f.write(new_items[-1]["id"])

        return message

    except Exception as e:
        # エラーもDiscordに送信すると便利！
        requests.post(webhook_url, json={
            "username": "ぽんちゃん見守り隊",
            "content": f"⚠️ エラー発生: {str(e)}"
        })
        return f"❌ エラー: {str(e)}"
