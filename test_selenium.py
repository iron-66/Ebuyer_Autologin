import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--log-level=3")
#options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

#options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
#                                "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=options)
# driver.execute_cdp_cmd("Network.setUserAgentOverride", {
#     "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36"
# })

start = time.time()
driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
end = time.time()

print(f"Page load time: {end - start:.2f} seconds")
driver.quit()

