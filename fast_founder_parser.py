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
TOTAL_PAGES = 234
ARTICLES_PER_PAGE = 7

os.makedirs(ARTICLES_DIR, exist_ok=True)
driver = webdriver.Chrome()


def login():
    """
    Logs into the WordPress admin panel using provided credentials
    """
    driver.get(LOGIN_URL)
    time.sleep(2)
    driver.find_element(By.ID, "user_login").send_keys(USERNAME)
    driver.find_element(By.ID, "user_pass").send_keys(PASSWORD)
    driver.find_element(By.ID, "wp-submit").click()
    time.sleep(3)


def get_articles():
    """
    Retrieves all article preview elements on the page

    Returns:
        list: A list of WebElements representing article links
    """
    time.sleep(1)
    return driver.find_elements(By.CLASS_NAME, "wp-post-image")


def save_article(index):
    """
    Saves article content (paragraphs) into a .txt file

    Args:
        index (int): Global index of the article (for filename)
    """
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
    """
    Navigates to the specified news page

    Args:
        page_number (int): Page number in the news pagination
    """
    next_page_url = NEWS_URL.format(page_number)
    driver.get(next_page_url)
    time.sleep(1)


def main():
    """
    Main script logic: logs in, iterates over pages and articles,
    and saves article content to disk
    """
    login()

    for page in range(1, TOTAL_PAGES + 1):
        print(f"Processing page {page}/{TOTAL_PAGES}")
        go_to_next_page(page)

        for i in range(ARTICLES_PER_PAGE):
            try:
                articles = get_articles()
                article = articles[i]
                article.click()
                article_index = (page - 1) * ARTICLES_PER_PAGE + (i + 1)
                save_article(article_index)
            except Exception as e:
                print(f"Error on article {i + 1}, page {page}: {e}")

    driver.quit()
    print("All articles saved.")


if __name__ == "__main__":
    main()