import os
import time
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

INPUT_FOLDER = "categories"
OUTPUT_FOLDER = "data"
INPUT_FILE = "Meat (beef, pork, poultry).txt"
SEPARATOR = ";"

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_PLUS_KEY"))

options = uc.ChromeOptions()
#options.add_argument("--headless=new")  # UI
driver = uc.Chrome(options=options)


def accept_cookies():
    try:
        driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
        time.sleep(3)
        print("Page loaded")

        wait = WebDriverWait(driver, 10)
        cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all']")))
        cookies_button.click()
        time.sleep(1)
        print("Cookies accepted")
    except:
        print("Cookies already accepted or not shown")


def extract_nutrition():
    """
    Extracts kcal, fat, protein, carbohydrate from nutrition table using GPT-4o-mini
    """
    try:
        wait = WebDriverWait(driver, 10)
        table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nutritionTable")))
        html = table.get_attribute("outerHTML")

        prompt = f"""
        You are a nutrition label parser.

        Here is an HTML table extracted from a grocery product page:
        {html}

        Extract the following values (per 100g or 100ml):
        - kcal
        - fat
        - carbohydrates
        - protein

        If the value contains a "<" sign (e.g. "<0.5g"), ignore the sign and return the number only (e.g. "0.5").
        Return the result in this format (numbers only, no units):
        kcal: <number>, fat: <number>, carbs: <number>, protein: <number>
        If any value is missing or not present, return 'N/A' for that field.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )

        nutrition_result = response.choices[0].message.content.strip()
        return nutrition_result

    except Exception as e:
        print(f"Nutrition extraction failed: {e}")
        return "N/A"


def extract_product_data(url):
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        name_elem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pd__header")))
        name = name_elem.text.strip()
        price_text = driver.find_element(By.CLASS_NAME, "pd__cost__retail-price").text.strip()
        price = price_text.replace("£", "").strip()
        nutrition = extract_nutrition()
        print(f"{name} ||| {price} ||| {nutrition}")

        return f"{name}{SEPARATOR}{url}{SEPARATOR}{price}{SEPARATOR}{nutrition}{SEPARATOR}true"
    except Exception as e:
        print(f"Failed: {url} -> {e}")
        return None


def main():
    input_path = os.path.join(INPUT_FOLDER, INPUT_FILE)
    category_name = INPUT_FILE.replace(".txt", "").strip()
    output_path = os.path.join(OUTPUT_FOLDER, f"{category_name} data.txt")

    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    processed_urls = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f_out:
            for line in f_out:
                parts = line.strip().split(SEPARATOR)
                if len(parts) >= 2:
                    processed_urls.add(parts[1])

    with open(input_path, "r", encoding="utf-8") as f:
        items = []
        for line in f:
            if ": http" in line:
                name, link = line.strip().split(": http", 1)
                link = "http" + link.strip()
                if link not in processed_urls:
                    items.append((name.strip(), link))

    print(f"Resuming from line {len(processed_urls)}. Remaining: {len(items)} URLs.")

    accept_cookies()

    with open(output_path, "a", encoding="utf-8") as f_out:
        for original_name, url in tqdm(items, desc="Processing"):
            data = extract_product_data(url)
            if data:
                f_out.write(data + "\n")

    driver.quit()
    print(f"\nDone. Output saved to: {output_path}")

if __name__ == "__main__":
    main()
