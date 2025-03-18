from openai import OpenAI
import os
from dotenv import load_dotenv
import time
from tqdm import tqdm

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_PLUS_KEY"))
START_LINE = 6260
INPUT_FILE = "products_links.txt"

CATEGORIES = [
    "Fresh fruits", "Fresh vegetables", "Greens (lettuce, herbs)", "Mushrooms",
    "Frozen fruits and vegetables", "Meat (beef, pork, poultry)", "Fish and seafood", "Sausages and bacon",
    "Plant-based meat alternatives", "Milk, yogurts, kefir", "Cheeses", "Butter", "Eggs and egg products",
    "Plant-based dairy alternatives", "Bread and bakery products", "Cakes, muffins, desserts",
    "Chocolate and candies", "Frozen vegetables and mixes", "Frozen desserts and ice cream",
    "Semi-finished products (ready-made meals, salads, Kyiv cutlets, etc.)", "Ready meals that require minimal processing",
    "Soft drinks (soda, energy drinks)", "Juices, nectars and smoothies", "Water", "Tea and coffee", "Alcohol",
    "Canned goods and preserves", "Pasta, rice, cereals", "Sauces, seasonings and spices", "Oils and vinegars",
    "Sweet and salty snacks, cookies", "Nuts and dried fruits", "Home and household", "Baby food"
]

def classify_product(url):
    prompt = f"""The following is a product URL from Sainsbury's online store:
{url}

Your task is to understand what kind of product it is based solely on the link address and assign it to one of the categories from the following list:
{", ".join(CATEGORIES)}

Return ONLY the category name that best fits the product. No explanations.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        category = response.choices[0].message.content.strip()
        print(category)
        return category if category in CATEGORIES else "Uncategorized"
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return "Uncategorized"

for category in CATEGORIES:
    open(f"categories/{category}.txt", "w").close()

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    urls = [line.strip() for line in file.readlines() if line.strip()]

urls_to_process = urls[START_LINE:]

for url in tqdm(urls_to_process, desc="Processing URLs"):
    category = classify_product(url)

    with open(f"categories/{category}.txt", "a", encoding="utf-8") as file:
        file.write(url + "\n")

    time.sleep(1)

print("✅ Classification completed! Check the 'categories' folder.")
