import json
import time
from datetime import datetime
import pytz
from instagrapi import Client
import os

SETTINGS_FILE = "settings.json"
SESSION_FILE = "session.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        print(f"❌ Error: {SETTINGS_FILE} not found!")
        return None
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        if "posts" not in data or not isinstance(data["posts"], list):
            print("❌ Error: 'posts' key missing or not a list in settings.json")
            return None
        print(f"✅ Loaded settings.json with {len(data['posts'])} posts")
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {SETTINGS_FILE}: {e}")
        return None

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("💾 Updated settings.json with posted flags")

def main():
    settings = load_settings()
    if not settings:
        return

    posts = settings["posts"]
    # Make sure each post has a "posted" flag
    for p in posts:
        p.setdefault("posted", False)

    cl = Client()
    username = posts[0].get("username")
    password = posts[0].get("password")
    if not username or not password:
        print("❌ Error: username/password missing in settings.json")
        return

    # Try loading saved session to avoid re-login
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            print("✅ Logged in using saved session!")
        except Exception as e:
            print(f"⚠️ Saved session invalid or expired: {e}")
            print("🔑 Logging in fresh...")
            cl = Client()
            cl.login(username, password)
            cl.dump_settings(SESSION_FILE)
            print("✅ Login successful and session saved!")
    else:
        # No saved session, login fresh and save session
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        print("✅ Login successful and session saved!")

    tz = pytz.timezone("Asia/Kolkata")

    while True:
        now = datetime.now(tz)
        print(f"\n⏰ Current IST time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        any_posted = False
        for post in posts:
            if post["posted"]:
                continue  # skip already posted

            try:
                sched = datetime.fromisoformat(post["post_time"])
                sched = tz.localize(sched)
            except Exception as e:
                print(f"❌ Invalid post_time for {post.get('image_path')}: {e}")
                post["posted"] = True
                any_posted = True
                continue

            print(f"  • Scheduled: {sched.strftime('%Y-%m-%d %H:%M:%S')}  Image: {post['image_path']}  Posted? {post['posted']}")

            if now >= sched:
                img = post.get("image_path")
                cap = post.get("caption", "")
                if not os.path.exists(img):
                    print(f"❌ File not found: {img}")
                else:
                    print(f"🚀 Posting {img}...")
                    try:
                        cl.photo_upload(img, cap)
                        print(f"✅ Posted {img}")
                    except Exception as e:
                        print(f"❌ Failed to post {img}: {e}")
                post["posted"] = True
                any_posted = True

        if any_posted:
            save_settings({"posts": posts})

        print("🛌 Sleeping for 60 seconds…")
        time.sleep(60)

if __name__ == "__main__":
    main()
