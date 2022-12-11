import csv
import subprocess
import time
from tempfile import NamedTemporaryFile
from typing import List, Tuple

import genanki
from anki.collection import Collection
from anki.importing import TextImporter
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
        browser = p.chromium.launch(headless=settings.web_scraping.headless)
        page = browser.new_page()
        vocab = get_most_recent_vocab(page)
        add_vocab_to_anki(vocab)
        browser.close()


def get_most_recent_vocab(page) -> VocabList:

    # Log in to News In Slow French
    page.goto(NISF_HOMEPAGE_URL)
    page.locator("a.signin").click()
    page.locator(".login-username").fill(settings.nisf.username)
    page.locator(".login-password").fill(settings.nisf.password)
    page.get_by_role("button", name="Login").click()

    # Find the most recent episode
    time.sleep(5)  # avoid concurrent navigation
    page.goto(NISF_NEWSPAGE_URL)
    most_recent_episode_link = page.locator('css=.episode a[tabindex="0"]')
    time.sleep(5)  # avoid concurrent navigation
    page.goto(NISF_BASE_URL + most_recent_episode_link.get_attribute("href"))

    # Download the vocab CSV
    page.get_by_role("checkbox", name="Flashcard").check()
    with page.expect_download() as download_info:
        page.get_by_text("CSV").click()
    download = download_info.value
    download.path()  # wait for download completion

    # Extract the vocab from the annoyingly formatted CSV
    vocab = []
    with NamedTemporaryFile(suffix=".csv", mode="wt+") as t:
        download.save_as(t.name)
        t.seek(0)
        reader = csv.reader(t)
        for line in reader:
            if len(line) != 2:
                continue
            french, english = line
            vocab.append((french, english))

    return vocab


def add_vocab_to_anki(vocab: VocabList):
    col = Collection(settings.anki.collection_fp)
    try:
        deck_id = col.decks.id(settings.anki.deck_name)
    finally:
        col.close()
    deck = genanki.Deck(deck_id, settings.anki.deck_name)
    print(f"Adding {len(vocab)} cards...")
    for french, english in vocab:
        note = genanki.Note(
            model=genanki.BASIC_AND_REVERSED_CARD_MODEL,
            fields=[french, english],
        )
        deck.add_note(note)
    with NamedTemporaryFile(suffix=".apkg") as t:
        genanki.Package(deck).write_to_file(t.name)
        t.seek(0)
        subprocess.check_call(["open", t.name])
        time.sleep(15)  # wait for anki to import, then quit


if __name__ == "__main__":
    main()
