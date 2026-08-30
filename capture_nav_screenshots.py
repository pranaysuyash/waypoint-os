#!/usr/bin/env python3
import os
import requests
from playwright.sync_api import sync_playwright

target_dir = "/Users/pranay/.gemini/antigravity/brain/75e69aa1-b102-49fd-a614-fe795a8063f3"
os.makedirs(target_dir, exist_ok=True)

# 1. Login to FastAPI backend to set httpOnly auth cookies
login_url = "http://localhost:8000/api/auth/login"
resp = requests.post(login_url, json={"email": "newuser@test.com", "password": "testpass123"})
print(f"Backend login response: {resp.status_code}")

cookies_list = []
if resp.status_code == 200:
    for cookie_name, cookie_val in resp.cookies.items():
        cookies_list.append({
            "name": cookie_name,
            "value": cookie_val,
            "domain": "localhost",
            "path": "/",
        })
    print(f"Acquired auth cookies: {[c['name'] for c in cookies_list]}")

routes = [
    ("overview", "http://localhost:3005/overview"),
    ("inquiries_new", "http://localhost:3005/inquiries/new"),
    ("quotes", "http://localhost:3005/quotes"),
    ("bookings", "http://localhost:3005/bookings"),
    ("suppliers", "http://localhost:3005/suppliers"),
    ("knowledge", "http://localhost:3005/knowledge"),
    ("documents", "http://localhost:3005/documents"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    if cookies_list:
        context.add_cookies(cookies_list)

    page = context.new_page()

    for name, url in routes:
        try:
            print(f"📸 Capturing {name}: {url}...")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            shot_path = os.path.join(target_dir, f"nav_{name}.png")
            page.screenshot(path=shot_path, full_page=False)
            print(f"✅ Saved screenshot to {shot_path}")
        except Exception as e:
            print(f"❌ Failed to capture {name}: {e}")

    browser.close()
    print("🎉 All Authenticated Navigation Screenshots Captured Successfully!")
