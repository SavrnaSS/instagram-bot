from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os
import time
import pickle
import tempfile
import subprocess
import shutil
from shutil import which
import pytz  # Import timezone library
from dotenv import load_dotenv
from selenium.common.exceptions import TimeoutException

load_dotenv()

# --- User Settings ---
USERNAME = "bellequotient"  # Direct Instagram username
PASSWORD = "8426G65AKI51638286"  # Direct Instagram password
APP_PASSWORD = "yqzj lkxt occd clbp"  # Direct app password
GMAIL_EMAIL = "savarnasumit@gmail.com"  # Direct Gmail email
CHROMEDRIVER_PATH = which("chromedriver")  # Find chromedriver in system PATH

BASE_IMAGE_DIR = os.path.abspath("/home/ubuntu/instagram_bot/pictures_selfie/")  # Contains IMG_6876.jpg  

# --- Scheduling Settings ---
POST_SCHEDULE = [
    {"image": os.path.join(BASE_IMAGE_DIR, "IMG_6876"), "caption": "Did you missed me ?", "time": "2025-05-04 14:12:00"},
    {"image": os.path.join(BASE_IMAGE_DIR, "IMG_6876"), "caption": "Hey, Whatsapp?", "time": "2025-05-04 14:13:00"}
]

# Define IST timezone
IST = pytz.timezone("Asia/Kolkata")

def wait_until(schedule_time_str):
    """Waits until the scheduled time is reached before continuing."""
    scheduled_time = datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M:%S")
    
    # Convert scheduled time to IST
    scheduled_time = IST.localize(scheduled_time)
    
    while True:
        now = datetime.now(pytz.utc)  # Get UTC time and convert to IST
        now_ist = now.astimezone(IST)

        diff = (scheduled_time - now_ist).total_seconds()

        if diff > 0:
            print(f"Waiting {diff:.0f} seconds until scheduled posting time ({schedule_time_str})...")
            time.sleep(min(diff, 60))  # Sleep in shorter intervals to stay responsive
        else:
            print("Scheduled time reached; proceeding with posting.")
            break


def save_cookies(driver):
    cookies_dir = "/app/.cookies"  # Use a persistent directory in Render
    if not os.path.exists(cookies_dir):
        os.makedirs(cookies_dir)
    pickle.dump(driver.get_cookies(), open(os.path.join(cookies_dir, "cookies.pkl"), "wb"))


