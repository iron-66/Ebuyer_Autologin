from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import openai
import time
import os
import uuid
import re

load_dotenv()
username = os.getenv("SAINSBURYS_USERNAME")
password = os.getenv("SAINSBURYS_PASSWORD")
openai_api_key = os.getenv("OPENAI_API_KEY")


def get_user_uuid(username):
    """
    Returns a unique UUID for the given username.
    If not found, generates and stores a new one

    Args:
        username (str): User email or ID

    Returns:
        str: UUID associated with the user
    """
    uuid_file = "user_uuids.txt"

    if os.path.exists(uuid_file):
        with open(uuid_file, "r", encoding="utf-8") as file:
            for line in file:
                saved_email, saved_uuid = line.strip().split(":")
                if saved_email == username:
                    return saved_uuid
    new_uuid = str(uuid.uuid4())
    with open(uuid_file, "a", encoding="utf-8") as file:
        file.write(f"{username}:{new_uuid}\n")
    return new_uuid


user_uuid = get_user_uuid(username)
user_folder = os.path.join("users", user_uuid)
os.makedirs(user_folder, exist_ok=True)
orders_file = os.path.join(user_folder, "orders.txt")
plan_file = os.path.join(user_folder, "purchase_plan.txt")


def login():
    """
    Logs into the Sainsbury's website using provided credentials

    Returns:
        webdriver.Chrome: Logged-in Selenium driver instance
    """
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
        time.sleep(3)
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
    """
    Iterates through available orders, saves new ones,
    and skips existing ones

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
    """
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

            result, order_data = save_order_details(driver)

            if result == "exists":
                print(f"Order {order_index + 1} already exists, stopping further processing")
                break

            if result == "saved":
                update_orders_file(order_data)
        except Exception as e:
            print(f"Error processing order {order_index + 1}: {e}")
            order_index += 1
            continue
        driver.back()
        order_index += 1
        time.sleep(3)


def save_order_details(driver):
    """
    Extracts and saves order information from the current page

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance

    Returns:
        tuple: ('saved' or 'exists' or 'error', order data or None)
    """
    try:
        order_url = driver.current_url
        match = re.search(r"/orders/(\d+)", order_url)

        if not match:
            print(f"Could not extract order number from URL: {order_url}")
            return "error", None

        order_number = match.group(1)
        file_path = os.path.join(user_folder, f"order_{order_number}.txt")

        if os.path.exists(file_path):
            return "exists", None

        order_details = driver.find_elements(By.CLASS_NAME, "ln-c-card.order-details__card")
        order_data = f"Order {order_number}:\n"
        order_data += "\n".join([detail.text for detail in order_details]) + "\n\n"

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(order_data)

        print(f"Order {order_number} saved")
        return "saved", order_data
    except Exception as save_error:
        print(f"Error saving order data: {save_error}")
        return "error", None


def update_orders_file(order_data):
    """
    Prepends newly saved order data to orders.txt file

    Args:
        order_data (str): Raw order text
    """
    try:
        if os.path.exists(orders_file):
            with open(orders_file, "r", encoding="utf-8") as file:
                existing_data = file.read()
        else:
            existing_data = ""

        with open(orders_file, "w", encoding="utf-8") as file:
            file.write(order_data + existing_data)

        print("Updated orders.txt successfully")
    except Exception as e:
        print(f"Error updating orders.txt: {e}")


def analyze_purchases():
    """
    Analyzes user's order history and generates a 6-month shopping plan using GPT.
    """
    if not os.path.exists(orders_file):
        print("No orders.txt file found, skipping analysis.")
        return

    try:
        with open(orders_file, "r", encoding="utf-8") as file:
            orders_data = file.read()

        prompt_text = (
            "Вот список покупок из прошлых заказов:\n\n"
            f"{orders_data}\n\n"
            "На основе этой информации составь план покупок на 6 месяцев, учитывая возможные тенденции и периодичность повторяющихся покупок."
        )

        client = openai.OpenAI(api_key=openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.7
        )

        plan = response.choices[0].message.content

        with open(plan_file, "w", encoding="utf-8") as file:
            file.write(plan)

        print("Purchase plan saved successfully.")
    except Exception as e:
        print(f"Error analyzing purchases: {e}")


def main():
    """
    Main function to run the login, order extraction, and optionally analysis
    """
    try:
        driver = login()
        process_orders(driver)
        #analyze_purchases()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
