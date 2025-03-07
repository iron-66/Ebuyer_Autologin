import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=options)

start = time.time()
driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
end = time.time()

print(f"Page load time: {end - start:.2f} seconds")
driver.quit()

