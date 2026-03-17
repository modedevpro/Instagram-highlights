from flask import Flask, request, jsonify
from curl_cffi import requests

app = Flask(__name__)

headers = {
    'user-agent': 'Instagram 113.0.0.39.122 Android (24/5.0; 515dpi; 1440x2416; huawei/google; Nexus 6P; angler; angler; en_US)',
}

@app.route("/")
def get_highlights():
    try:
        username = request.args.get("user")
        if not username:
            return jsonify({
                "status": "error",
                "message": "ضيف ?user=username"
            }), 400

        params = {'username': username}

        # 1️⃣ user info
        try:
            response = requests.get(
                'https://i.instagram.com/api/v1/users/web_profile_info/',
                params=params,
                headers=headers,
                impersonate="chrome110"
            )
        except Exception as e:
            return jsonify({
                "status": "error",
                "step": "request_user_info",
                "message": str(e)
            }), 500

        if response.status_code != 200:
            return jsonify({
                "status": "error",
                "step": "user_info_response",
                "code": response.status_code,
                "text": response.text[:300]
            }), 500

        data = response.json()

        if "data" not in data:
            return jsonify({
                "status": "error",
                "step": "user_data",
                "response": data
            }), 400

        user = data["data"]["user"]
        user_id = user["id"]

        result = {
            "status": "success",
            "user": {
                "username": user["username"],
                "id": user_id,
                "followers": user["edge_followed_by"]["count"],
                "following": user["edge_follow"]["count"]
            },
            "highlights": []
        }

        # 2️⃣ highlights
        try:
            highlights_res = requests.get(
                f'https://i.instagram.com/api/v1/highlights/{user_id}/highlights_tray/',
                headers=headers,
                impersonate="chrome110"
            )
        except Exception as e:
            return jsonify({
                "status": "error",
                "step": "request_highlights",
                "message": str(e)
            }), 500

        highlights_data = highlights_res.json()

        tray = highlights_data.get("tray", [])
        if not tray:
            result["note"] = "لا يوجد هايلايتس أو الحساب خاص"

        for h in tray:
            highlight_id = h.get("id")

            highlight_obj = {
                "id": highlight_id,
                "title": h.get("title", ""),
                "stories": []
            }

            # 3️⃣ items
            try:
                items_res = requests.get(
                    f'https://i.instagram.com/api/v1/feed/reels_media/?reel_ids=highlight:{highlight_id}',
                    headers=headers,
                    impersonate="chrome110"
                )
                items_data = items_res.json()
            except Exception as e:
                highlight_obj["error"] = str(e)
                result["highlights"].append(highlight_obj)
                continue

            items = items_data.get("reels", {}).get(f"highlight:{highlight_id}", {}).get("items", [])

            for item in items:
                try:
                    if "video_versions" in item:
                        highlight_obj["stories"].append({
                            "type": "video",
                            "url": item["video_versions"][0]["url"]
                        })

                    elif "image_versions2" in item:
                        highlight_obj["stories"].append({
                            "type": "image",
                            "url": item["image_versions2"]["candidates"][0]["url"])
                except Exception as e:
                    highlight_obj["stories"].append({
                        "error": str(e)
                    })

            result["highlights"].append(highlight_obj)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "fatal_error",
            "message": str(e)
        }), 500


# مهم لـ Vercel
app = app
