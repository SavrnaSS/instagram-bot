from seleniumwire import webdriver    # Selenium‑Wire’s webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from datetime import datetime
import os, time, pickle, tempfile, subprocess, shutil, pytz
from shutil import which
from dotenv import load_dotenv

load_dotenv()

# ─── Settings ────────────────────────────────────────────────────────────────
USERNAME          = os.getenv("US")
PASSWORD          = os.getenv("PAS")
CHROMEDRIVER_PATH = which("chromedriver")
BASE_IMAGE_DIR    = "/home/ubuntu/instagram_bot/pictures_selfie"
POST_SCHEDULE     = [
    {"image": os.path.join(BASE_IMAGE_DIR, "selfie_0.jpg"), "caption": "Did you missed me ?", "time": "2025-05-04 14:12:00"},
    {"image": os.path.join(BASE_IMAGE_DIR, "selfie_0.jpg"), "caption": "Hey, Whatsapp?",    "time": "2025-05-04 14:13:00"}
]
IST = pytz.timezone("Asia/Kolkata")

# ─── Proxy (authenticated) ───────────────────────────────────────────────────
#PROXY_HOST, PROXY_PORT = "82.23.67.179", "5437"
#PROXY_USER, PROXY_PASS = "nftiuvfu", "8ris7fu5rgrn"
#proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
#seleniumwire_options = {
    #'proxy': {'http': proxy_url, 'https': proxy_url, 'no_proxy': 'localhost,127.0.0.1'}
#}

# ── Helpers ───────────────────────────────────────────────────────────────────
def wait_until(schedule_time_str):
    scheduled = IST.localize(datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M:%S"))
    while True:
        now_ist = datetime.now(pytz.utc).astimezone(IST)
        diff = (scheduled - now_ist).total_seconds()
        if diff > 0:
            print(f"[{schedule_time_str}] waiting {diff:.0f}s…")
            time.sleep(min(diff,60))
        else:
            print(f"[{schedule_time_str}] reached.")
            return

def save_cookies(driver):
    pickle.dump(driver.get_cookies(), open("cookies.pkl","wb"))

def load_cookies(driver):
    try:
        for c in pickle.load(open("cookies.pkl","rb")):
            driver.add_cookie(c)
        print("✅ loaded cookies")
    except FileNotFoundError:
        print("⚠️ no cookies found")

def dismiss_overlays(driver, wait):
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@role='button' and @aria-label='Close']")))
        btn.click()
        print("Closed overlay")
        time.sleep(1)
    except:
        pass

# ── Login ─────────────────────────────────────────────────────────────────────
def login_to_instagram(driver, wait):
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    for attempt in range(1, 6):
        driver.get(LOGIN_URL)
        load_cookies(driver)
        time.sleep(3)

        # accept cookie banner
        try:
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Allow all cookies']")))
            btn.click()
            print("🍪 accepted cookies")
            time.sleep(1)
        except TimeoutException:
            pass

        # dismiss any modal overlays
        dismiss_overlays(driver, wait)

        try:
            # locate inputs by name
            user_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='username']")))
            pass_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='password']")))

            # click or JS-click username
            try:
                user_input.click()
            except ElementClickInterceptedException:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", user_input)
                driver.execute_script("arguments[0].click();", user_input)

            user_input.clear()
            user_input.send_keys(USERNAME)

            # click or JS-click password
            try:
                pass_input.click()
            except ElementClickInterceptedException:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", pass_input)
                driver.execute_script("arguments[0].click();", pass_input)

            pass_input.clear()
            pass_input.send_keys(PASSWORD)
            pass_input.send_keys(Keys.ENTER)
            print(f"Submitted login (attempt {attempt})")
            driver.save_screenshot("login_attempt.png")
            time.sleep(6)

            save_cookies(driver)

           # checkpoint?
            if "challenge" in driver.current_url:
                print("⚠️ checkpoint encountered"); return False

            # ── NEW: wait for the Home icon SVG ────────────────────
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//svg[@aria-label='Home']")))
            print("✅ login successful")

            # screenshot on success
            sp2 = "/tmp/login_success.png"
            ok2 = driver.save_screenshot(sp2)
            print("Saved success screenshot?", ok2, "→", sp2)
            return True

        except TimeoutException as e:
            print(f"Login attempt {attempt} timed out:", e)
            time.sleep(5)

    print("❌ all login attempts failed")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    subprocess.run(["pkill","-f","chrome"], check=False)
    time.sleep(1)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--headless")            # headless ON for EC2
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=ChromeService(executable_path=CHROMEDRIVER_PATH),
        options=chrome_options,
        #seleniumwire_options=seleniumwire_options
    )
    wait = WebDriverWait(driver, 15)

    if not login_to_instagram(driver, wait):
        print("Login failed or checkpointed; exiting.")
        driver.quit()
        return

    dismiss_overlays(driver, wait)

    try:
        for post in POST_SCHEDULE:
            print(f"\nPosting {post['image']} at {post['time']}")
            wait_until(post["time"])
            dismiss_overlays(driver, wait)

            inp = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='file']")))
            inp.send_keys(post["image"])
            print("📤 image uploaded")
            time.sleep(2)

            for label in ("Next","Next"):
                btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//button[normalize-space()='{label}']")))
                btn.click()
                print(f"➡️ clicked {label}")
                time.sleep(2)

            cap = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//textarea[@aria-label='Write a caption…']")))
            cap.send_keys(post["caption"])
            print("✍️ caption entered")
            time.sleep(1)

            share = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Share']")))
            share.click()
            print("🚀 clicked Share")
            time.sleep(10)

            print("✅ posted!")
            driver.refresh()
            time.sleep(3)

    except Exception as e:
        print("Error during posting:", type(e).__name__, e)
        driver.save_screenshot("error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
