import json
import time
from datetime import datetime, timedelta
import pytz
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import os

SETTINGS_FILE = "settings.json"
SESSION_FILE = "session.json"
FOLLOWED_USERS_FILE = "followed_users.json"

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
        if "target_post_urls" not in data or not isinstance(data["target_post_urls"], list):
            print("❌ Error: 'target_post_urls' key missing or not a list in settings.json")
            return None
        print(f"✅ Loaded settings.json with {len(data['posts'])} posts and {len(data['target_post_urls'])} target posts")
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {SETTINGS_FILE}: {e}")
        return None

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("💾 Updated settings.json")

def load_followed_users():
    if not os.path.exists(FOLLOWED_USERS_FILE):
        return []
    try:
        with open(FOLLOWED_USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_followed_users(users):
    with open(FOLLOWED_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)
    print(f"💾 Saved followed users list ({len(users)} users)")

def login_client(cl, username, password):
    try:
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            print("✅ Logged in using saved session!")
        else:
            cl.login(username, password)
            cl.dump_settings(SESSION_FILE)
            print("✅ Login successful and session saved!")
    except Exception as e:
        print(f"⚠️ Saved session invalid or expired: {e}")
        print("🔑 Logging in fresh...")
        cl = Client()
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        print("✅ Login successful and session saved!")
    return cl

def get_media_id_from_url(cl, url):
    try:
        media = cl.media_pk_from_url(url)
        return media
    except Exception as e:
        print(f"❌ Failed to get media ID from URL {url}: {e}")
        return None

def follow_commenters_of_post(cl, media_id, followed_users, max_follow=80):
    new_follows = 0
    try:
        commenters = cl.media_comments(media_id, amount=1000)
    except LoginRequired:
        print("⚠️ Session expired during fetching comments, re-logging in...")
        raise

    for comment in commenters:
        user_id = comment.user.pk
        username = comment.user.username
        if user_id not in followed_users and new_follows < max_follow:
            try:
                cl.user_follow(user_id)
                print(f"➕ Followed: {username} (user_id: {user_id})")
                followed_users.append(user_id)
                new_follows += 1
                time.sleep(5)  # avoid spam detection
            except Exception as e:
                print(f"❌ Failed to follow {username}: {e}")
                if "feedback_required" in str(e).lower():
                    print("🚫 Instagram has temporarily blocked following. Exiting follow task early.")
                    break
    return new_follows

def main():
    settings = load_settings()
    if not settings:
        return

    posts = settings["posts"]
    for p in posts:
        p.setdefault("posted", False)

    target_post_urls = settings["target_post_urls"]

    username = posts[0].get("username")
    password = posts[0].get("password")
    if not username or not password:
        print("❌ Error: username/password missing in settings.json")
        return

    cl = Client()
    cl = login_client(cl, username, password)

    tz = pytz.timezone("Asia/Kolkata")

    followed_users = load_followed_users()

    # To rotate target posts daily for following commenters:
    last_follow_date = None
    current_target_index = 0

    # To control follow once per 24 hours without blocking posting
    next_follow_time = datetime.now(tz) - timedelta(seconds=1)  # start immediately

    print("🚀 Bot started. Posting and following will run continuously...")

    while True:
        now = datetime.now(tz)
        print(f"\n⏰ Current IST time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Posting logic (runs every 60 seconds)
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

        # Follow commenters logic (runs once per 24 hours independently)
        if now >= next_follow_time:
            print(f"🚶‍♂️ Starting follow commenters task...")

            # Rotate through target posts daily
            days_since_epoch = (now.date() - datetime(1970,1,1).date()).days
            current_target_index = days_since_epoch % len(target_post_urls)
            target_post_url = target_post_urls[current_target_index]

            media_id = get_media_id_from_url(cl, target_post_url)
            if media_id is None:
                print(f"❌ Could not get media_id for target post {target_post_url}")
            else:
                try:
                    new_follows = follow_commenters_of_post(cl, media_id, followed_users, max_follow=80)
                    if new_follows > 0:
                        save_followed_users(followed_users)
                    else:
                        print("ℹ️ No new users to follow today.")
                except LoginRequired:
                    print("⚠️ Session expired during follow task, re-logging in...")
                    cl = login_client(cl, username, password)
                    # Retry follow after re-login
                    try:
                        new_follows = follow_commenters_of_post(cl, media_id, followed_users, max_follow=80)
                        if new_follows > 0:
                            save_followed_users(followed_users)
                    except Exception as e:
                        print(f"❌ Failed again after re-login: {e}")

            # Schedule next follow 24 hours later
            next_follow_time = now + timedelta(hours=24)
            print(f"⏳ Next follow task scheduled at {next_follow_time.strftime('%Y-%m-%d %H:%M:%S')}")

        print("🛌 Sleeping for 60 seconds…")
        time.sleep(60)

if __name__ == "__main__":
    main()