def load_cookies(driver):
    cookies_dir = "/app/.cookies"  # Persistent cookies directory
    try:
        cookies = pickle.load(open(os.path.join(cookies_dir, "cookies.pkl"), "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("Loaded cookies successfully.")
    except Exception:
        print("No saved cookies found.")


def dismiss_overlays(driver, wait):
    """Tries to dismiss any overlays blocking interactions."""
    try:
        close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Close']")))
        close_button.click()
        print("Closed an overlay before proceeding.")
        time.sleep(2)
    except Exception:
        print("No overlay found. Proceeding with post.")
        
        
def login_to_instagram(driver, wait):
    """Attempts to log in to Instagram, refreshing until the correct UI appears."""
    max_retries = 5  # Prevent infinite loops
    retries = 0

    while retries < max_retries:
        driver.get("https://www.instagram.com/accounts/login/")
        load_cookies(driver)
        time.sleep(5)  # Allow page to load

        try:
            # Check for the standard login UI
            username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            
            # Accept cookies if prompted
            try:
                cookie_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept All']")))
                cookie_btn.click()
                time.sleep(2)
            except Exception:
                pass  # No cookie pop-up, continue

            # If found, enter credentials and proceed
            username_field.send_keys(USERNAME)
            password_field.send_keys(PASSWORD)
            password_field.send_keys(Keys.ENTER)
            print("Login attempt successful.")
            save_cookies(driver)
            return  # Exit the function if login UI is found

        except Exception as e:
            print(f"Unexpected login UI detected. Refreshing... ({retries + 1}/{max_retries})")
            retries += 1
            driver.refresh()
            time.sleep(5)

    print("Max retries reached. Exiting script.")
    driver.quit()
    exit()


def kill_existing_chrome_processes():
    """Kill any lingering Chrome processes that might lock the user data directory."""
    try:
        subprocess.run(["pkill", "-f", "chrome"], check=False)
        print("Killed existing Chrome processes.")
        time.sleep(1)  # Give time for processes to terminate
    except Exception as e:
        print(f"Error killing Chrome processes: {e}")


def attempt_action(wait, xpath, action_name, max_attempts=3):
    """Attempts an action with retries."""
    for attempt in range(max_attempts):
        try:
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            element.click()
            print(f"Clicked on {action_name}.")
            return True
        except TimeoutException:
            print(f"Attempt {attempt + 1}/{max_attempts} failed for {action_name}.")
            if attempt < max_attempts - 1:
                time.sleep(2)  # Wait before retrying
    raise TimeoutException(f"Failed to locate {action_name} after {max_attempts} attempts")


def main():
    # Kill any existing Chrome processes to free up resources
    kill_existing_chrome_processes()

    # Create a unique temporary directory for Chrome user data
    user_data_dir = "/app/.chrome_profile"  # Use a persistent directory in Render

    if os.path.exists(user_data_dir):
        print(f"Warning: Directory {user_data_dir} exists. Attempting to remove it.")
        try:
            shutil.rmtree(user_data_dir)
        except Exception as e:
            print(f"Error removing directory: {e}")
            user_data_dir = "/app/.chrome_profile"  # Create a new one if removal fails

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--headless=new")  # Run Chrome in headless mode
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")  # Specify persistent user data directory
    chrome_options.add_argument("--no-sandbox")  # Required for some Linux environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # Prevents crashes in Docker
    
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # 1. Log in to Instagram with retry logic
        login_to_instagram(driver, wait)
        time.sleep(5)  # Allow time after login
        # ✅ Dismiss the "Not Now" pop-up after login
        dismiss_overlays(driver, wait)

        # ✅ Handle "Save Your Login Info?" pop-up
        for _ in range(2):
            try:
                not_now_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
                not_now_btn.click()
                print("Clicked 'Not Now' button.")
                time.sleep(2)
            except Exception:
                pass

        # Loop through the scheduled posts
        for post in POST_SCHEDULE:
            wait_until(post["time"])  # Wait for scheduled time

            dismiss_overlays(driver, wait)  # ✅ Ensure nothing blocks interaction

            # 2. Click on the "Create" (plus) button
            create_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[local-name()='svg' and @aria-label='New post']/ancestor::div[1]")
            ))
            create_btn.click()
            print("Clicked on the Create button.")
            time.sleep(2)

            # 3. Click on the "Post" option
            post_option = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[.//span[contains(text(),'Post')]]")
            ))
            post_option.click()
            print("Clicked on the 'Post' option.")
            time.sleep(3)

            # 4. Click "Select From Computer"
            select_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Select From Computer']")
            ))
            select_btn.click()
            print("Clicked on 'Select From Computer' button.")
            time.sleep(2)

            # 5. Upload the correct image
            file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
            file_input.send_keys(post["image"])
            print(f"Uploaded image: {post['image']}")
            time.sleep(3)

            # 6. Click "Next"
            for _ in range(2):  # There are two "Next" buttons
                next_div = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(@class, '_ac7b') and contains(@class, '_ac7d')]//div[normalize-space()='Next']")
                ))
                next_div.click()
                print("Clicked 'Next' button.")
                time.sleep(3)

            # 7. Enter the caption
            caption_div = wait.until(EC.presence_of_element_located((By.XPATH, "//textarea[@aria-label='Write a caption…']")))
            caption_div.send_keys(post["caption"])
            print(f"Entered caption: {post['caption']}")

            # 8. Finally, click "Share" to post
            share_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Share']")
            ))
            share_button.click()
            print(f"Posted image with caption: {post['caption']}")

            time.sleep(5)  # Wait a bit before next post

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
