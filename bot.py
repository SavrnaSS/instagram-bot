import os
import time
import pickle
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
from selenium.common.exceptions import TimeoutException, WebDriverException

# ─── Load environment ─────────────────────────────────────────────────────────
load_dotenv()
USERNAME          = os.getenv("IG_USERNAME", "bellequotient")
PASSWORD          = os.getenv("IG_PASSWORD", "8426G65AKI51638286")
CHROMEDRIVER_PATH = shutil.which("chromedriver") or "/usr/local/bin/chromedriver"
BASE_IMAGE_DIR    = os.getenv("BASE_IMAGE_DIR", "/home/ubuntu/instagram_bot/pictures_selfie")
POST_SCHEDULE     = [
    {"image": os.path.join(BASE_IMAGE_DIR, "selfie_0.jpg"),
     "caption": "Did you missed me ?",
     "time": "2025-05-04 14:12:00"},
    {"image": os.path.join(BASE_IMAGE_DIR, "selfie_0.jpg"),
     "caption": "Hey, Whatsapp?",
     "time": "2025-05-04 14:13:00"},
]
IST = pytz.timezone("Asia/Kolkata")

# ─── Helpers ───────────────────────────────────────────────────────────────────
def wait_until(schedule_time_str: str):
    scheduled = IST.localize(datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M:%S"))
    while True:
        now_ist = datetime.now(pytz.utc).astimezone(IST)
        diff = (scheduled - now_ist).total_seconds()
        if diff > 0:
            print(f"[{schedule_time_str}] waiting {diff:.0f}s…")
            time.sleep(min(diff, 60))
        else:
            return

def save_cookies(driver):
    with open("cookies.pkl", "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver, wait):
    # Navigate once so cookies can be added
    try:
        driver.get("https://www.instagram.com/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception:
        pass
    # Load cookie file
    try:
        with open("cookies.pkl", "rb") as f:
            for c in pickle.load(f):
                try:
                    driver.add_cookie(c)
                except Exception:
                    continue
        print("✅ Loaded cookies safely")
    except FileNotFoundError:
        print("⚠️ No cookies file found")

def dismiss_overlays(driver, wait):
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='button' and @aria-label='Close']")))
        btn.click()
        time.sleep(1)
    except Exception:
        pass

# ─── Login Routine ─────────────────────────────────────────────────────────────
def login_to_instagram(driver, wait) -> bool:
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    # one-time cookie load
    load_cookies(driver, wait)
    driver.get(LOGIN_URL)
    time.sleep(2)

    # Accept cookie banner if present
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Allow all cookies']")))
        btn.click(); time.sleep(1)
    except Exception:
        pass

    dismiss_overlays(driver, wait)

    for attempt in range(1, 6):
        try:
            user = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
            pwd  = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
            user.clear(); user.send_keys(USERNAME)
            pwd.clear();  pwd.send_keys(PASSWORD); pwd.send_keys(Keys.ENTER)
            print(f"Submitted login (attempt {attempt})")
            driver.save_screenshot("login_attempt.png")
            time.sleep(5)

            save_cookies(driver)

            # Wait for Home icon to confirm login
            wait.until(EC.presence_of_element_located((By.XPATH, "//svg[@aria-label='Home']")))
            print("✅ Login successful")
            driver.save_screenshot("login_success.png")
            return True

        except TimeoutException:
            print(f"Login attempt {attempt} timed out, retrying...")
            time.sleep(3)
            driver.get(LOGIN_URL)
        except WebDriverException:
            print("⚠️ Browser crashed during login, will restart")
            return False

    print("❌ All login attempts failed")
    return False

# ─── Main Flow ─────────────────────────────────────────────────────────────────
def main():
    # Kill leftover Chrome processes
    subprocess.run(["pkill", "-f", "chrome"], check=False)
    time.sleep(1)

    chrome_opts = webdriver.ChromeOptions()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--window-size=1280,800")

    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver  = webdriver.Chrome(service=service, options=chrome_opts)
    wait    = WebDriverWait(driver, 15)

    # Attempt login, with one restart if tab crash occurs
    for _ in range(2):
        if login_to_instagram(driver, wait):
            break
        driver.quit()
        driver = webdriver.Chrome(service=service, options=chrome_opts)
        wait   = WebDriverWait(driver, 15)
    else:
        print("Unable to login after restart; exiting.")
        driver.quit()
        return

    dismiss_overlays(driver, wait)

    # Handle "Not Now" pop-ups
    for _ in range(2):
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
            btn.click(); time.sleep(1)
        except Exception:
            break

    # Scheduled posting
    for post in POST_SCHEDULE:
        print(f"\nPosting {post['image']} at {post['time']}")
        wait_until(post["time"])
        dismiss_overlays(driver, wait)

        inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        inp.send_keys(post["image"])
        time.sleep(2)

        # Click "Next" twice
        for _ in range(2):
            nxt = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']")))
            nxt.click(); time.sleep(2)

        cap = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//textarea[@aria-label='Write a caption…']")))
        cap.send_keys(post["caption"]); time.sleep(1)

        share = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Share']")))
        share.click(); time.sleep(10)
        print("✅ Posted!")

        driver.refresh()
        time.sleep(3)

    driver.quit()

if __name__ == "__main__":
    main()
