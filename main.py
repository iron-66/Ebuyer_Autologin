from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
import os

load_dotenv()
USERNAME = os.getenv("SAINSBURYS_USERNAME")
PASSWORD = os.getenv("SAINSBURYS_PASSWORD")
driver = webdriver.Chrome()
output_folder = "order_details"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

try:
    driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
    time.sleep(3)

    wait = WebDriverWait(driver, 10)
    cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all']")))
    cookies_button.click()
    time.sleep(1)

    sign_in_button = driver.find_element(By.LINK_TEXT, "Log in / Register")
    sign_in_button.click()
    time.sleep(1)

    wait = WebDriverWait(driver, 10)
    cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all cookies']")))
    cookies_button.click()
    time.sleep(1)

    email_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")

    email_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)

    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    time.sleep(2)

    print("Login successful")

    account_button = driver.find_element(By.ID, "account-link")
    account_button.click()
    time.sleep(2)

    see_orders_button = driver.find_element(By.LINK_TEXT, "See all orders")
    see_orders_button.click()
    time.sleep(2)

    order_index = 0

    while True:
        try:
            orders = driver.find_elements(By.CSS_SELECTOR, ".order__controls-button")
            if order_index >= len(orders):
                print("All orders have been processed")
                break

            print(f"Order processing {order_index + 1}...")
            orders[order_index].click()
            time.sleep(2)

            try:
                order_details = driver.find_elements(By.CLASS_NAME, "ln-c-card.order-details__card")
                file_path = os.path.join(output_folder, f"order_{order_index + 1}.txt")
                with open(file_path, "w", encoding="utf-8") as file:
                    for detail in order_details:
                        file.write(detail.text + "\n\n")
                print(f"Order {order_index + 1} saved")
            except Exception as save_error:
                print(f"Error saving order data {order_index + 1}: {save_error}")

            driver.back()
            order_index += 1
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")


except Exception as e:
    print(f"Error: {e}")

finally:
    driver.quit()
