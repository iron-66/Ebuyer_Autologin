import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By

load_dotenv()
USERNAME = os.getenv("WP_USERNAME")
PASSWORD = os.getenv("WP_PASSWORD")
LOGIN_URL = "https://fastfounder.ru/wp-login.php"
NEWS_URL = "https://fastfounder.ru/news/page/{}/"
ARTICLES_DIR = "articles"

os.makedirs(ARTICLES_DIR, exist_ok=True)
driver = webdriver.Chrome()


def login():
    driver.get(LOGIN_URL)
    time.sleep(2)
    driver.find_element(By.ID, "user_login").send_keys(USERNAME)
    driver.find_element(By.ID, "user_pass").send_keys(PASSWORD)
    driver.find_element(By.ID, "wp-submit").click()
    time.sleep(3)


def get_articles():
    time.sleep(1)
    return driver.find_elements(By.CLASS_NAME, "wp-post-image")


def save_article(index):
    time.sleep(1)
    paragraphs = driver.find_elements(By.TAG_NAME, "p")
    content = "\n".join([p.text for p in paragraphs if p.text.strip()])

    filename = os.path.join(ARTICLES_DIR, f"article_{index}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filename}")

    driver.back()
    time.sleep(1)


def go_to_next_page(page_number):
    next_page_url = NEWS_URL.format(page_number)
    driver.get(next_page_url)
    time.sleep(1)


def main():
    login()

    total_pages = 234
    articles_per_page = 7

    for page in range(1, total_pages + 1):
        print(f"Processing page {page}/{total_pages}")
        go_to_next_page(page)

        for i in range(articles_per_page):
            try:
                articles = get_articles()
                article = articles[i]
                article.click()
                save_article((page - 1) * articles_per_page + (i + 1))
            except Exception as e:
                print(f"Ошибка при обработке статьи {i + 1} на странице {page}: {e}")

    driver.quit()
    print("All articles saved.")


if __name__ == "__main__":
    main()