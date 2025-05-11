from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import os
import time
import pickle
import tempfile
import subprocess
import shutil
from shutil import which
import pytz
from dotenv import load_dotenv

load_dotenv()

# --- User Settings ---
USERNAME = "bellequotient"
PASSWORD = "8426G65AKI51638286"
APP_PASSWORD = "yqzj lkxt occd clbp"
GMAIL_EMAIL = "savarnasumit@gmail.com"
CHROMEDRIVER_PATH = which("chromedriver")

BASE_IMAGE_DIR = os.path.abspath("/home/ubuntu/instagram_bot/pictures_selfie/")

POST_SCHEDULE = [
    {"image": os.path.join(BASE_IMAGE_DIR, "IMG_6876"), "caption": "Did you missed me ?", "time": "2025-05-04 14:12:00"},
    {"image": os.path.join(BASE_IMAGE_DIR, "IMG_6876"), "caption": "Hey, Whatsapp?", "time": "2025-05-04 14:13:00"}
]

IST = pytz.timezone("Asia/Kolkata")

def wait_until(schedule_time_str):
    scheduled_time = datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M:%S")
    scheduled_time = IST.localize(scheduled_time)
    while True:
        now = datetime.now(pytz.utc).astimezone(IST)
        diff = (scheduled_time - now).total_seconds()
        if diff > 0:
            print(f"Waiting {diff:.0f} seconds until scheduled posting time ({schedule_time_str})...")
            time.sleep(min(diff, 60))
        else:
            print("Scheduled time reached; proceeding with posting.")
            break

def save_cookies(driver):
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))

def load_cookies(driver):
    try:
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("Loaded cookies successfully.")
    except Exception:
        print("No saved cookies found.")

def kill_existing_chrome_processes():
    try:
        subprocess.run(["pkill", "-f", "chrome"], check=False)
        print("Killed existing Chrome processes.")
        time.sleep(1)
    except Exception as e:
        print(f"Error killing Chrome processes: {e}")

def dismiss_overlays(driver, wait):
    try:
        close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Close']")))
        close_button.click()
        print("Closed an overlay before proceeding.")
        time.sleep(2)
    except Exception:
        print("No overlay found. Proceeding with post.")

def login_to_instagram(driver, wait):
    max_retries = 5
    retries = 0
    while retries < max_retries:
        driver.get("https://www.instagram.com/accounts/login/")
        load_cookies(driver)
        time.sleep(5)
        try:
            username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            try:
                cookie_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept All']")))
                cookie_btn.click()
                time.sleep(2)
            except Exception:
                pass
            username_field.send_keys(USERNAME)
            password_field.send_keys(PASSWORD)
            password_field.send_keys(Keys.ENTER)
            print("Login attempt successful.")
            save_cookies(driver)
            return
        except Exception:
            print(f"Unexpected login UI detected. Refreshing... ({retries + 1}/{max_retries})")
            retries += 1
            driver.refresh()
            time.sleep(5)
    print("Max retries reached. Exiting script.")
    driver.quit()
    exit()

def main():
    kill_existing_chrome_processes()

    user_data_dir = tempfile.mkdtemp(prefix="chrome_profile_")
    if os.path.exists(user_data_dir):
        print(f"Warning: Directory {user_data_dir} exists. Attempting to remove it.")
        try:
            shutil.rmtree(user_data_dir)
        except Exception as e:
            print(f"Error removing directory: {e}")
            user_data_dir = tempfile.mkdtemp(prefix="chrome_profile_")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        login_to_instagram(driver, wait)
        time.sleep(5)
        dismiss_overlays(driver, wait)

        for _ in range(2):
            try:
                not_now_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
                not_now_btn.click()
                print("Clicked 'Not Now' button.")
                time.sleep(2)
            except Exception:
                pass

        for post in POST_SCHEDULE:
            wait_until(post["time"])
            dismiss_overlays(driver, wait)

            create_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[local-name()='svg' and @aria-label='New post']/ancestor::div[1]")))
            create_btn.click()
            print("Clicked on the Create button.")
            time.sleep(2)

            post_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[.//span[contains(text(),'Post')]]")))
            post_option.click()
            print("Clicked on the 'Post' option.")
            time.sleep(3)

            select_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Select From Computer']")))
            select_btn.click()
            print("Clicked on 'Select From Computer' button.")
            time.sleep(2)

            file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
            file_input.send_keys(post["image"])
            print(f"Uploaded image: {post['image']}")
            time.sleep(3)

            for _ in range(2):
                next_div = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, '_ac7b') and contains(@class, '_ac7d')]//div[normalize-space()='Next']")))
                next_div.click()
                print("Clicked 'Next' button.")
                time.sleep(3)

            caption_div = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Write a caption...' and @contenteditable='true']")))
            caption_div.click()
            caption_div.send_keys(post["caption"])
            print(f"Caption entered: {post['caption']}")
            time.sleep(2)

            final_share = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, '_ac7b') and contains(@class, '_ac7d')]//div[normalize-space()='Share']")))
            final_share.click()
            print("Clicked 'Share' button. Post should be uploaded.")
            time.sleep(12)

            driver.refresh()
            print("Page refreshed after posting.")
            time.sleep(4)

    except Exception as e:
        print("An error occurred:", repr(e))
        screenshot_path = os.path.abspath("error_screenshot.png")
        driver.save_screenshot(screenshot_path)
        print("Screenshot saved to:", screenshot_path)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
