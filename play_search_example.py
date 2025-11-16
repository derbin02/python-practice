# play_search_example.py
from playwright.sync_api import sync_playwright
from pathlib import Path
import time, traceback

OUT = Path(".").absolute()

def save_debug(page, name="debug"):
    try:
        page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
        (OUT / f"{name}.html").write_text(page.content(), encoding="utf-8")
        print("Saved debug files:", name + ".png", name + ".html")
    except Exception as e:
        print("Could not save debug files:", e)

def run_search(query="playwright tutorial"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)   # headless=False while developing
        page = browser.new_page()
        try:
            print("Opening DuckDuckGo...")
            page.goto("https://duckduckgo.com", wait_until="networkidle", timeout=20000)

            # wait for search input to appear
            page.wait_for_selector("input[name='q']", timeout=10000)
            print("Search input visible — filling query:", query)

            # focus (click) then fill (two-step is more reliable)
            page.click("input[name='q']")
            page.fill("input[name='q']", query)

            # press Enter to search
            page.keyboard.press("Enter")

            # wait for results container - this selector is stable for DuckDuckGo
            page.wait_for_selector("#links .result", timeout=10000)
            print("Search results loaded.")

            # take a screenshot of results page
            page.screenshot(path=str(OUT / "search_results.png"), full_page=True)
            print("Saved search_results.png")

            # click the first search result (use locator().first)
            first = page.locator("#links .result").first
            title = first.locator("h2").inner_text() if first.locator("h2").count() else "<no-title>"
            print("Clicking first result:", title.strip()[:120])
            first.click()

            # wait for navigation or new content (short wait)
            page.wait_for_timeout(3000)

            # capture final screenshot of the opened page
            page.screenshot(path=str(OUT / "first_result_opened.png"), full_page=True)
            print("Saved first_result_opened.png")

            # try to read some text from the opened page (if available)
            body_preview = page.locator("body").inner_text()[:800]
            print("\n--- Page preview (first 800 chars) ---\n")
            print(body_preview)
            print("\n--- end preview ---\n")

            print("Search automation finished successfully.")

        except Exception as err:
            print("ERROR during search automation:", err)
            traceback.print_exc()
            # save debug files to help you and your tutor see the problem
            save_debug(page, "search_error_debug")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    run_search("Derbin is learning Playwright")
