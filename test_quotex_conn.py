import asyncio
import sys
import os
import json

# Add api_quotex to path
API_QUOTEX_PATH = os.path.join(os.path.dirname(__file__), "..", "API-Quotex-main")
if API_QUOTEX_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(API_QUOTEX_PATH))

from api_quotex.client import AsyncQuotexClient

async def test_connection():
    # Read session
    session_path = os.path.join(API_QUOTEX_PATH, "sessions", "session.json")
    with open(session_path) as f:
        session_data = json.load(f)
    
    ssid = session_data.get("ssid", "")
    is_demo = session_data.get("is_demo", True)
    
    print(f"Testing connection with SSID: {ssid[:40]}...")
    print(f"is_demo: {is_demo}")
    print(f"SSID length: {len(ssid)}")
    
    try:
        client = AsyncQuotexClient(ssid=ssid, is_demo=is_demo)
        connected = await client.connect()
        print(f"\nConnection result: {connected}")
        
        if connected:
            print("SUCCESS! Connected to Quotex.")
            # Try to get balance
            balance = await client.get_balance()
            print(f"Balance: {balance}")
            await client.disconnect()
        else:
            print("FAILED to connect.")
            print("\nPossible reasons:")
            print("1. SSID expired (sessions expire within minutes)")
            print("2. Wrong format (need Socket.IO frame)")
            print("3. Network/DNS issues")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
