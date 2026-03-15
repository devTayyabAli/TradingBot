"""
Manual SSID Extractor for Quotex Live Mode
Run this while logged into Quotex in Chrome
"""
import json
import os

print("="*60)
print("QUOTEX LIVE MODE - SSID EXTRACTOR")
print("="*60)

# Read credentials
config_path = r"d:\TradingBot\API-Quotex-main\sessions\config.json"
session_path = r"d:\TradingBot\API-Quotex-main\sessions\session.json"

with open(config_path) as f:
    config = json.load(f)

print(f"\nEmail: {config.get('email', 'N/A')}")
print(f"Password: {'*' * len(config.get('password', ''))}")

print("\n" + "="*60)
print("INSTRUCTIONS TO GET LIVE MODE WORKING:")
print("="*60)

print("""
1. OPEN CHROME (keep it open)
2. Go to: https://market-qx.trade
3. Login if not already logged in
4. Press F12 (Developer Tools)
5. Click on NETWORK tab
6. Filter by "WS" (WebSocket)
7. Refresh page (F5)
8. Look for connection to: wss://ws.qxbroker.com/
9. Click on it
10. Click MESSAGES tab
11. Look for first message sent (authorization)
12. Copy the session ID from:
    42["authorization",{"session":"XXXXX",...}]
    
    Session ID is the XXXXX part (without quotes)
""")

print("="*60)
ssid = input("\nPaste the Session ID here: ").strip()

if ssid:
    # Build SSID frame
    ssid_frame = f'42["authorization",{{"session":"{ssid}","isDemo":0,"tournamentId":0}}]'
    
    # Save
    with open(session_path, 'w') as f:
        json.dump({
            "ssid": ssid_frame,
            "is_demo": False
        }, f, indent=2)
    
    print(f"\n[OK] Session saved to: {session_path}")
    print(f"SSID: {ssid_frame[:60]}...")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Restart the server:")
    print("   taskkill /f /im python.exe")
    print("   venv\\Scripts\\python start_server.py")
    print("\n2. Refresh your browser")
    print("\n3. You should now see LIVE data!")
    print("="*60)
else:
    print("\n[ERROR] No SSID provided. Session not updated.")
