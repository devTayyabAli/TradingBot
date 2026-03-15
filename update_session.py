"""
Helper script to update Quotex session with fresh SSID
Run this after manually obtaining a new session from browser
"""
import json
import os

SESSION_FILE = r"d:\TradingBot\API-Quotex-main\sessions\session.json"

def update_session(new_ssid: str, is_demo: bool = True):
    """Update session.json with new SSID"""
    # Format SSID in Socket.IO frame if not already
    if not new_ssid.startswith('42['):
        formatted_ssid = f'42["authorization",{{"session":"{new_ssid}","isDemo":{1 if is_demo else 0},"tournamentId":0}}]'
    else:
        formatted_ssid = new_ssid
    
    session_data = {
        "ssid": formatted_ssid,
        "is_demo": is_demo
    }
    
    with open(SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=4)
    
    print(f"✅ Session updated successfully!")
    print(f"📁 File: {SESSION_FILE}")
    print(f"🔑 SSID: {formatted_ssid[:50]}...")
    print(f"\n🚀 Restart the server to use the new session:")
    print(f"   taskkill /f /im python.exe")
    print(f"   venv\\Scripts\\python start_server.py")

if __name__ == "__main__":
    print("=" * 60)
    print("Quotex Session Updater")
    print("=" * 60)
    print("\nTo get a fresh SSID:")
    print("1. Open Chrome and go to https://qxbroker.com")
    print("2. Log in with your credentials")
    print("3. Open DevTools (F12) → Application → Cookies")
    print("4. Find 'session' or 'ssid' cookie")
    print("5. Copy the value (should look like: Y62R6vFomrGvuCQ...)")
    print("6. Paste it below:\n")
    
    ssid = input("Enter new SSID: ").strip()
    
    if ssid:
        update_session(ssid)
    else:
        print("❌ No SSID provided. Session not updated.")
