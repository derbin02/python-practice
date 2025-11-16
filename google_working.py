from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://google.com", wait_until="networkidle")

    # Wait until search box appears
    page.wait_for_selector("input[name='q']", timeout=15000)

    # Click the search box (important: gives focus)
    page.click("input[name='q']")

    # Type your search
    page.fill("input[name='q']", "Derbin is learning Playwright")

    # Press Enter
    page.keyboard.press("Enter")

    # Wait 3 seconds to see results
    page.wait_for_timeout(3000)

    browser.close()
