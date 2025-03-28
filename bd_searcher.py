from fastapi import FastAPI, HTTPException, Query
from typing import List
import psycopg2
import os
from dotenv import load_dotenv
import openai

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_PLUS_KEY")

openai.api_key = OPENAI_API_KEY

app = FastAPI(
    title="Smart Grocery Product Search",
    description="Finds products by natural language request, using category, brand, type and validation",
    version="2.0.0"
)

CATEGORIES = [
    "Fresh fruits", "Fresh vegetables", "Greens (lettuce, herbs)", "Mushrooms",
    "Frozen fruits and vegetables", "Meat (beef, pork, poultry)", "Fish and seafood", "Sausages and bacon",
    "Plant-based meat alternatives", "Milk, yogurts, kefir", "Cheeses", "Butter", "Eggs and egg products",
    "Plant-based dairy alternatives", "Bread and bakery products", "Cakes, muffins, desserts", "Spices",
    "Chocolate and candies", "Frozen vegetables and mixes", "Frozen desserts and ice cream", "Cereals",
    "Semi-finished products (ready-made meals, salads, Kyiv cutlets, etc.)",
    "Ready meals that require minimal processing", "Soft drinks (soda, energy drinks)",
    "Juices, nectars and smoothies", "Water", "Tea and coffee", "Alcohol", "Canned goods and preserves",
    "Pasta, rice, cereals", "Sauces, seasonings and spices", "Oils and vinegars",
    "Snacks and cookies", "Nuts and dried fruits", "Home and household", "Baby food", "Health supplements"
]

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def get_category_from_query(query: str) -> str:
    prompt = f"""You are a classification assistant.
Task: Given a user request for a grocery item, return the best category.
Categories: {', '.join(CATEGORIES)}
If the user's query is not in English, first translate it into English. Then choose the best matching category from the list above.
ONLY return the category name from the list."""

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
    )
    category = response.choices[0].message.content.strip()
    return category if category in CATEGORIES else "Uncategorized"

def extract_keywords(query: str) -> List[str]:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract 1–3 short keywords (e.g. brand, type, or key features) from the query. If the user's query is not in English, first translate it into English. Return a comma-separated list."},
            {"role": "user", "content": query}
        ]
    )
    keywords = response.choices[0].message.content.strip().lower().split(",")
    return [k.strip() for k in keywords if k.strip()]

def validate_match(product_name: str, query: str) -> bool:
    prompt = f"""User asked: "{query}"
Product name: "{product_name}"
Does this product match the intent of the user request? Respond with 'Yes' or 'No' only."""

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().lower().startswith("yes")

@app.get("/search")
def search_products(q: str = Query(..., description="Search like 'I want Aptamil baby milk'")):
    try:
        category = get_category_from_query(q)
        keywords = extract_keywords(q)

        if category == "Uncategorized":
            raise HTTPException(status_code=400, detail="Could not determine category from query.")

        if not keywords:
            raise HTTPException(status_code=400, detail="Could not extract useful keywords.")

        conn = get_db_connection()
        cur = conn.cursor()

        keyword_conditions = " AND ".join(["LOWER(name) ILIKE %s"] * len(keywords))
        sql = f"""
            SELECT name, url FROM products
            WHERE category = %s AND {keyword_conditions}
            LIMIT 20
        """
        cur.execute(sql, [category] + [f"%{kw}%" for kw in keywords])
        raw_results = cur.fetchall()

        if not raw_results and keywords:
            fallback_pattern = f"%{keywords[0]}%"
            cur.execute("""
                        SELECT name, url FROM products
                        WHERE category = %s AND LOWER(name) LIKE %s
                        LIMIT 10
                    """, (category, fallback_pattern))
            raw_results = cur.fetchall()

        cur.close()
        conn.close()

        validated_results = []
        for name, url in raw_results:
            if validate_match(name, q):
                validated_results.append({"name": name, "url": url})
            if len(validated_results) >= 10:
                break

        return {
            "query": q,
            "category": category,
            "keywords": keywords,
            "results": validated_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {e}")
