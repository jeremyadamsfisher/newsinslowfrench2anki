from playwright.sync_api import sync_playwright

HOMEPAGE_URL = "https://www.newsinslowfrench.com/home/news/intermediate"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(HOMEPAGE_URL)
        page.locator("a.signin").click()
        page.screenshot(path="example.png")
        browser.close()


if __name__ == "__main__":
    main()
