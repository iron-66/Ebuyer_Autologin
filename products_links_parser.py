from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Файл для сохранения ссылок
output_file = "products_links.txt"
input_file = "initial_urls.txt"  # Файл со ссылками

def accept_cookies(driver):
    """ Принимает Cookies только один раз при запуске """
    wait = WebDriverWait(driver, 10)
    try:
        cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all']")))
        cookies_button.click()
        time.sleep(2)
        print("Cookies приняты.")
    except:
        print("Cookies уже приняты или не требуются.")

def get_links_from_page(driver, url):
    """ Переходит по ссылке и собирает все href с классом pt__link """
    driver.get(url)
    time.sleep(2)

    try:
        # Поиск всех ссылок с классом pt__link
        links = driver.find_elements(By.CSS_SELECTOR, "a.pt__link")
        hrefs = [link.get_attribute("href") for link in links if link.get_attribute("href")]

        # Удаление дубликатов на странице
        hrefs = list(set(hrefs))
        return hrefs

    except Exception as e:
        print(f"Ошибка при парсинге ссылок на странице {url}: {e}")
        return []

def save_links(hrefs):
    # Проверка и создание файла
    if not os.path.exists(output_file):
        with open(output_file, "w", encoding="utf-8") as file:
            pass

    # Чтение уже сохранённых ссылок
    with open(output_file, "r", encoding="utf-8") as file:
        existing_links = file.read().splitlines()

    # Проверка на дубли
    new_links = []
    duplicate_links = []

    for link in hrefs:
        if link not in existing_links:
            new_links.append(link)
        else:
            duplicate_links.append(link)

    # Сохранение новых ссылок в файл
    if new_links:
        with open(output_file, "a", encoding="utf-8") as file:
            for link in new_links:
                file.write(link + "\n")

        print(f"Добавлено {len(new_links)} новых ссылок.")
    else:
        print("Новых ссылок нет.")

    # Сообщение о дублирующихся ссылках
    if duplicate_links:
        print(f"Найдено {len(duplicate_links)} дублирующихся ссылок, они не добавлены:")
        for dup in duplicate_links:
            print(f" - {dup}")

def main():
    # Проверяем наличие файла со ссылками
    if not os.path.exists(input_file):
        print(f"Файл {input_file} не найден. Создайте файл и добавьте ссылки по одной на строку.")
        return

    # Чтение ссылок из файла
    with open(input_file, "r", encoding="utf-8") as file:
        urls = file.read().splitlines()

    if not urls:
        print(f"Файл {input_file} пуст. Добавьте ссылки и повторите запуск.")
        return

    # Запуск браузера
    driver = webdriver.Chrome()

    try:
        # Переходим по первой ссылке и принимаем Cookies
        driver.get(urls[0])
        accept_cookies(driver)

        # Переход по всем ссылкам из файла
        for url in urls:
            print(f"\nПарсинг страницы: {url}")
            hrefs = get_links_from_page(driver, url)
            save_links(hrefs)

    except Exception as e:
        print(f"Ошибка при обработке: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
