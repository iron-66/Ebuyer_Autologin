import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def measure_page_load_time(url: str) -> float:
    """
    Measures how long it takes to fully load the specified URL using a headless Chrome browser

    Args:
        url (str): The web page URL to load

    Returns:
        float: Total load time in seconds
    """
    options = Options()
    options.add_argument("--log-level=3")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    #                                "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.5735.199 Safari/537.36"
        )
    })

    try:
        start = time.time()
        driver.get(url)
        end = time.time()
        return end - start
    finally:
        driver.quit()


if __name__ == "__main__":
    target_url = "https://www.sainsburys.co.uk/gol-ui/groceries"
    load_time = measure_page_load_time(target_url)
    print(f"⏱️ Page load time: {load_time:.2f} seconds")
