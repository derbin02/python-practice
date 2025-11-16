from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://google.com")

    page.fill("input[name='q']", "Derbin is learning Playwright")
    page.keyboard.press("Enter")

    page.wait_for_timeout(3000)
    browser.close()
