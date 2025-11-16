# play_template.py
from playwright.sync_api import sync_playwright
from pathlib import Path
import time, traceback

# config
HEADLESS = False
OUT = Path(".").absolute()

def save_debug(page, name_prefix="debug"):
    try:
        shot = OUT / f"{name_prefix}.png"
        page.screenshot(path=str(shot), full_page=True)
        html = OUT / f"{name_prefix}.html"
        html.write_text(page.content(), encoding="utf-8")
        print("Saved:", shot, html)
    except Exception as e:
        print("Failed to save debug:", e)

def run_task():
    html = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()
        try:
            # ---------- TASK STEPS ----------
            # 1) Open page
            page.goto("https://example.com/login", wait_until="networkidle")
            page.wait_for_selector("input[name='username']", timeout=10000)

            # 2) Fill login
            page.fill("input[name='username']", "your_user")
            page.fill("input[name='password']", "your_pass")
            page.click("button[type='submit']")

            # 3) Wait for next page element to confirm success
            page.wait_for_selector("#profileHeader", timeout=10000)

            # 4) Fill a profile form example
            page.fill("#fullname", "Derbin")
            page.select_option("#age", value="26-35")
            page.check("#newsletter")
            page.click("#submitBtn")

            # 5) Wait for result and screenshot
            page.wait_for_selector("#result", timeout=10000)
            page.screenshot(path=str(OUT/"final_result.png"), full_page=True)
            print("Done. Saved final_result.png")

            # ---------- TASK STEPS END ----------
        except Exception as err:
            print("ERROR:", err)
            traceback.print_exc()
            save_debug(page, "error_debug")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    run_task()
