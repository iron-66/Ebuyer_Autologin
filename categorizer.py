from openai import OpenAI
import os
from dotenv import load_dotenv
import time
from tqdm import tqdm

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_PLUS_KEY"))

INPUT_FILE = "products_links.txt"
CATEGORY_DIR = "categories"

CATEGORIES = [
    "Fresh fruits", "Fresh vegetables", "Greens (lettuce, herbs)", "Mushrooms",
    "Frozen fruits and vegetables", "Meat (beef, pork, poultry)", "Fish and seafood", "Sausages and bacon",
    "Plant-based meat alternatives", "Milk, yogurts, kefir", "Cheeses", "Butter", "Eggs and egg products",
    "Plant-based dairy alternatives", "Bread and bakery products", "Cakes, muffins, desserts", "Spices",
    "Chocolate and candies", "Frozen vegetables and mixes", "Frozen desserts and ice cream", "Cereals",
    "Semi-finished products (ready-made meals, salads, Kyiv cutlets, etc.)", "Ready meals that require minimal processing",
    "Soft drinks (soda, energy drinks)", "Juices, nectars and smoothies", "Water", "Tea and coffee", "Alcohol",
    "Canned goods and preserves", "Pasta, rice, cereals", "Sauces, seasonings and spices", "Oils and vinegars",
    "Snacks and cookies", "Nuts and dried fruits", "Home and household", "Baby food", "Health supplements"
]

os.makedirs(CATEGORY_DIR, exist_ok=True)

def get_last_processed_line():
    processed_urls = set()
    for category in CATEGORIES:
        category_file = os.path.join(CATEGORY_DIR, f"{category}.txt")
        if os.path.exists(category_file):
            with open(category_file, "r", encoding="utf-8") as file:
                for line in file:
                    if line.strip():
                        processed_urls.add(line.strip().split(": ")[-1])
    return processed_urls

processed_urls = get_last_processed_line()

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    urls = [line.strip() for line in file.readlines() if line.strip()]

urls_to_process = [url for url in urls if url not in processed_urls]

print(f"🔄 Resuming from line {len(processed_urls)}. Remaining: {len(urls_to_process)} URLs.")

def classify_product(url):
    prompt = f"""The following is a product URL from Sainsbury's online store:
{url}

Your task is:
1. Extract the product name from the URL.
2. Assign the product to one of the categories from the following list:
{", ".join(CATEGORIES)}

Return the response in this format: 
Category: <category_name>
Product Name: <product_name>

Do NOT return anything else.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content.strip()
        print(content)

        lines = content.split("\n")
        category = lines[0].replace("Category: ", "").strip()
        product_name = lines[1].replace("Product Name: ", "").strip()

        if category not in CATEGORIES:
            category = "Uncategorized"

        return category, product_name
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return "Uncategorized", "Unknown Product"

for url in tqdm(urls_to_process, desc="Processing URLs"):
    category, product_name = classify_product(url)

    with open(os.path.join(CATEGORY_DIR, f"{category}.txt"), "a", encoding="utf-8") as file:
        file.write(f"{product_name}: {url}\n")

    time.sleep(1)

print("Classification completed. All created files in the 'categories' folder.")
