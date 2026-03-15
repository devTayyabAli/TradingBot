"""
Debug Quotex connection with different formats
"""
import asyncio
import json
import os
import sys

# Add api_quotex to path
API_QUOTEX_PATH = os.path.join(os.path.dirname(__file__), "..", "API-Quotex-main")
if API_QUOTEX_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(API_QUOTEX_PATH))

from api_quotex.client import AsyncQuotexClient
from api_quotex.login import validate_ssid

async def test_ssid_formats():
    session_path = os.path.join(API_QUOTEX_PATH, "sessions", "session.json")
    with open(session_path) as f:
        session_data = json.load(f)
    
    raw_ssid = session_data.get("ssid", "")
    
    print("Testing different SSID formats...")
    print(f"Raw SSID from file: {raw_ssid[:50]}...")
    
    # Try different formats
    formats_to_test = [
        # Format 1: Raw SSID (current)
        ("Raw SSID", raw_ssid),
        # Format 2: With Socket.IO frame
        ("Socket.IO frame", f'42["authorization",{{"session":"{raw_ssid}","isDemo":0,"tournamentId":0}}]'),
        # Format 3: Try demo mode
        ("Demo mode raw", raw_ssid, True),
    ]
    
    for name, ssid, *args in formats_to_test:
        is_demo = args[0] if args else False
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"is_demo: {is_demo}")
        print(f"SSID: {ssid[:50]}...")
        
        try:
            # First validate
            print("Validating SSID...")
            is_valid = await validate_ssid(ssid)
            print(f"Validation result: {is_valid}")
            
            if is_valid:
                print(f"{name} is VALID! Trying to connect...")
                client = AsyncQuotexClient(ssid=ssid, is_demo=is_demo)
                connected = await client.connect()
                print(f"Connection result: {connected}")
                
                if connected:
                    print(f"SUCCESS with {name}!")
                    await client.disconnect()
                    return True, name, ssid, is_demo
            else:
                print(f"{name} validation FAILED")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n{'='*60}")
    print("All formats failed!")
    print("\nPossible issues:")
    print("1. Session expired on server side")
    print("2. Account needs re-authentication (2FA, CAPTCHA)")
    print("3. API-Quotex library version mismatch")
    print("4. WebSocket endpoint changed")
    
    return False, None, None, None

if __name__ == "__main__":
    asyncio.run(test_ssid_formats())
