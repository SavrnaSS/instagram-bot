from instagrapi import Client
import time
import json
from datetime import datetime
import pytz
import os

def load_settings():
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
        return settings
    except FileNotFoundError:
        print("❌ Error: settings.json not found!")
        exit()
    except json.JSONDecodeError:
        print("❌ Error: settings.json is invalid JSON!")
        exit()

def get_ist_time():
    utc_now = datetime.utcnow()
    ist_tz = pytz.timezone('Asia/Kolkata')
    ist_now = utc_now.replace(tzinfo=pytz.utc).astimezone(ist_tz)
    return ist_now

def wait_until(post_time):
    while True:
        now = get_ist_time()
        if now >= post_time:
            print(f"✅ It's time to post! ({now.strftime('%Y-%m-%d %H:%M:%S')})")
            break
        else:
            print(f"⏳ Waiting... Current IST time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(30)

def post_image(cl, post):
    if not os.path.exists(post["image_path"]):
        print(f"❌ Error: Image file '{post['image_path']}' not found!")
        return

    try:
        media = cl.photo_upload(post["image_path"], post["caption"])
        print(f"✅ Photo posted successfully! Media ID: {media.pk}")
    except Exception as e:
        print(f"❌ Error occurred while posting {post['image_path']}: {e}")

def main():
    posts = load_settings()
    if not posts:
        print("❌ No posts found in settings.json!")
        exit()

    cl = Client()
    cl.login(posts[0]["username"], posts[0]["password"])
    print("✅ Logged in successfully!")

    for post in posts:
        post_time = datetime.strptime(post["post_time"], "%Y-%m-%dT%H:%M:%S")
        post_time = pytz.timezone('Asia/Kolkata').localize(post_time)

        print(f"🕒 Scheduling post for {post_time.strftime('%Y-%m-%d %H:%M:%S')} IST")
        wait_until(post_time)

        post_image(cl, post)

    print("✅ All scheduled posts completed!")

if __name__ == "__main__":
    main()
