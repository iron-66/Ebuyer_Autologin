from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
import os

load_dotenv()
username = os.getenv("SAINSBURYS_USERNAME")
password = os.getenv("SAINSBURYS_PASSWORD")

output_folder = "order_details"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def login():
    driver = webdriver.Chrome()

    try:
        driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
        time.sleep(3)

        wait = WebDriverWait(driver, 10)
        cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all']")))
        cookies_button.click()
        time.sleep(1)

        driver.find_element(By.LINK_TEXT, "Log in / Register").click()
        time.sleep(1)

        cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all cookies']")))
        cookies_button.click()
        time.sleep(1)

        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(2)
        print("Login successful")

        driver.find_element(By.ID, "account-link").click()
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "See all orders").click()
        time.sleep(2)

        return driver
    except Exception as e:
        driver.quit()
        raise RuntimeError(f"Error during login: {e}")


def process_orders(driver):
    order_index = 0
    while True:
        try:
            orders = driver.find_elements(By.CSS_SELECTOR, ".order__controls-button")
            if order_index >= len(orders):
                print("All orders have been saved")
                break

            print(f"Processing order {order_index + 1}...")
            orders[order_index].click()
            time.sleep(2)

            save_order_details(driver, order_index)
            driver.back()
            order_index += 1
            time.sleep(2)
        except Exception as e:
            print(f"Error processing order {order_index + 1}: {e}")
            break


def save_order_details(driver, order_index):
    try:
        order_details = driver.find_elements(By.CLASS_NAME, "ln-c-card.order-details__card")
        file_path = os.path.join(output_folder, f"order_{order_index + 1}.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            for detail in order_details:
                file.write(detail.text + "\n\n")
        print(f"Order {order_index + 1} saved")
    except Exception as save_error:
        print(f"Error saving order data {order_index + 1}: {save_error}")


def main():
    try:
        driver = login()
        process_orders(driver)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
