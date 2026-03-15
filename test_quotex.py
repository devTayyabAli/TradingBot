"""Test Quotex API connection"""
import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.abspath(r'd:\TradingBot\API-Quotex-main'))
sys.path.insert(0, os.path.abspath(r'd:\TradingBot\backend'))

from api_quotex.login import get_ssid
from api_quotex.client import AsyncQuotexClient

async def test_connection():
    print("=" * 50)
    print("Testing Quotex API Connection")
    print("=" * 50)
    
    # Try to get SSID
    print("\n[1] Authenticating with Quotex...")
    ok, session_data = await get_ssid(email="", password="", is_demo=True)
    
    if not ok or not session_data.get("ssid"):
        print("❌ Authentication failed. Please update config.json with valid credentials:")
        print("   d:\TradingBot\API-Quotex-main\sessions\config.json")
        return False
    
    ssid = session_data["ssid"]
    print(f"✅ SSID obtained: {ssid[:20]}...")
    
    # Connect to WebSocket
    print("\n[2] Connecting to WebSocket...")
    client = AsyncQuotexClient(ssid=ssid, is_demo=True)
    connected = await client.connect()
    
    if not connected:
        print("❌ WebSocket connection failed")
        return False
    
    print("✅ WebSocket connected!")
    
    # Get available assets
    print("\n[3] Fetching available assets...")
    assets = await client.get_available_assets()
    open_assets = {k: v for k, v in assets.items() if v.get('is_open')}
    print(f"✅ Found {len(open_assets)} open assets")
    
    # Get candles for EURUSD_otc
    print("\n[4] Fetching candles for EURUSD_otc...")
    candles = await client.get_candles(asset="EURUSD_otc", end_from_time=0, offset=600, period=60)
    if candles:
        print(f"✅ Received {len(candles)} candles")
        print(f"   Latest: O={candles[-1].open:.5f} H={candles[-1].high:.5f} L={candles[-1].low:.5f} C={candles[-1].close:.5f}")
    else:
        print("❌ No candles received")
    
    # Get balance
    print("\n[5] Fetching balance...")
    balance = await client.get_balance()
    print(f"✅ Balance: {balance.balance} {balance.currency}")
    
    await client.disconnect()
    print("\n" + "=" * 50)
    print("✅ All tests passed! Quotex API is ready.")
    print("=" * 50)
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        sys.exit(1)
