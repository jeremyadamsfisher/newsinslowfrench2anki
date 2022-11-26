import csv
import time
from tempfile import NamedTemporaryFile
from typing import List, Tuple

from playwright.sync_api import sync_playwright

from newsinslowfrenchdaemon.config import settings

VocabList = List[Tuple[str, str]]

NISF_BASE_URL = "https://www.newsinslowfrench.com"
NISF_HOMEPAGE_URL = f"{NISF_BASE_URL}/french-podcast"
NISF_NEWSPAGE_URL = f"{NISF_BASE_URL}/home/news/intermediate"
ANKI_LOGIN_URL = "https://ankiweb.net/account/login"
ANKI_EDIT_URL = "https://ankiuser.net/edit/"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        vocab = get_most_recent_vocab(page)
        add_vocab_to_anki(page, vocab)
        browser.close()


def get_most_recent_vocab(page) -> VocabList:

    # Log in to News In Slow French
    page.goto(NISF_HOMEPAGE_URL)
    page.locator("a.signin").click()
    page.locator(".login-username").fill(settings.nisf.username)
    page.locator(".login-password").fill(settings.nisf.password)
    page.get_by_role("button", name="Login").click()

    # Find the most recent episode
    page.goto(NISF_NEWSPAGE_URL)
    most_recent_episode_link = page.locator('css=.episode a[tabindex="0"]')
    page.goto(NISF_BASE_URL + most_recent_episode_link.get_attribute("href"))

    # Download the vocab CSV
    page.get_by_role("checkbox", name="Flashcard").check()
    with page.expect_download() as download_info:
        page.get_by_text("CSV").click()
    download = download_info.value
    download.path()  # wait for download completion

    # Extract the vocab from the annoyingly formatted CSV
    vocab = []
    with NamedTemporaryFile(suffix=".csv") as t:
        download.save_as(t.name)
        t.seek(0)
        reader = csv.reader(t)
        for line in reader:
            if len(line) != 2:
                continue
            french, english = line
            vocab.append((french, english))

    return vocab


def add_vocab_to_anki(page, vocab: VocabList):

    # Log in to Anki
    page.goto(ANKI_LOGIN_URL)
    page.get_by_label("Email").fill(settings.anki.username)
    page.get_by_label("Password").fill(settings.anki.password)
    page.get_by_role("button", name="Log in").click()

    # Add each as a card with one language on either side
    page.goto(ANKI_EDIT_URL)
    for french, english in vocab:
        page.get_by_label("Type").select_option("1")  # 1 = Basic (and reversed card)
        page.locator("#f0").fill(french)  # Front
        page.locator("#f1").fill(english)  # Back
        page.get_by_role("button", name="Save").click()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
