#!/usr/bin/env python3
"""Debug script to find 500 error cause"""
import sys
import os

# Add paths
sys.path.insert(0, r'd:\TradingBot\backend')
sys.path.insert(0, r'd:\TradingBot\API-Quotex-main')

print("=" * 60)
print("DEBUG: Finding 500 Error Cause")
print("=" * 60)

# Test 1: Imports
print("\n1. Testing imports...")
try:
    import pandas as pd
    import numpy as np
    from ultra_conservative_engine import UltraConservativeSignalEngine
    from data_fetcher import quotex_fetcher
    from yahoo_fetcher import YahooDataFetcher
    print("   ✓ All imports successful")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Create engine
print("\n2. Creating UltraConservativeSignalEngine...")
try:
    engine = UltraConservativeSignalEngine({})
    print("   ✓ Engine created")
except Exception as e:
    print(f"   ✗ Engine creation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Fetch data
print("\n3. Fetching data from Yahoo Finance...")
try:
    import asyncio
    
    async def fetch_data():
        yahoo = YahooDataFetcher()
        df = yahoo.fetch_data('EURUSD_otc', timeframe='1m', count=150)
        return df
    
    df = asyncio.run(fetch_data())
    
    if df is None:
        print("   ✗ Data is None")
        sys.exit(1)
    
    print(f"   ✓ Data fetched: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   First row: {df.iloc[0].to_dict()}")
    print(f"   Last row: {df.iloc[-1].to_dict()}")
    
except Exception as e:
    print(f"   ✗ Data fetch error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Calculate signals
print("\n4. Calculating signals...")
try:
    result = engine.calculate_signals(df)
    print(f"   ✓ Signal calculated: {result.get('signal')}")
    print(f"   Confidence: {result.get('confidence')}")
    print(f"   Strength: {result.get('strength')}")
    print(f"   Full result keys: {list(result.keys())}")
except Exception as e:
    print(f"   ✗ Signal calculation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("SUCCESS: All tests passed!")
print("=" * 60)
