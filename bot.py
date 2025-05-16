from instagrapi import Client
import time

def main():
    cl = Client()
    cl.load_settings("settings.json")
    cl.login("bellequotient", "8426G65AKI51638286")

    media_path = "image.jpg"
    caption = "Hello from Render! 🚀"

    cl.photo_upload(media_path, caption)
    print("✅ Post uploaded successfully")

if __name__ == "__main__":
    while True:
        try:
            main()
            print("✅ Task completed, sleeping 24h")
            time.sleep(86400)  # sleep for 1 day
        except Exception as e:
            print(f"❌ Error occurred: {e}")
            time.sleep(60)  # retry after 1 minute
