"""
Get fresh SSID using cloudscraper (no browser needed)
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(r"d:\TradingBot\API-Quotex-main"))

from api_quotex.login import get_ssid

async def get_fresh_session():
    # Read credentials
    config_path = r"d:\TradingBot\API-Quotex-main\sessions\config.json"
    with open(config_path, "r") as f:
        cfg = json.load(f)
    
    email = cfg.get("email", "")
    password = cfg.get("password", "")
    
    print(f"Getting fresh session for {email[:5]}...")
    
    try:
        ok, session_data = await get_ssid(email=email, password=password, is_demo=True)
        if ok and session_data.get("ssid"):
            print(f"[SUCCESS] SSID obtained.")
            print(f"   Token: {session_data.get('token', 'N/A')[:30]}...")
            print(f"   SSID length: {len(session_data['ssid'])}")
            
            # Save to session.json
            session_path = r"d:\TradingBot\API-Quotex-main\sessions\session.json"
            with open(session_path, "w") as f:
                json.dump(session_data, f, indent=4)
            print(f"[SUCCESS] Saved to {session_path}")
            return True
        else:
            print(f"[FAILED] ok={ok}, has_ssid={bool(session_data.get('ssid'))}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(get_fresh_session())
    sys.exit(0 if result else 1)
