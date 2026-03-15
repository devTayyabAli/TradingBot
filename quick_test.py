import asyncio
import json
import os
import sys

API_QUOTEX_PATH = r'd:\TradingBot\API-Quotex-main'
if API_QUOTEX_PATH not in sys.path:
    sys.path.insert(0, API_QUOTEX_PATH)

# Try with demo mode since real account keeps failing
session = {'ssid': 'Y62R6vFomrGvuCQ27jP3qcIoaD8ZHM1OPw9VjyZ4', 'is_demo': True}

from api_quotex.client import AsyncQuotexClient

async def test():
    print('Testing SSID:', session['ssid'][:30], '...')
    print('is_demo:', session['is_demo'])
    
    try:
        client = AsyncQuotexClient(ssid=session['ssid'], is_demo=session['is_demo'])
        print('Client created')
        connected = await client.connect()
        print('Connected:', connected)
        if connected:
            print('SUCCESS!')
            await client.disconnect()
        else:
            print('Connection failed')
    except Exception as e:
        print('Error:', e)
        import traceback
        traceback.print_exc()

asyncio.run(test())
