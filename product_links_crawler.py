from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

input_file = "initial_urls.txt"
output_file = "products_links.txt"


def accept_cookies(driver):
    """
    Accepts cookies on the Sainsbury's website if the consent banner is shown
    """
    wait = WebDriverWait(driver, 10)
    try:
        cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all']")))
        cookies_button.click()
        time.sleep(2)
        print("Cookies accepted")
    except:
        print("Cookies already accepted or not required")


def get_links_from_page(driver, url):
    """
    Extracts all product links from the given page

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
        url (str): URL of the page to parse

    Returns:
        list[str]: Unique list of product URLs found on the page
    """
    driver.get(url)
    time.sleep(2)

    try:
        links = driver.find_elements(By.CSS_SELECTOR, "a.pt__link")
        hrefs = [link.get_attribute("href") for link in links if link.get_attribute("href")]
        hrefs = list(set(hrefs))
        return hrefs
    except Exception as e:
        print(f"Error parsing links from page {url}: {e}")
        return []


def save_links(hrefs):
    """
    Saves only new product links to the output file

    Args:
        hrefs (list[str]): List of extracted product links
    """
    if not os.path.exists(output_file):
        with open(output_file, "w", encoding="utf-8"):
            pass

    with open(output_file, "r", encoding="utf-8") as file:
        existing_links = file.read().splitlines()

    new_links = []
    duplicate_links = []

    for link in hrefs:
        if link not in existing_links:
            new_links.append(link)
        else:
            duplicate_links.append(link)

    if new_links:
        with open(output_file, "a", encoding="utf-8") as file:
            for link in new_links:
                file.write(link + "\n")
        print(f"Added {len(new_links)} new links")
    else:
        print("No new links found")

    if duplicate_links:
        print(f"{len(duplicate_links)} duplicate links skipped:")
        for dup in duplicate_links:
            print(f" - {dup}")


def main():
    """
    Main entry point, loads category URLs and processes each to collect product links
    """
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found")
        return

    with open(input_file, "r", encoding="utf-8") as file:
        urls = file.read().splitlines()

    if not urls:
        print(f"Input file '{input_file}' is empty")
        return

    driver = webdriver.Chrome()

    try:
        driver.get(urls[0])
        accept_cookies(driver)

        for url in urls:
            print(f"\nProcessing page: {url}")
            hrefs = get_links_from_page(driver, url)
            save_links(hrefs)
    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
