from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")  # Без интерфейса
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
    print("Selenium запущен успешно!")
    driver.quit()
except Exception as e:
    print(f"Ошибка запуска Selenium: {e}")
