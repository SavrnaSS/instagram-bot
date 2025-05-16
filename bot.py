import os
from instagrapi import Client
from dotenv import load_dotenv
from datetime import datetime
import pytz, time

load_dotenv()
USERNAME = os.getenv("US")
PASSWORD = os.getenv("PAS")

POST_SCHEDULE = [
    {"image": "pictures_selfie/selfie_0.jpg", "caption": "Did you missed me ?", "time": "2025-05-04 14:12:00"},
    {"image": "pictures_selfie/selfie_1.jpg", "caption": "Hey, Whatsapp?",    "time": "2025-05-04 14:13:00"}
]
IST = pytz.timezone("Asia/Kolkata")

def wait_until(ts):
    target = IST.localize(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"))
    while True:
        now = datetime.now(pytz.utc).astimezone(IST)
        diff = (target - now).total_seconds()
        if diff>0:
            print(f"Waiting {diff:.0f}s…"); time.sleep(min(diff,60))
        else:
            return

def main():
    cl = Client()
    cl.login(USERNAME, PASSWORD)
    print("✅ Logged in via instagrapi")

    for post in POST_SCHEDULE:
        print(f"Scheduling {post['image']} at {post['time']}")
        wait_until(post["time"])
        media = cl.photo_upload(post["image"], post["caption"])
        print("✅ Uploaded:", media.pk)

if __name__=="__main__":
    main()
