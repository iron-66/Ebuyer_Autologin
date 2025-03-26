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
    title="Product Search API",
    description="Search for grocery products based on natural language queries",
    version="2.0.0"
)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def analyze_query_with_gpt(query: str) -> dict:
    system_prompt = """
    You're a product search assistant. Given a user query, extract:
    1. Category from a predefined list
    2. Brand (if specified)
    3. Product type (if specified)

    Return ONLY in this format:
    Category: <category>
    Brand: <brand or None>
    Type: <product type or None>
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    )

    result = response.choices[0].message.content.strip().split("\n")
    parsed = {line.split(":")[0].lower(): line.split(":")[1].strip() for line in result if ":" in line}
    return parsed

def validate_results_with_gpt(query: str, results: List[dict]) -> List[dict]:
    product_text = "\n".join([f"{r['name']} ({r['url']})" for r in results])
    system_prompt = """
    You are a product validator. Given a user's query and a list of product names, return ONLY those that are relevant to the query. If none match, return an empty list.
    Format: name: url
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\nProducts:\n{product_text}"}
        ]
    )

    lines = response.choices[0].message.content.strip().split("\n")
    valid = [line for line in lines if "(" in line and ")" in line]
    output = []
    for line in valid:
        try:
            name, url = line.rsplit("(", 1)
            output.append({"name": name.strip(), "url": url.replace(")", "").strip()})
        except:
            continue
    return output

@app.get("/search")
def search_products(q: str = Query(..., description="Search query like 'I want Aptamil baby milk'")):
    try:
        parsed = analyze_query_with_gpt(q)
        category = parsed.get("category", "Uncategorized")
        brand = parsed.get("brand", None)
        product_type = parsed.get("type", None)

        search_keywords = []
        if brand and brand.lower() != "none":
            search_keywords.append(f"%{brand.lower()}%")
        if product_type and product_type.lower() != "none":
            search_keywords.append(f"%{product_type.lower()}%")

        conditions = " AND ".join(["LOWER(name) LIKE %s"] * len(search_keywords))
        sql = f"SELECT name, url FROM products WHERE category = %s"
        if conditions:
            sql += f" AND {conditions}"
        sql += " LIMIT 20"

        values = [category] + search_keywords

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, values)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = [{"name": name, "url": url} for name, url in rows]
        validated = validate_results_with_gpt(q, results)

        return {
            "query": q,
            "category": category,
            "brand": brand,
            "type": product_type,
            "results": validated
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {e}")