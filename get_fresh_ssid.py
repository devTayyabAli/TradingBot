"""
Get fresh SSID from Quotex browser session
"""
import asyncio
import os
import sys

# Add api_quotex to path
API_QUOTEX_PATH = os.path.join(os.path.dirname(__file__), "..", "API-Quotex-main")
if API_QUOTEX_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(API_QUOTEX_PATH))

from api_quotex.login import get_ssid

async def main():
    email = input("Enter Quotex email: ").strip()
    password = input("Enter Quotex password: ").strip()
    
    print("\n🔐 Attempting login with browser automation...")
    print("⏳ Chrome will open. Complete any CAPTCHA if needed.\n")
    
    ok, session = await get_ssid(email=email, password=password, is_demo=True)
    
    if ok and session.get("ssid"):
        print(f"\n✅ SUCCESS! SSID obtained:")
        print(f"   {session['ssid'][:60]}...")
        print(f"\n📁 Session saved to API-Quotex-main/sessions/session.json")
        print("🚀 Restart your server to use real Quotex data!")
    else:
        print("\n❌ Failed to get SSID automatically")
        print("\n🔧 Manual method:")
        print("1. Open Chrome → https://qxbroker.com")
        print("2. Log in")
        print("3. F12 → Network → WS (WebSocket)")
        print("4. Look for wss://ws.qxbroker.com/")
        print("5. Find 'authorization' message with session ID")

if __name__ == "__main__":
    asyncio.run(main())
