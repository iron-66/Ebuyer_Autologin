from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import time
import os


# --------------------------------
# 1. Load environment variables
# --------------------------------
load_dotenv()
username = os.getenv("SAINSBURYS_USERNAME")
password = os.getenv("SAINSBURYS_PASSWORD")


# --------------------------------
# 2. Pydantic model for input data
# --------------------------------
class ProductList(BaseModel):
    urls: List[str]


# --------------------------------
# 3. Initialize FastAPI
# --------------------------------
app = FastAPI(
    title="Sainsburys Bot API",
    description="Automate adding items to cart and selecting a delivery slot",
    version="1.0.0",
)


# --------------------------------
# 4. Middleware for adding a header
# --------------------------------
@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    headers = dict(request.headers)
    headers["bypass-tunnel-reminder"] = "1"
    response = await call_next(request)

    return response


# --------------------------------
# 5. Core functions (login, add_to_cart, etc.)
# --------------------------------
def login(driver):
    try:
        driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
        time.sleep(3)
        print("Page loaded")

        wait = WebDriverWait(driver, 10)
        cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all']")))
        cookies_button.click()
        time.sleep(1)
        print("Cookies accepted")

        driver.find_element(By.LINK_TEXT, "Log in / Register").click()
        time.sleep(1)
        print("Button founded")

        cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all cookies']")))
        cookies_button.click()
        time.sleep(1)
        print("Button clicked")

        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)
        print("Login successful")

    except Exception as e:
        driver.quit()
        raise RuntimeError(f"Error during login: {e}")


def add_to_cart(driver, url):
    wait = WebDriverWait(driver, 10)
    driver.get(url)
    try:
        add_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".ln-c-button.ln-c-button--filled.ln-c-button--full.pt__add-button--reduced-height")
        ))
        add_button.click()
        print(f"Item from {url} added to cart")
    except Exception as e:
        print(f"Error adding item from {url}: {e}")


def proceed_to_checkout(driver):
    wait = WebDriverWait(driver, 10)
    driver.get("https://www.sainsburys.co.uk/gol-ui/trolley")
    time.sleep(2)

    try:
        checkout_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".ln-c-button.ln-c-button--filled.trolley__cta-button")
        ))
        checkout_button.click()
        print("Cart is complete")
    except Exception as e:
        print(f"Error proceeding to checkout: {e}")

    try:
        all_buttons = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".ln-c-button.ln-c-button--filled")
        ))
        time.sleep(2)

        if len(all_buttons) > 1:
            second_button = all_buttons[1]
            driver.execute_script("arguments[0].scrollIntoView(true);", second_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", second_button)
            print("Proceed to selecting a delivery slot")
            time.sleep(5)
            select_delivery_slot(driver)
        else:
            print("Slot already booked")
    except Exception as e:
        print(f"Error clicking on the second button: {e}")


def handle_redirects(driver):
    wait = WebDriverWait(driver, 10)
    for _ in range(5):
        current_url = driver.current_url.lower()
        if "before-you-go" in current_url:
            print("We are on the 'before you go' page")
            click_continue_button(driver, wait)
            time.sleep(2)
            continue
        elif "forgotten-favourites" in current_url:
            print("We are on the 'forgotten favourites' page")
            click_continue_button(driver, wait)
            time.sleep(2)
            continue
        elif "summary" in current_url:
            print("We are on the summary page")
            click_continue_button(driver, wait)
            time.sleep(2)
            print("Confirmation successful")
            continue
        elif "payment" in current_url:
            print("We are on the payment page")
            while True:
                time.sleep(2)
                new_url = driver.current_url.lower()
                if "payment" not in new_url:
                    print(f"Payment finished. URL changed to {new_url}")
                    break
            continue
        else:
            print("No more known redirects:", current_url)
            break


def click_continue_button(driver, wait):
    try:
        cta_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ln-c-button.ln-c-button--filled.trolley__cta-button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", cta_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", cta_button)
        print("Continue button clicked successfully.")
        time.sleep(2)
    except Exception as e:
        print(f"Error clicking continue button: {e}")


def select_delivery_slot(driver):
    wait = WebDriverWait(driver, 15)
    try:
        table = wait.until(EC.presence_of_element_located((By.ID, "slot-table")))
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if not tds:
                continue
            for cell in tds:
                try:
                    button = cell.find_element(By.CSS_SELECTOR, "button.book-slot-grid__slot")
                except:
                    continue
                if "book-slot-grid__slot-full" in button.get_attribute("class"):
                    continue
                if "Unavailable" in button.text:
                    continue
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", button)
                print("First available slot selected.")
                time.sleep(2)
                try:
                    confirm_btn = wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        ".ln-c-button.ln-c-button--filled.ln-c-button--full.reserve-slot-modal__primary-button"
                    )))
                    driver.execute_script("arguments[0].scrollIntoView(true);", confirm_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", confirm_btn)
                    print("Slot reservation confirmed.")
                except Exception as e:
                    print(f"Error confirming slot reservation: {e}")
                time.sleep(2)
                try:
                    secondary_btn = wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        ".ds-c-button.ds-c-button--secondary.ds-c-button--md.booking-confirmation__button"
                    )))
                    driver.execute_script("arguments[0].scrollIntoView(true);", secondary_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", secondary_btn)
                    print("Clicked the booking confirmation secondary button.")
                except Exception as e:
                    print(f"Error clicking booking confirmation button: {e}")
                time.sleep(2)
                try:
                    final_cta_btn = wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        ".ln-c-button.ln-c-button--filled.trolley__cta-button"
                    )))
                    driver.execute_script("arguments[0].scrollIntoView(true);", final_cta_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", final_cta_btn)
                    print("Clicked the final trolley CTA button.")
                except Exception as e:
                    print(f"Error clicking final CTA button: {e}")
                return
        print("No available slots found.")
    except Exception as e:
        current_url = driver.current_url.lower()
        if "summary" in current_url:
            print("Already on the summary page, no slot selection needed.")
        else:
            print(f"Error selecting a delivery slot: {e}")


# --------------------------------
# 6. Function to process an order
# --------------------------------
def process_order(product_urls: list[str]):
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36"
    })

    try:
        print("Script started")
        login(driver)
        for url in product_urls:
            print(f"\nAdding to cart: {url}")
            add_to_cart(driver, url)
            time.sleep(2)
        proceed_to_checkout(driver)
        handle_redirects(driver)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()


# --------------------------------
# 7. FastAPI endpoint to receive a list of products
# --------------------------------
@app.post("/order")
def create_order(data: ProductList, request: Request):
    headers = dict(request.headers)
    print(f"Headers: {headers}")

    if not data.urls:
        raise HTTPException(status_code=400, detail="No product URLs provided.")

    process_order(data.urls)
    print("Returning 200 OK (script completed successfully).")
    return {"status": "OK", "added": data.urls}
