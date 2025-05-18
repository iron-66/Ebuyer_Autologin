from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psycopg2
import uuid
import os
import bcrypt
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

app = FastAPI(title="User Auth & Profile API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Database connection
# ----------------------------
def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# ----------------------------
# Pydantic models
# ----------------------------
class UserProfile(BaseModel):
    login: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    postcode: Optional[str] = None
    address: Optional[str] = None

# ----------------------------
# Verify login via Selenium
# ----------------------------
def verify_sainsburys_credentials(login: str, password: str) -> bool:
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)

        driver.get("https://www.sainsburys.co.uk/gol-ui/groceries")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all']"))
        ).click()
        driver.find_element(By.LINK_TEXT, "Log in / Register").click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all cookies']"))
        ).click()
        driver.find_element(By.ID, "username").send_keys(login)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "account-link"))
        )
        driver.quit()
        return True
    except Exception as e:
        print(f"[LOGIN ERROR] {e}")
        return False

# ----------------------------
# POST /login
# ----------------------------
@app.post("/login")
def login_user(login: str = Form(...), password: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE login = %s", (login,))
    user = cur.fetchone()

    if user:
        stored_hash = user[3]
        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            raise HTTPException(status_code=403, detail="Incorrect password.")
        return {"status": "existing_user", "uuid": user[1]}
    else:
        if not verify_sainsburys_credentials(login, password):
            raise HTTPException(status_code=401, detail="Invalid Sainsbury's credentials.")

        user_uuid = str(uuid.uuid4())
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute("""
            INSERT INTO users (uuid, login, password)
            VALUES (%s, %s, %s)
        """, (user_uuid, login, hashed_password))
        conn.commit()
        return {"status": "created", "uuid": user_uuid}

# ----------------------------
# GET /profile
# ----------------------------
@app.get("/profile/{uuid}")
def get_profile(uuid: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT first_name, last_name, phone, postcode, address FROM users WHERE uuid = %s", (uuid,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "first_name": row[0],
        "last_name": row[1],
        "phone": row[2],
        "postcode": row[3],
        "address": row[4]
    }

# ----------------------------
# POST /profile/{uuid}
# ----------------------------
@app.post("/profile/{uuid}")
def update_profile(uuid: str, data: UserProfile):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET
            first_name = %s,
            last_name = %s,
            phone = %s,
            postcode = %s,
            address = %s
        WHERE uuid = %s
    """, (
        data.first_name,
        data.last_name,
        data.phone,
        data.postcode,
        data.address,
        uuid
    ))
    conn.commit()
    return {"status": "updated"}
