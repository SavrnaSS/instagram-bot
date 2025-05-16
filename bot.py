import os, time, pickle, subprocess, shutil
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

# ─── Setup ─────────────────────────────────────────────────────────────────────
load_dotenv()
USERNAME   = os.getenv("IG_USERNAME", "bellequotient")
PASSWORD   = os.getenv("IG_PASSWORD", "8426G65AKI51638286")
CHROME_PATH= shutil.which("chromedriver") or "/usr/local/bin/chromedriver"
BASE_DIR   = os.getenv("BASE_IMAGE_DIR", "/home/ubuntu/instagram_bot/pictures_selfie")
POSTS      = [{"image": os.path.join(BASE_DIR,"selfie_0.jpg"),
               "caption":"Did you missed me ?",
               "time":"2025-05-04 14:12:00"}]
IST = pytz.timezone("Asia/Kolkata")

def wait_until(ts):
    target = IST.localize(datetime.strptime(ts,"%Y-%m-%d %H:%M:%S"))
    while True:
        now = datetime.now(pytz.utc).astimezone(IST)
        diff = (target-now).total_seconds()
        if diff>0:
            print(f"Waiting {diff:.0f}s…"); time.sleep(min(diff,60))
        else:
            return

def save_cookies(d):
    with open("cookies.pkl","wb") as f: pickle.dump(d.get_cookies(),f)

def load_cookies(d,wait):
    try:
        d.get("https://www.instagram.com/"); wait.until(EC.presence_of_element_located((By.TAG_NAME,"body")))
    except: pass
    try:
        with open("cookies.pkl","rb") as f:
            for c in pickle.load(f):
                try: d.add_cookie(c)
                except: pass
        print("✅ Loaded cookies")
    except FileNotFoundError:
        print("⚠️ No cookies")

def build_driver():
    opts = webdriver.ChromeOptions()
    # New headless mode
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,800")
    # Anti-detection
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    # Remote debugging
    opts.add_argument("--remote-debugging-port=9222")
    service = ChromeService(executable_path=CHROME_PATH)
    d = webdriver.Chrome(service=service, options=opts)
    # Navigator.webdriver override
    d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
      "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return d

def login(d,wait):
    url="https://www.instagram.com/accounts/login/"
    load_cookies(d,wait)
    d.get(url); time.sleep(2)
    for i in range(1,6):
        try:
            user=wait.until(EC.element_to_be_clickable((By.NAME,"username")))
            pw  =wait.until(EC.element_to_be_clickable((By.NAME,"password")))
            user.clear(); user.send_keys(USERNAME)
            pw.clear(); pw.send_keys(PASSWORD); pw.send_keys(Keys.ENTER)
            print(f"Login attempt {i}")
            d.save_screenshot(f"login{i}.png"); time.sleep(5)
            save_cookies(d)
            wait.until(EC.presence_of_element_located((By.XPATH,"//svg[@aria-label='Home']")))
            print("✅ Logged in")
            return True
        except TimeoutException:
            print(f"Timeout {i}, retrying"); d.get(url); time.sleep(3)
        except WebDriverException as e:
            print("Crash, restart", e); return False
    print("❌ Login failed"); return False

def main():
    subprocess.run(["pkill","-f","chrome"],check=False); time.sleep(1)
    d = build_driver(); wait = WebDriverWait(d,15)
    # try login twice
    for _ in range(2):
        if login(d,wait): break
        d.quit(); d=build_driver(); wait=WebDriverWait(d,15)
    else:
        print("Could not login"); return

    # Dismiss overlays
    try: wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Not Now']"))).click()
    except: pass

    # Post loop
    for post in POSTS:
        print("Posting at",post["time"])
        wait_until(post["time"])
        inp=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"input[type='file']")))
        inp.send_keys(post["image"]); time.sleep(2)
        for _ in range(2):
            wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Next']"))).click()
            time.sleep(2)
        wait.until(EC.presence_of_element_located((By.XPATH,"//textarea[@aria-label='Write a caption…']"))) \
            .send_keys(post["caption"]); time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH,"//button[normalize-space()='Share']"))).click()
        print("✅ Shared"); time.sleep(10)
        d.refresh(); time.sleep(3)

    d.quit()

if __name__=="__main__":
    main()
