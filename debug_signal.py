import sys
sys.path.insert(0, r'd:\TradingBot\backend')
sys.path.insert(0, r'd:\TradingBot\API-Quotex-main')

import asyncio
from data_fetcher import quotex_fetcher
from ultra_conservative_engine import UltraConservativeSignalEngine

async def test():
    try:
        df = await quotex_fetcher.fetch_data('EURUSD_otc', timeframe='1m', count=150)
        print(f"Data shape: {df.shape if df is not None else None}")
        if df is not None:
            engine = UltraConservativeSignalEngine({})
            result = engine.calculate_signals(df)
            print(f"Signal: {result.get('signal')}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Strength: {result.get('strength')}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
