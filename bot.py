import os
import time
import pickle
import tempfile
import subprocess
import shutil
from datetime import datetime

import pytz
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

# Load .env
load_dotenv()

# ─── Settings ────────────────────────────────────────────────────────────────
USERNAME          = os.getenv("US", "bellequotient")
PASSWORD          = os.getenv("PAS", "8426G65AKI51638286")
CHROMEDRIVER_PATH = shutil.which("chromedriver") or "/usr/local/bin/chromedriver"
BASE_IMAGE_DIR    = os.getenv("BASE_IMAGE_DIR", "/home/ubuntu/instagram_bot/pictures_selfie")
POST_SCHEDULE     = [
    {"image": os.path.join(BASE_IMAGE_DIR, "selfie_0.jpg"),
     "caption": "Did you missed me ?",
     "time": "2025-05-04 14:12:00"},
    {"image": os.path.join(BASE_IMAGE_DIR, "selfie_0.jpg"),
     "caption": "Hey, Whatsapp?",
     "time": "2025-05-04 14:13:00"}
]
IST = pytz.timezone("Asia/Kolkata")

# ── Helpers ───────────────────────────────────────────────────────────────────
def wait_until(schedule_time_str: str):
    scheduled = IST.localize(datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M:%S"))
    while True:
        now_ist = datetime.now(pytz.utc).astimezone(IST)
        diff = (scheduled - now_ist).total_seconds()
        if diff > 0:
            print(f"[{schedule_time_str}] waiting {diff:.0f}s…")
            time.sleep(min(diff, 60))
        else:
            print(f"[{schedule_time_str}] reached.")
            return

def save_cookies(driver):
    with open("cookies.pkl", "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver):
    try:
        with open("cookies.pkl", "rb") as f:
            for cookie in pickle.load(f):
                driver.add_cookie(cookie)
        print("✅ Loaded cookies")
    except FileNotFoundError:
        print("⚠️ No cookies found")

def dismiss_overlays(driver, wait):
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='button' and @aria-label='Close']")))
        btn.click()
        print("Closed overlay")
        time.sleep(1)
    except Exception:
        pass

# ── Login ─────────────────────────────────────────────────────────────────────
def login_to_instagram(driver, wait) -> bool:
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    for attempt in range(1, 6):
        driver.get(LOGIN_URL)
        time.sleep(3)
        load_cookies(driver)

        # Accept cookies banner if present
        try:
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Allow all cookies']")))
            btn.click()
            print("🍪 Accepted cookies")
            time.sleep(1)
        except TimeoutException:
            pass

        dismiss_overlays(driver, wait)

        try:
            user_input = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
            pass_input = wait.until(EC.element_to_be_clickable((By.NAME, "password")))

            # Enter credentials
            user_input.clear()
            user_input.send_keys(USERNAME)

            pass_input.clear()
            pass_input.send_keys(PASSWORD)
            pass_input.send_keys(Keys.ENTER)
            print(f"Submitted login (attempt {attempt})")
            driver.save_screenshot("login_attempt.png")
            time.sleep(6)

            save_cookies(driver)

            # Check for checkpoint
            if "challenge" in driver.current_url:
                print("⚠️ Checkpoint encountered")
                return False

            # Confirm home icon
            wait.until(EC.presence_of_element_located((By.XPATH, "//svg[@aria-label='Home']")))
            print("✅ Login successful")
            driver.save_screenshot("login_success.png")
            return True

        except TimeoutException as e:
            print(f"Login attempt {attempt} timed out:", e)
            time.sleep(5)

    print("❌ All login attempts failed")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Kill existing Chrome to avoid conflicts
    subprocess.run(["pkill", "-f", "chrome"], check=False)
    time.sleep(1)

    # Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Launch
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 15)

    if not login_to_instagram(driver, wait):
        print("Login failed; exiting.")
        driver.quit()
        return

    dismiss_overlays(driver, wait)

    try:
        # Close "Save Your Login Info?" pop-ups
        for _ in range(2):
            try:
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
                btn.click()
                print("Clicked 'Not Now'")
                time.sleep(1)
            except Exception:
                break

        # Scheduled posts
        for post in POST_SCHEDULE:
            print(f"\nPosting {post['image']} at {post['time']}")
            wait_until(post["time"])
            dismiss_overlays(driver, wait)

            # File upload input
            inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
            inp.send_keys(post["image"])
            print("📤 Uploaded image")
            time.sleep(2)

            # Click through Next, Next
            for _ in range(2):
                nxt = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space()='Next']")))
                nxt.click()
                print("➡️ Clicked Next")
                time.sleep(2)

            # Caption
            cap = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//textarea[@aria-label='Write a caption…']")))
            cap.send_keys(post["caption"])
            print("✍️ Caption entered")
            time.sleep(1)

            # Share
            share = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Share']")))
            share.click()
            print("🚀 Clicked Share")
            time.sleep(10)

            print("✅ Posted!")
            driver.refresh()
            time.sleep(3)

    except Exception as e:
        print("Error during posting:", type(e).__name__, e)
        driver.save_screenshot("error.png")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
