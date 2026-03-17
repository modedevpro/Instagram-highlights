from flask import Flask, request, jsonify
from curl_cffi import requests

app = Flask(__name__)

headers = {
    'user-agent': 'Instagram 113.0.0.39.122 Android (24/5.0; 515dpi; 1440x2416; huawei/google; Nexus 6P; angler; angler; en_US)',
}

@app.route("/")
def home():
    return {
        "message": "Use /highlights?user=username"
    }

@app.route("/highlights")
def get_highlights():

    username = request.args.get("user")
    if not username:
        return jsonify({"error": "ضيف ?user=username"}), 400

    params = {
        'username': username,
    }

    # 1️⃣ user info
    response = requests.get(
        'https://i.instagram.com/api/v1/users/web_profile_info/',
        params=params,
        headers=headers,
        impersonate="chrome110"
    )

    data = response.json()

    if "data" not in data:
        return jsonify({"error": "الحساب غير موجود أو محظور"}), 400

    user = data["data"]["user"]
    user_id = user["id"]

    result = {
        "user": {
            "username": user["username"],
            "id": user_id,
            "followers": user["edge_followed_by"]["count"],
            "following": user["edge_follow"]["count"]
        },
        "highlights": []
    }

    # 2️⃣ highlights
    highlights_res = requests.get(
        f'https://i.instagram.com/api/v1/highlights/{user_id}/highlights_tray/',
        headers=headers,
        impersonate="chrome110"
    )

    highlights_data = highlights_res.json()

    for h in highlights_data.get("tray", []):
        highlight_id = h["id"]
        title = h.get("title", "No Title")

        highlight_obj = {
            "id": highlight_id,
            "title": title,
            "stories": []
        }

        # 3️⃣ items
        items_res = requests.get(
            f'https://i.instagram.com/api/v1/feed/reels_media/?reel_ids=highlight:{highlight_id}',
            headers=headers,
            impersonate="chrome110"
        )

        items_data = items_res.json()

        items = items_data.get("reels", {}).get(f"highlight:{highlight_id}", {}).get("items", [])

        for item in items:
            story = {}

            if "video_versions" in item:
                story["type"] = "video"
                story["url"] = item["video_versions"][0]["url"]

            elif "image_versions2" in item:
                story["type"] = "image"
                story["url"] = item["image_versions2"]["candidates"][0]["url"]

            highlight_obj["stories"].append(story)

        result["highlights"].append(highlight_obj)

    return jsonify(result)


if __name__ == "__main__":
    app.run()
