from fastapi import FastAPI, HTTPException, Query
from typing import List
import psycopg2
import os
from dotenv import load_dotenv
import openai

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_PLUS_KEY")

openai.api_key = OPENAI_API_KEY

# ------------------------------
# Initialize FastAPI
# ------------------------------
app = FastAPI(
    title="Product Search API",
    description="Search for grocery products based on natural language queries",
    version="1.0.0"
)

# ------------------------------
# Connect to PostgreSQL
# ------------------------------
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# ------------------------------
# Helper to convert query to SQL category
# ------------------------------
def get_category_from_query(query: str) -> str:
    categories = [
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

    system_prompt = f"""You are an assistant that maps user food requests to product categories.
Available categories: {', '.join(categories)}
Respond ONLY with the name of the best-matching category from the list above."""

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    )

    category = response.choices[0].message.content.strip()
    return category if category in categories else "Uncategorized"

# ------------------------------
# Endpoint: /search
# ------------------------------
@app.get("/search")
def search_products(q: str = Query(..., description="Search query like 'I want chocolate snacks'")):
    category = get_category_from_query(q)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, url FROM groceries
            WHERE category = %s
            LIMIT 10
        """, (category,))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "query": q,
            "category": category,
            "results": [{"name": name, "url": url} for name, url in rows]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")