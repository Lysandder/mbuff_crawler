from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
import random
import time
from itertools import islice
import flask
import psycopg2
import subprocess
import sys

import os
from dotenv import load_dotenv
load_dotenv(".env")
PROFILE_URL = os.getenv("PROFILE_URL")
LOGIN_URL = os.getenv("LOGIN_URL")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
DECK_URL = os.getenv("DECK_URL")
ADS_URL = os.getenv("ADS_URL")
SHOJOS_URL = os.getenv("SHOJOS_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

WORDS_LIST = ["Good", "Bad", "New", "Else"]

executors = {
    'default': ThreadPoolExecutor(max_workers=1)  # only 1 job runs at a time
}

app = flask.Flask(__name__)


@app.route("/")
def home():
    return "OK", 200


def connect_db():
    # if not DATABASE_URL:
    #     print("ERROR" * 10)
    #     print("Something is wrong with the DB URL");
    return psycopg2.connect(DATABASE_URL)


def install_chromium():
    print('=' * 100)
    print("Starting Installing Chromium...")
    subprocess.run(
        ["playwright", "install", "chromium"],
        check=True
    )
    subprocess.run(
        ["playwright", "install-deps", "chromium"],
        check=True
    )
    print("Finished Installing Chromium")
    print('=' * 100)


def get_index():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM state WHERE key = 'index'")
    index = cur.fetchone()[0]
    cur.close()
    conn.close()
    return index


def set_index(index):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE state SET value = %s WHERE key = 'index'", (index,))
    conn.commit()
    cur.close()
    conn.close()


def get_links(index):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT link FROM chapters
        WHERE id >= %s
        ORDER BY id
        LIMIT 4
    """, (index,))
    links = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return links


def cleanup(browser):
    for page in browser.pages:
        page.close()


def ensure_logged_in(page):
    page.goto(PROFILE_URL)

    if "login" in page.url.lower():
        page.goto(LOGIN_URL)
        time.sleep(random.randint(3, 7))
        page.fill(".form__field[type='email']", EMAIL)
        page.fill(".form__field[type='password']", PASSWORD)
        page.click(".login-button")
        page.wait_for_timeout(random.randint(5182, 7382))  # in ms


def read_chapter():  # 4 with a delay 2.5-3.5 minutes
    print('=' * 100)
    print("Reading chapters started")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./user_data", headless=True)

        cleanup(browser)
        page = browser.new_page()

        ensure_logged_in(page)

        # with open("index.txt", 'r') as file:
        #     index = int(file.readline().strip())
        #
        # with open("chapters.txt", 'r') as file:
        #     links = [line.strip()
        #              for line in islice(file, index - 1, index + 3)]

        index = get_index()
        links = get_links(index)

        completed = 0
        for link in links:
            try:
                page.goto(link)
                time.sleep(random.randint(1, 3))
                js_command = """
                    read_status_send = false; 
                    is_read = true; 
                    loadTime = new Date().getTime() - 11000; 
                    addHistory(); 
                    let items = JSON.parse(localStorage.getItem('history_pool')) || []; 
                    if (items.length > 0) { 
                        $.post("/addHistory?r=702", { items: items }, function (data) { 
                            localStorage.setItem('history_pool', JSON.stringify([]));
                            console.log('Batch sent to server:', data); 
                        });
                    }
                """
                page.evaluate(js_command)
                completed += 1
                if link != links[-1]:
                    time.sleep(random.randint(120, 180))

            except Exception:
                ensure_logged_in(page)

        # with open("index.txt", 'w') as file:
        #     file.write(f"{index}")
        set_index(index + completed)

        browser.close()
    print("Finished Reading chapters")
    print('=' * 100)


def leave_comment():  # 10 with a delay 10-30 seconds
    print('=' * 100)
    print("Leaving comments started")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./user_data", headless=True)

        cleanup(browser)
        page = browser.new_page()

        ensure_logged_in(page)

        page.goto(DECK_URL)
        time.sleep(random.randint(3, 7))
        page.click(".comments__send-form--mini")

        for _ in range(10):
            try:
                page.fill(".comments__send-form textarea",
                          "Something " + WORDS_LIST[random.randint(0, 3)])
                page.click(".comments__send-btn")

                delay = random.randint(10, 30)
                time.sleep(delay)
            except Exception:
                ensure_logged_in(page)

        browser.close()
    print("Finished Leaving comments")
    print('=' * 100)


def watch_ads():
    print('=' * 100)
    print("Watching ADS started")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./user_data", headless=True)

        cleanup(browser)
        page = browser.new_page()

        ensure_logged_in(page)

        page.goto(ADS_URL)
        time.sleep(random.randint(3, 7))

        for _ in range(3):
            try:
                page.click(".user-quest__watch-ads-btn")
                time.sleep(35)
                page.click("[data-fullscreen-element-name='close-btn']")
                time.sleep(random.randint(2, 4))
            except Exception:
                ensure_logged_in(page)

        browser.close()
    print("Finished Watching ADS")
    print('=' * 100)


# def scrape_names():
#     with sync_playwright() as p:
#         browser = p.chromium.launch_persistent_context(
#             user_data_dir="./user_data", headless=True)
#
#         cleanup(browser)
#         page = browser.new_page()
#
#         ensure_logged_in(page)
#
#         page.goto(SHOJOS_URL)
#         time.sleep(random.randint(3, 7))
#
#         next_page_button = page.locator(
#             "li.pagination__button a", has_text="Вперёд")
#
#         while (next_page_button.count() > 0):
#             names_links = page.eval_on_selector_all(
#                 "a.cards__item",
#                 "els => els.map(el => el.href)"
#             )
#             with open("names.txt", 'a') as file:
#                 for link in names_links:
#                     file.write(link + "\n")
#             next_page_button.click()
#             time.sleep(random.randint(2, 5))
#
#         browser.close()
#
#
# def scrape_chapters():
#     with sync_playwright() as p:
#         browser = p.chromium.launch_persistent_context(
#             user_data_dir="./user_data", headless=True)
#
#         cleanup(browser)
#         page = browser.new_page()
#
#         ensure_logged_in(page)
#
#         with open("names.txt", "r") as names_file:
#             for line in names_file:
#                 # for line in islice(names_file, 204, None):
#                 page.goto(line.strip())
#                 time.sleep(random.randint(1, 5))
#
#                 if page.is_disabled("button[data-page='chapters']"):
#                     print("=" * 100)
#                     print(line)
#                     print("=" * 100)
#                     continue
#                 page.click("button[data-page='chapters']")
#
#                 chapters_links = page.eval_on_selector_all(
#                     ".chapters__list a.chapters__item",
#                     "els => els.map(el => el.href)"
#                 )
#
#                 with open("chapters.txt", 'a') as file:
#                     for link in chapters_links:
#                         file.write(link + "\n")
#                 time.sleep(random.randint(1, 5))
#
#         browser.close()


# scrape_names()
# scrape_chapters()

install_chromium()

scheduler = BackgroundScheduler(timezone="Asia/Tashkent", executors=executors)
scheduler.add_job(read_chapter, 'interval', hours=1, next_run_time=datetime.now(), max_instances=1)
scheduler.add_job(leave_comment, 'cron', hour=3, minute=30, max_instances=1)
scheduler.add_job(watch_ads, 'cron', hour=2, minute=30, max_instances=1)
scheduler.start()

# if __name__ == "__main__":
port = int(os.environ.get("PORT", 3000))
app.run(host="0.0.0.0", port=port)
