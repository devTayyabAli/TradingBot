# Simplified data fetcher for Railway deployment
# Uses Yahoo Finance when Quotex API is not available

import yfinance as yf
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class DataFetcher:
    def __init__(self):
        self.connected = False
        
    async def connect(self) -> bool:
        # Simulate connection for Railway
        self.connected = True
        print("[DataFetcher] Using Yahoo Finance data source")
        return True
        
    async def fetch_data(self, symbol: str, timeframe: str = "1m", count: int = 100) -> Optional[pd.DataFrame]:
        try:
            # Convert symbol for Yahoo Finance
            yf_symbol = symbol.replace('_otc', '=X')
            
            # Map timeframes to Yahoo intervals
            interval_map = {
                '1s': '1m',
                '5s': '1m', 
                '30s': '1m',
                '1m': '1m',
                '5m': '5m',
                '15m': '15m'
            }
            interval = interval_map.get(timeframe, '1m')
            
            # Fetch data
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(period="7d", interval=interval)
            
            if data.empty:
                return None
                
            # Process data
            df = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            
            # Return last N candles
            return df.tail(count)
            
        except Exception as e:
            print(f"[DataFetcher] Error fetching {symbol}: {e}")
            return None

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Return the latest Close price for given asset."""
        try:
            yf_symbol = symbol.replace('_otc', '=X')
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if data is not None and not data.empty:
                return float(data["Close"].iloc[-1])
            return None
        except Exception as e:
            print(f"[DataFetcher] Error getting price for {symbol}: {e}")
            return None

    async def get_available_assets(self) -> Dict[str, Any]:
        """Return basic available assets."""
        return {
            "EURUSD_otc": {"name": "EUR/USD OTC", "payout": 92, "is_otc": True, "is_open": True},
            "GBPUSD_otc": {"name": "GBP/USD OTC", "payout": 92, "is_otc": True, "is_open": True},
            "USDJPY_otc": {"name": "USD/JPY OTC", "payout": 92, "is_otc": True, "is_open": True},
            "AUDUSD_otc": {"name": "AUD/USD OTC", "payout": 92, "is_otc": True, "is_open": True},
            "USDCAD_otc": {"name": "USD/CAD OTC", "payout": 92, "is_otc": True, "is_open": True},
            "GOLD_otc": {"name": "Gold OTC", "payout": 95, "is_otc": True, "is_open": True},
            "OIL_otc": {"name": "Crude Oil OTC", "payout": 85, "is_otc": True, "is_open": True},
            "BTCUSD_otc": {"name": "BTC/USD OTC", "payout": 90, "is_otc": True, "is_open": True},
            "ETHUSD_otc": {"name": "ETH/USD OTC", "payout": 88, "is_otc": True, "is_open": True},
            "SP500_otc": {"name": "S&P 500 OTC", "payout": 92, "is_otc": True, "is_open": True},
            "NAS100_otc": {"name": "NASDAQ 100 OTC", "payout": 92, "is_otc": True, "is_open": True}
        }

# Create singleton instance
quotex_fetcher = DataFetcher()
