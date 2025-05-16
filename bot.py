from instagrapi import Client
from datetime import datetime, timedelta
import time
import json
import os
import pytz

def load_settings():
    if not os.path.exists("settings.json"):
        print("❌ Error: settings.json not found!")
        return None
    with open("settings.json", "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: Invalid settings.json format!")
            return None

def post_image(cl, username, image_path, caption):
    print(f"📤 Uploading {image_path} with caption: {caption}")
    cl.photo_upload(image_path, caption)
    print(f"✅ Posted {image_path} successfully!")

def main():
    settings = load_settings()
    if not settings or "posts" not in settings:
        print("❌ Exiting due to missing or invalid settings.json")
        return

    posts = settings["posts"]
    if not posts:
        print("❌ No posts found in settings.json")
        return

    # Login once
    cl = Client()
    cl.login(posts[0]["username"], posts[0]["password"])

    india_tz = pytz.timezone('Asia/Kolkata')

    while True:
        now = datetime.now(india_tz).replace(second=0, microsecond=0)
        print(f"🕒 Current India Time: {now}")

        for post in posts:
            post_time = datetime.fromisoformat(post["post_time"]).astimezone(india_tz).replace(second=0, microsecond=0)
            if now == post_time:
                post_image(cl, post["username"], post["image_path"], post["caption"])

        time.sleep(60)

if __name__ == "__main__":
    main()
