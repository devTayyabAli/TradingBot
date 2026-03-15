"""
Extract SSID from Quotex using existing credentials
Tries multiple methods: cloudscraper, browser automation, localStorage extraction
"""
import asyncio
import json
import os
import sys

# Add api_quotex to path
API_QUOTEX_PATH = os.path.join(os.path.dirname(__file__), "..", "API-Quotex-main")
if API_QUOTEX_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(API_QUOTEX_PATH))

# Read credentials
config_path = os.path.join(API_QUOTEX_PATH, "sessions", "config.json")
with open(config_path) as f:
    config = json.load(f)

email = config.get("email", "")
password = config.get("password", "")

print(f"Using credentials: {email}")
print("Attempting login...\n")

# Method 1: Try cloudscraper first
print("Method 1: Cloudscraper login...")
try:
    import cloudscraper
    import requests
    
    scraper = cloudscraper.create_scraper()
    
    # Quotex login endpoint
    login_url = "https://market-qx.trade/en/sign-in"
    api_url = "https://api.qxbroker.com/v1/auth/login"
    
    session = requests.Session()
    
    # Get initial cookies
    resp = session.get(login_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    print(f"   Status: {resp.status_code}")
    
    # Try API login
    login_data = {
        "email": email,
        "password": password,
        "remember": True
    }
    
    resp = session.post(api_url, json=login_data, headers={
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    })
    
    print(f"   API Response: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        if 'token' in data or 'session' in data:
            print(f"[OK] Got session via API!")
            print(f"   Data: {data}")
            
except Exception as e:
    print(f"   Failed: {e}")

# Method 2: Browser automation
print("\nMethod 2: Browser automation...")
try:
    from playwright.async_api import async_playwright
    
    async def browser_login():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=100)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            
            # Navigate to login
            await page.goto("https://market-qx.trade/en/sign-in", wait_until='networkidle')
            
            print("   Page loaded, filling credentials...")
            
            # Fill login form
            await page.fill('input[type="email"], input[name="email"]', email)
            await page.fill('input[type="password"], input[name="password"]', password)
            
            # Click login
            await page.click('button[type="submit"], .btn-login')
            
            # Wait for navigation
            await page.wait_for_timeout(5000)
            
            # Check localStorage for session
            local_storage = await page.evaluate('() => JSON.stringify(localStorage)')
            print(f"   LocalStorage: {local_storage[:200]}...")
            
            # Check cookies
            cookies = await context.cookies()
            for cookie in cookies:
                if 'session' in cookie['name'].lower() or 'ssid' in cookie['name'].lower():
                    print(f"   Found session cookie: {cookie['name']} = {cookie['value'][:30]}...")
            
            # Keep browser open for manual inspection
            print("   Browser open for 30 seconds...")
            await page.wait_for_timeout(30000)
            
            await browser.close()
    
    asyncio.run(browser_login())
    
except Exception as e:
    print(f"   Failed: {e}")

print("\n" + "="*60)
print("\n[ERROR] If automatic methods failed, use manual extraction:")
print("1. Open https://qxbroker.com in Chrome")
print("2. Login with your credentials")
print("3. F12 -> Application -> LocalStorage")
print("4. Look for 'session' or 'token' key")
print("5. Copy the value and update session.json")
print("="*60)
