import json
import time
from datetime import datetime
from instagrapi import Client

def load_settings():
    with open("settings.json", "r") as f:
        return json.load(f)

def post_image(cl, image_path, caption):
    print(f"📸 Uploading {image_path} with caption: {caption}")
    cl.photo_upload(image_path, caption)
    print(f"✅ Posted {image_path} successfully!")

def main():
    settings = load_settings()
    username = settings["username"]
    password = settings["password"]
    posts = settings["posts"]

    cl = Client()
    cl.login(username, password)

    while posts:
        now = datetime.now()
        for post in posts[:]:
            post_time = datetime.fromisoformat(post["post_time"])
            if now >= post_time:
                try:
                    post_image(cl, post["image_path"], post["caption"])
                    posts.remove(post)
                except Exception as e:
                    print(f"❌ Failed to post {post['image_path']}: {e}")

        if not posts:
            print("🎉 All posts done. Exiting.")
            break

        time.sleep(60)  # check every minute

if __name__ == "__main__":
    main()
