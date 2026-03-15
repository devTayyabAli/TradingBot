"""
Manual Session Setup for Quotex API
Run this to create session.json from manually obtained SSID
"""
import json
import os

SESSIONS_DIR = r"d:\TradingBot\API-Quotex-main\sessions"
SESSION_FILE = os.path.join(SESSIONS_DIR, "session.json")

def setup_manual_session():
    print("=" * 60)
    print("Manual Quotex Session Setup")
    print("=" * 60)
    print("\nSince browser automation isn't working, we'll set up manually.")
    print("\nSteps:")
    print("1. Open Chrome and go to: https://qxbroker.com/en/sign-in/")
    print("2. Log in with your credentials")
    print("3. Press F12 → Network tab → WS (WebSocket)")
    print("4. Look for WebSocket connection to qxbroker.com")
    print("5. Find the 'authorization' message with your session ID")
    print("\nOR use this easier method:")
    print("1. After logging in, press F12 → Application/Storage tab")
    print("2. Look in Local Storage or Cookies for 'session' or 'ssid'")
    print("3. Copy that value")
    print()
    
    ssid = input("Paste your SSID/session token here: ").strip()
    
    if not ssid or len(ssid) < 10:
        print("❌ Invalid SSID (too short)")
        return False
    
    # Save to session.json
    session_data = {
        "ssid": ssid,
        "is_demo": True
    }
    
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=4)
    
    print(f"\n✅ Session saved to: {SESSION_FILE}")
    print(f"   SSID: {ssid[:20]}...")
    print("\nNow restart your server:")
    print("   Ctrl+C")
    print("   venv\\Scripts\\python start_server.py")
    return True

if __name__ == "__main__":
    setup_manual_session()
