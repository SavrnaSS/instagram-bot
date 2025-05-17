import json
import time
from datetime import datetime, timedelta
import pytz
from instagrapi import Client
import os

SETTINGS_FILE = "settings.json"
SESSION_FILE = "session.json"
FOLLOWED_FILE = "followed_users.json"

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

def load_follow_history():
    if not os.path.exists(FOLLOWED_FILE):
        return set()
    try:
        with open(FOLLOWED_FILE, "r") as f:
            data = json.load(f)
            return set(data)
    except json.JSONDecodeError:
        return set()

def save_follow_history(history_set):
    with open(FOLLOWED_FILE, "w") as f:
        json.dump(list(history_set), f, indent=2)

def follow_commenters_of_post(cl, post_url, daily_limit=80):
    print(f"🔍 Fetching commenters for post: {post_url}")
    media_id = cl.media_pk_from_url(post_url)
    print(f"✅ Got Media ID: {media_id}")

    commenters = cl.media_comments(media_id, amount=1000)
    print(f"💬 Found {len(commenters)} comments")

    followed_today = 0
    follow_history = load_follow_history()

    for comment in commenters:
        user_id = comment.user.pk
        username = comment.user.username

        if str(user_id) in follow_history:
            print(f"➡️ Already followed {username} (skipping)")
            continue

        try:
            cl.user_follow(user_id)
            follow_history.add(str(user_id))
            followed_today += 1
            print(f"✅ Followed {username} | Total today: {followed_today}/{daily_limit}")
            time.sleep(10)  # Safe delay between follows
        except Exception as e:
            print(f"❌ Failed to follow {username}: {e}")

        if followed_today >= daily_limit:
            print(f"🚫 Reached daily follow limit of {daily_limit}")
            break

    save_follow_history(follow_history)
    print(f"💾 Updated follow history with {followed_today} new follows today")
    return followed_today

def main():
    settings = load_settings()
    if not settings:
        return

    posts = settings["posts"]
    for p in posts:
        p.setdefault("posted", False)

    cl = Client()
    username = posts[0].get("username")
    password = posts[0].get("password")
    if not username or not password:
        print("❌ Error: username/password missing in settings.json")
        return

    # Login & session management
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            print("✅ Logged in using saved session!")
        except Exception as e:
            print(f"⚠️ Saved session invalid: {e} | Logging in fresh…")
            cl = Client()
            cl.login(username, password)
            cl.dump_settings(SESSION_FILE)
            print("✅ Login successful & session saved!")
    else:
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        print("✅ Login successful & session saved!")

    tz = pytz.timezone("Asia/Kolkata")
    last_follow_time = None

    while True:
        now = datetime.now(tz)
        print(f"\n⏰ Current IST time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # --- Posting logic (runs every minute) ---
        any_posted = False
        for post in posts:
            if post["posted"]:
                continue

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

        # --- Follow commenters logic (once per 24h) ---
        if not last_follow_time or (now - last_follow_time).total_seconds() >= 86400:
            target_post_urls = settings.get("target_post_urls", [])
            if target_post_urls:
                today = now.date()
                index = (today.toordinal() % len(target_post_urls))
                today_post_url = target_post_urls[index]
                print(f"📅 Today ({today}) targeting post: {today_post_url}")

                follow_commenters_of_post(cl, today_post_url, daily_limit=80)
                last_follow_time = now
            else:
                print("⚠️ 'target_post_urls' not found in settings.json")

        # --- Sleep 60s before next post check ---
        print("🛌 Sleeping for 60 seconds (posting check continues)...")
        time.sleep(60)

if __name__ == "__main__":
    main()
