"""
Alternative data fetcher using Yahoo Finance for live forex data
Falls back to this when Quotex connection fails
"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional

class YahooDataFetcher:
    """Fetch live forex data from Yahoo Finance"""
    
    # Map common forex pairs to Yahoo Finance symbols
    ASSET_MAP = {
        'EURUSD': 'EURUSD=X',
        'EURUSD_otc': 'EURUSD=X',
        'GBPUSD': 'GBPUSD=X',
        'GBPUSD_otc': 'GBPUSD=X',
        'USDJPY': 'USDJPY=X',
        'USDJPY_otc': 'USDJPY=X',
        'AUDUSD': 'AUDUSD=X',
        'AUDUSD_otc': 'AUDUSD=X',
        'USDCAD': 'USDCAD=X',
        'USDCAD_otc': 'USDCAD=X',
        'USDCHF': 'USDCHF=X',
        'USDCHF_otc': 'USDCHF=X',
        'NZDUSD': 'NZDUSD=X',
        'NZDUSD_otc': 'NZDUSD=X',
        'EURGBP': 'EURGBP=X',
        'EURGBP_otc': 'EURGBP=X',
        'GBPJPY': 'GBPJPY=X',
        'GBPJPY_otc': 'GBPJPY=X',
        'EURJPY': 'EURJPY=X',
        'EURJPY_otc': 'EURJPY=X',
        'Gold': 'GC=F',
        'Gold_otc': 'GC=F',
        'Silver': 'SI=F',
        'Silver_otc': 'SI=F',
        'BTC': 'BTC-USD',
        'BTC_otc': 'BTC-USD',
        'ETH': 'ETH-USD',
        'ETH_otc': 'ETH-USD',
    }
    
    def fetch_data(self, asset: str, timeframe: str = "1m", count: int = 100) -> Optional[pd.DataFrame]:
        """Fetch data from Yahoo Finance"""
        try:
            symbol = self.ASSET_MAP.get(asset, asset)
            
            # Map timeframe to Yahoo interval
            interval_map = {
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '4h': '1h',  # Yahoo doesn't have 4h, use 1h
                '1d': '1d',
            }
            interval = interval_map.get(timeframe, '1m')
            
            # Calculate period
            period_map = {
                '1m': '5d',
                '5m': '10d',
                '15m': '20d',
                '30m': '30d',
                '1h': '60d',
                '4h': '60d',
                '1d': '1y',
            }
            period = period_map.get(timeframe, '5d')
            
            print(f"[YahooFinance] Fetching {symbol} ({interval})...")
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"[YahooFinance] No data returned for {symbol}")
                return None
            
            # Rename columns to match expected format
            df = df.rename(columns={
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
            # Get last N candles
            df = df.tail(count)
            
            print(f"[YahooFinance] Got {len(df)} candles for {asset}")
            return df
            
        except Exception as e:
            print(f"[YahooFinance] Error fetching {asset}: {e}")
            return None
    
    def get_current_price(self, asset: str) -> float:
        """Get current price for asset"""
        try:
            symbol = self.ASSET_MAP.get(asset, asset)
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('regularMarketPrice', 0.0)
        except Exception as e:
            print(f"[YahooFinance] Error getting price for {asset}: {e}")
            return 0.0
