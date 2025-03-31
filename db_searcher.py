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
    """
    Establish a connection to the PostgreSQL database

    Returns:
        psycopg2.extensions.connection: Database connection object
    """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def get_category_from_query(query: str) -> str:
    """
    Use GPT to classify the user's query into a known product category

    Args:
        query (str): Natural language query from the user

    Returns:
        str: Category name from CATEGORIES list or "Uncategorized"
    """
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
    """
    Extract 1–3 key terms from the user's query (e.g. brand, product type)

    Args:
        query (str): User's original request

    Returns:
        List[str]: List of lowercase keywords
    """
    prompt = f"""Extract 1–3 short keywords (e.g. brand, type, or key features) from the query.
    It could be just the name of the product (e.g. water, milk, pizza). Each key = 1 word.
    If the product name consists of several words, separate them (e.g. easy peelers -> easy, peelers).
    If the user's query is not in English, first translate it into English.
    Return a comma-separated list."""

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
    )
    keywords = response.choices[0].message.content.strip().lower().split(",")
    return [k.strip() for k in keywords if k.strip()]


def validate_match(product_name: str, query: str) -> bool:
    """
    Determine if a product name matches the user's intent

    Args:
        product_name (str): Product title from database
        query (str): Original user query

    Returns:
        bool: True if the product matches user intent, False otherwise
    """
    prompt = f"""User asked: "{query}"
    Product name: "{product_name}"
    Does this product match the intent of the user request? Respond with 'Yes' or 'No' only."""

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().lower().startswith("yes")


def validate_fallback(product_names: List[str], query: str, max_results: int = 10) -> List[int]:
    """
    Uses GPT to filter a list of product names and return indexes of those most relevant to the query

    Args:
        product_names (List[str]): List of product titles from fallback query
        query (str): Original user query
        max_results (int): Maximum number of results to return

    Returns:
        List[int]: Indexes of matching products
    """
    items = "\n".join([f"{i+1}. {name}" for i, name in enumerate(product_names)])

    prompt = f"""User asked: "{query}"
    Here is a list of product names:
    {items}
    
    Your task is to select the most relevant products (up to {max_results}) that match the user's request. 
    Return only a list of numbers corresponding to the items, separated by commas. Do not return anything else."""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        indexes = [int(i) - 1 for i in content.split(",") if i.strip().isdigit()]
        return [i for i in indexes if 0 <= i < len(product_names)]
    except Exception as e:
        print(f"GPT filtering failed: {e}")
        return list(range(min(max_results, len(product_names))))


@app.get("/search")
def search_products(query_str: str = Query(..., description="Search like 'I want Aptamil baby milk'")):
    """
    Endpoint to search products based on a natural language query.
    First extracts category and keywords, then searches and filters validated products

    Args:
        query_str (str): User's query string

    Returns:
        dict: Search results including matched products
    """
    try:
        category = get_category_from_query(query_str)
        keywords = extract_keywords(query_str)

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
        validated_results = []

        if raw_results:
            for name, url in raw_results:
                if validate_match(name, query_str):
                    validated_results.append({"name": name, "url": url})
                if len(validated_results) >= 10:
                    break
        else:
            fallback_conditions = " OR ".join(["LOWER(name) LIKE %s"] * len(keywords))
            fallback_query = f"""
                SELECT name, url FROM products
                WHERE {fallback_conditions}
                LIMIT 200
            """
            cur.execute(fallback_query, [f"%{kw}%" for kw in keywords])
            raw_results = cur.fetchall()
            product_names = [name for name, _ in raw_results]
            selected_indexes = validate_fallback(product_names, query_str)

            validated_results = [{"name": raw_results[i][0], "url": raw_results[i][1]} for i in selected_indexes[:10]]

        cur.close()
        conn.close()

        return {
            "query": query_str,
            "category": category,
            "keywords": keywords,
            "results": validated_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {e}")
