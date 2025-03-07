import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

start = time.time()
driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
end = time.time()

print(f"Page load time: {end - start:.2f} seconds")
driver.quit()

