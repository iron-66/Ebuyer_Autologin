from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import undetected_chromedriver as uc
import time
import os

load_dotenv()
username = os.getenv("SAINSBURYS_USERNAME")
password = os.getenv("SAINSBURYS_PASSWORD")

class ProductList(BaseModel):
    urls: List[str]

app = FastAPI(
    title="Sainsburys Bot API",
    description="Automate adding items to cart and selecting a delivery slot",
    version="1.0.0",
)


@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    """
    Middleware that adds a custom header to all incoming requests

    Args:
        request (Request): The incoming HTTP request
        call_next (Callable): The next handler in the middleware chain

    Returns:
        Response: The HTTP response with added headers
    """
    headers = dict(request.headers)
    headers["bypass-tunnel-reminder"] = "1"
    response = await call_next(request)
    return response


def login(driver):
    """
    Logs in to the Sainsbury's website using credentials from environment variables

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance

    Raises:
        RuntimeError: If any step of the login process fails
    """
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
    """
    Adds products to the shopping cart by visiting its URL

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
        url (str): Product page URL
    """
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
    """
    Navigates to the cart page and proceeds to the checkout step
    Handles selection of home delivery slot if required

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
    """
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
            home_delivery_button = all_buttons[1]

            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", home_delivery_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", home_delivery_button)
                print("Proceed to selecting a delivery slot")
                time.sleep(5)
                select_delivery_slot(driver)
            except Exception:
                print("Slot already booked")
        else:
            print("Slot already booked")
    except Exception as e:
        print(f"Error searching for home delivery button: {e}")


def handle_redirects(driver):
    """
    Handles intermediate redirect pages during checkout.
    For example: forgotten favourites, before-you-go, summary, payment

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
    """
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
    """
    Finds and clicks the main 'Continue' button on a page

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
        wait (WebDriverWait): Selenium WebDriverWait object
    """
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
    """
    Searches for the first available delivery slot and confirms it

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
    """
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


def process_order(product_urls: list[str]):
    """
    Executes the full flow: logs in, adds products to the cart, checks out,
    and selects a delivery slot

    Args:
        product_urls (list[str]): List of Sainsbury's product URLs to add to the cart
    """
    options = uc.ChromeOptions()
    # options.add_argument("--headless=new")  # UI
    driver = uc.Chrome(options=options)

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


@app.post("/order")
def create_order(data: ProductList):
    """
    FastAPI endpoint to create an order based on incoming product URLs

    Args:
        data (ProductList): JSON body with a list of product URLs

    Returns:
        dict: Confirmation with list of processed URLs
    """
    if not data.urls:
        raise HTTPException(status_code=400, detail="No product URLs provided.")

    process_order(data.urls)
    print("Returning 200 OK (script completed successfully).")
    return {"status": "OK", "added": data.urls}
