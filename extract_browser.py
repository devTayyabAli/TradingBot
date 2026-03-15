"""
Browser-based SSID extractor for Quotex
Opens Chrome, logs in, and extracts the session
"""
import asyncio
import json
import os
import sys

# Add api_quotex to path
API_QUOTEX_PATH = os.path.join(os.path.dirname(__file__), "..", "API-Quotex-main")
if API_QUOTEX_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(API_QUOTEX_PATH))

from api_quotex.login import get_ssid

async def extract_session():
    # Read credentials
    config_path = os.path.join(API_QUOTEX_PATH, "sessions", "config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    email = config.get("email", "")
    password = config.get("password", "")
    
    print("Extracting fresh SSID from Quotex...")
    print(f"Email: {email}")
    print("\nThis will open Chrome. Please:")
    print("1. Wait for the page to load")
    print("2. Complete any CAPTCHA if shown")
    print("3. The session will be extracted automatically")
    print("\nStarting browser...")
    
    # Try to get SSID (is_demo=False for live mode)
    ok, session_data = await get_ssid(email=email, password=password, is_demo=False)
    
    if ok and session_data.get("ssid"):
        ssid = session_data["ssid"]
        print(f"\n[OK] Got fresh SSID: {ssid[:50]}...")
        
        # Save to session.json
        session_path = os.path.join(API_QUOTEX_PATH, "sessions", "session.json")
        with open(session_path, 'w') as f:
            json.dump({
                "ssid": ssid,
                "is_demo": False
            }, f, indent=2)
        
        print(f"[OK] Saved to {session_path}")
        print("\nRestart the server:")
        print("  taskkill /f /im python.exe")
        print("  venv\\Scripts\\python start_server.py")
        return True
    else:
        print("\n[FAIL] Could not extract session")
        print("Trying alternative method...")
        return False

if __name__ == "__main__":
    success = asyncio.run(extract_session())
    
    if not success:
        print("\n" + "="*60)
        print("ALTERNATIVE: Manual Extraction")
        print("="*60)
        print("\n1. Open Chrome -> https://market-qx.trade")
        print("2. Login with your credentials")
        print("3. F12 -> Application -> Cookies")
        print("4. Look for 'session' cookie")
        print("5. Copy the value and paste it below:")
        
        ssid = input("\nPaste session ID: ").strip()
        
        if ssid:
            session_path = os.path.join(API_QUOTEX_PATH, "sessions", "session.json")
            with open(session_path, 'w') as f:
                json.dump({
                    "ssid": ssid,
                    "is_demo": False
                }, f, indent=2)
            print("[OK] Session saved!")
