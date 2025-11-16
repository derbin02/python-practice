from playwright.sync_api import sync_playwright
import time
from pathlib import Path

OUT = Path(".").absolute()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    try:
        print("-> Opening google.com ...")
        page.goto("https://google.com", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1200)

        # save before screenshot
        page.screenshot(path=str(OUT / "google_before.png"), full_page=True)
        print("-> Saved google_before.png")

        # 1) press Escape (many popups close with Esc)
        try:
            print("-> Pressing Escape to close overlays (if any)...")
            page.keyboard.press("Escape")
            page.wait_for_timeout(600)
        except Exception as e:
            print("   Escape error:", e)

        # 2) try clicking popup action buttons by visible text (common on your screenshot)
        candidates = ["Not interested", "Try it", "Not now", "No thanks", "Not interested."]
        clicked = False
        for txt in candidates:
            try:
                loc = page.locator(f"text=\"{txt}\"")
                if loc.count() > 0:
                    print(f"-> Found button with text '{txt}', clicking it.")
                    loc.first.click(timeout=3000)
                    page.wait_for_timeout(600)
                    clicked = True
                    break
            except Exception as e:
                print("   candidate click error for", txt, e)

        # 3) try to find generic close button inside dialogs or promos
        if not clicked:
            try:
                # search many possible close selectors
                close_selectors = [
                    "button[aria-label='Close']",
                    "button[aria-label='Dismiss']",
                    "button[title='Close']",
                    "button:has-text('Close')",
                    "button:has-text('Dismiss')",
                    "div[role='dialog'] button"
                ]
                for sel in close_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            print("-> Clicking close selector:", sel)
                            page.locator(sel).first.click(timeout=3000)
                            page.wait_for_timeout(600)
                            clicked = True
                            break
                    except Exception:
                        pass
            except Exception as e:
                print("   generic close search error:", e)

        # 4) If still not dismissed, remove likely promo DOM elements with JS (last resort)
        if not clicked:
            print("-> Attempting JS removal of popup elements (last resort).")
            js = r"""
            (() => {
                // try remove elements by checking bottom-right popups commonly added by Chrome
                const candidates = Array.from(document.querySelectorAll('div,section'));
                let removed = 0;
                candidates.forEach(el => {
                    const s = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    // element likely popup if fixed position and at bottom-right
                    if (s.position === 'fixed' && rect.right > (window.innerWidth - 300) && rect.bottom > (window.innerHeight - 200)) {
                        el.remove();
                        removed++;
                    }
                });
                return removed;
            })();
            """
            try:
                removed = page.evaluate(js)
                print(f"-> JS removal removed {removed} elements.")
                page.wait_for_timeout(500)
            except Exception as e:
                print("   JS removal error:", e)

        # final safety wait and screenshot
        page.screenshot(path=str(OUT / "google_after_popup_attempt.png"), full_page=True)
        print("-> Saved google_after_popup_attempt.png")

        # ensure search input exists and is visible
        page.wait_for_selector("input[name='q']", timeout=10000)
        print("-> Search box visible. Focusing and filling now.")

        # click + fill + press enter (these three together are reliable)
        page.click("input[name='q']")
        page.fill("input[name='q']", "Derbin is learning Playwright - popup fixed")
        page.keyboard.press("Enter")

        # wait to see results
        page.wait_for_timeout(3000)
        page.screenshot(path=str(OUT / "google_final.png"), full_page=True)
        print("-> Saved google_final.png - check it for proof.")

    except Exception as err:
        print("-> Script error:", err)
        try:
            page.screenshot(path=str(OUT / "google_error.png"), full_page=True)
            print("-> Saved google_error.png")
        except:
            pass
        raise
    finally:
        browser.close()
