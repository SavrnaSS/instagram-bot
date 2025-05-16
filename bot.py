import json
import time
from instagrapi import Client

def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error: settings.json not found or invalid!")
        print(f"❌ Exiting due to missing or invalid settings.json")
        exit(1)

def main():
    settings = load_settings()

    username = settings.get("username")
    password = settings.get("password")
    image_path = settings.get("image_path")
    caption = settings.get("caption")
    sleep_hours = settings.get("sleep_hours", 24)

    cl = Client()
    try:
        cl.login(username, password)
        print("✅ Logged in successfully!")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return

    try:
        cl.photo_upload(image_path, caption)
        print("✅ Photo uploaded!")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

    print(f"⏳ Sleeping for {sleep_hours} hours before next post...")
    time.sleep(sleep_hours * 3600)

if __name__ == "__main__":
    main()
