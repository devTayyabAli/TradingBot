"""
QuotexDataFetcher – replaces yfinance with the live Quotex WebSocket API.

FIRST RUN SETUP:
  1. Run `pip install -e d:/TradingBot/API-Quotex-main` (or ensure dependencies are installed).
  2. Make sure `d:/TradingBot/API-Quotex-main/sessions/config.json` contains:
       { "email": "your@email.com", "password": "yourpassword" }
  3. On first start, a Chromium browser will open to log in and save session.json.
     Subsequent starts reuse the saved session automatically.
"""
import sys
import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import pandas as pd

# Add api_quotex to path
API_QUOTEX_PATH = os.path.join(os.path.dirname(__file__), "..", "API-Quotex-main")
if API_QUOTEX_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(API_QUOTEX_PATH))

from api_quotex.client import AsyncQuotexClient
from api_quotex.login import get_ssid
from api_quotex.config import Config
from yahoo_fetcher import YahooDataFetcher

# Timeframe label → seconds
TIMEFRAME_MAP: Dict[str, int] = {
    "1s":  5,    # Quotex minimum is 5s
    "5s":  5,
    "30s": 30,
    "1m":  60,
    "5m":  300,
    "15m": 900,
    "30m": 1800,
    "1h":  3600,
    "4h":  14400,
    "1d":  86400,
}


class QuotexDataFetcher:
    """Singleton Quotex API client that provides OHLC data for the signal engine.
    Falls back to demo mode if connection fails."""

    def __init__(self):
        self._client: Optional[AsyncQuotexClient] = None
        self._connected: bool = False
        self._demo_mode: bool = False
        self._demo_data_cache: Dict[str, pd.DataFrame] = {}

    def _generate_demo_candles(self, asset: str, timeframe: str, count: int) -> pd.DataFrame:
        """Generate realistic demo OHLC data with trends for testing."""
        import numpy as np
        
        period_secs = TIMEFRAME_MAP.get(timeframe, 60)
        now = datetime.now(timezone.utc)
        
        # Generate timestamps
        timestamps = [now - timedelta(seconds=period_secs * i) for i in range(count, 0, -1)]
        
        # Base price by asset
        if "EURUSD" in asset:
            base_price = 1.0850
            volatility = 0.0003
        elif "GBPUSD" in asset:
            base_price = 1.2650
            volatility = 0.0004
        elif "JPY" in asset:
            base_price = 149.50
            volatility = 0.05
        elif "Gold" in asset:
            base_price = 2035.0
            volatility = 2.0
        elif "BTC" in asset:
            base_price = 43200.0
            volatility = 150.0
        else:
            base_price = 1.2500
            volatility = 0.0003
        
        # Generate trending price data with alternating strong trends
        # Use random seed based on time for variety
        np.random.seed(int(datetime.now().timestamp()) % 10000)
        
        # Decide trend direction randomly but strongly (70% strong trend, 30% neutral)
        trend_type = np.random.choice(['strong_up', 'strong_down', 'neutral'], p=[0.4, 0.4, 0.2])
        
        if trend_type == 'strong_up':
            trend_direction = 1
            trend_strength = np.random.uniform(2.0, 4.0)  # Very strong upward
        elif trend_type == 'strong_down':
            trend_direction = -1
            trend_strength = np.random.uniform(2.0, 4.0)  # Very strong downward
        else:
            trend_direction = np.random.choice([-1, 1])
            trend_strength = np.random.uniform(0.3, 0.8)  # Weak/neutral
        
        prices = [base_price]
        
        for i in range(count - 1):
            # Strong directional bias
            drift = trend_direction * volatility * trend_strength
            noise = np.random.normal(0, volatility * 0.3)
            change = drift + noise
            
            new_price = prices[-1] + change
            
            # Keep within bounds
            if new_price < base_price * 0.97:
                new_price = base_price * 0.97 + abs(np.random.normal(0, volatility))
            elif new_price > base_price * 1.03:
                new_price = base_price * 1.03 - abs(np.random.normal(0, volatility))
                
            prices.append(new_price)
        
        # Generate OHLC from close prices
        rows = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            # Create realistic OHLC around close
            body = abs(np.random.normal(0, volatility * 0.5))
            wick = abs(np.random.normal(0, volatility * 0.8))
            
            if i > 0 and close > prices[i-1]:  # Bullish candle
                open_p = close - body
                high = close + wick
                low = open_p - wick * 0.3
            else:  # Bearish or first candle
                open_p = close + body
                high = open_p + wick
                low = close - wick * 0.3
            
            # Ensure OHLC consistency
            high = max(high, open_p, close)
            low = min(low, open_p, close)
            
            rows.append({
                "Datetime": ts,
                "Open": open_p,
                "High": high,
                "Low": low,
                "Close": close,
                "Volume": float(np.random.randint(100, 10000)),
            })
        
        df = pd.DataFrame(rows).set_index("Datetime").sort_index()
        return df

    def enable_demo_mode(self):
        """Enable demo mode with simulated data."""
        self._demo_mode = True
        self._connected = True
        print("[QuotexDataFetcher] DEMO MODE ENABLED - Using simulated data")

    @property
    def is_demo_mode(self) -> bool:
        return self._demo_mode

    async def connect(self) -> bool:
        """
        Initialise the Quotex WebSocket client.
        Falls back to demo mode if connection fails.
        """
        try:
            # Use absolute path to API-Quotex-main/sessions
            sessions_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "API-Quotex-main", "sessions")
 )
            config_file = os.path.join(sessions_path, "config.json")
            
            # Read config.json directly
            if not os.path.exists(config_file):
                print(f"[QuotexDataFetcher] Config file not found: {config_file}")
                return False
                
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            email = config_data.get("email", "")
            password = config_data.get("password", "")

            if not email or not password:
                print(
                    "[QuotexDataFetcher] No email/password in config.json. "
                    "Please create API-Quotex-main/sessions/config.json with "
                    '{"email": "you@example.com", "password": "yourpassword"}'
                )
                return False

            print(f"[QuotexDataFetcher] Authenticating with Quotex... (email: {email[:5]}...)")
            
            # SKIP session reuse - always get fresh session via browser
            # This ensures we get a valid, non-expired session
            print("[QuotexDataFetcher] Getting fresh session via browser...")
            
            # Try browser automation for LIVE mode (is_demo=False)
            ok, session_data = await get_ssid(email=email, password=password, is_demo=False)
            if ok and session_data.get("ssid"):
                ssid = session_data["ssid"]
                print(f"[QuotexDataFetcher] Got fresh SSID via browser: {ssid[:40]}...")
                
                # Save the fresh session
                with open(session_file, "w", encoding="utf-8") as f:
                    json.dump({"ssid": ssid, "is_demo": False}, f)
                
                self._client = AsyncQuotexClient(ssid=ssid, is_demo=False)
                connected = await self._client.connect()
                
                if connected:
                    self._connected = True
                    print("[QuotexDataFetcher] Connected to LIVE Quotex WebSocket!")
                    return True
                else:
                    print("[QuotexDataFetcher] Fresh session failed, falling back to demo...")
            if not ok or not session_data.get("ssid"):
                print(f"[QuotexDataFetcher] Browser automation failed.")
                print(f"[QuotexDataFetcher] Enabling DEMO MODE for testing...")
                self.enable_demo_mode()
                return True  # Return True so app starts in demo mode

            ssid = session_data["ssid"]
            self._client = AsyncQuotexClient(ssid=ssid, is_demo=True)
            connected = await self._client.connect()

            if connected:
                self._connected = True
                print("[QuotexDataFetcher] Connected to Quotex WebSocket ✅")
            else:
                print("[QuotexDataFetcher] Failed to connect to Quotex WebSocket ❌")

            return connected

        except Exception as e:
            print(f"[QuotexDataFetcher] Connection error: {e}")
            return False

    async def disconnect(self):
        """Cleanly disconnect from Quotex WebSocket."""
        if self._client and self._connected:
            await self._client.disconnect()
            self._connected = False
            print("[QuotexDataFetcher] Disconnected from Quotex WebSocket.")

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None and self._client.is_connected

    async def fetch_data(
        self,
        asset: str,
        timeframe: str = "1m",
        count: int = 100,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC candles from Yahoo Finance (real data) or demo data.
        Returns DataFrame compatible with SignalEngine (columns: Open, High, Low, Close, Volume).
        """
        # Try Yahoo Finance first for real market data
        try:
            yahoo = YahooDataFetcher()
            df = yahoo.fetch_data(asset, timeframe=timeframe, count=count)
            if df is not None and not df.empty:
                print(f"[DataFetcher] Yahoo Finance data for {asset}: {len(df)} candles")
                return df
        except Exception as e:
            print(f"[DataFetcher] Yahoo Finance failed: {e}")
        
        # Fallback to demo mode if Yahoo fails
        if self._demo_mode:
            cache_key = f"{asset}_{timeframe}"
            if len(self._demo_data_cache) > 10:
                self._demo_data_cache.clear()
            if cache_key not in self._demo_data_cache:
                self._demo_data_cache[cache_key] = self._generate_demo_candles(asset, timeframe, count)
            print(f"[DataFetcher] Using demo data for {asset}: {count} candles")
            return self._demo_data_cache[cache_key]
        
        # Try Quotex if connected
        if self.is_connected:
            try:
                period_secs = TIMEFRAME_MAP.get(timeframe, 60)
                candles = await self._client.get_candles(
                    asset=asset,
                    end_from_time=0,
                    offset=period_secs * count,
                    period=period_secs,
                )
                if candles:
                    rows = []
                    for c in candles:
                        try:
                            rows.append({
                                "Datetime": datetime.fromtimestamp(
                                    c.timestamp.timestamp() if hasattr(c.timestamp, "timestamp") else float(c.timestamp),
                                    tz=timezone.utc,
                                ),
                                "Open": float(c.open),
                                "High": float(c.high),
                                "Low": float(c.low),
                                "Close": float(c.close),
                                "Volume": 0.0,
                            })
                        except Exception:
                            continue
                    if rows:
                        df = pd.DataFrame(rows).set_index("Datetime").sort_index()
                        return df
            except Exception as e:
                print(f"[DataFetcher] Quotex fetch error: {e}")
        
        # Final fallback to demo
        print(f"[DataFetcher] All sources failed, using demo data for {asset}")
        return self._generate_demo_candles(asset, timeframe, count)

    async def get_current_price(self, asset: str) -> Optional[float]:
        """Return the latest Close price for the given asset."""
        df = await self.fetch_data(asset, timeframe="1m", count=5)
        if df is not None and not df.empty:
            return float(df["Close"].iloc[-1])
        return None

    async def get_available_assets(self) -> Dict[str, Any]:
        """Return all available Quotex assets with payout info."""
        if self._demo_mode:
            # Return sample assets for demo mode
            return {
                "EURUSD_otc": {"name": "EUR/USD OTC", "payout": 92, "is_otc": True, "is_open": True},
                "GBPUSD_otc": {"name": "GBP/USD OTC", "payout": 92, "is_otc": True, "is_open": True},
                "USDJPY_otc": {"name": "USD/JPY OTC", "payout": 90, "is_otc": True, "is_open": True},
                "AUDUSD_otc": {"name": "AUD/USD OTC", "payout": 90, "is_otc": True, "is_open": True},
                "Gold_otc": {"name": "Gold OTC", "payout": 85, "is_otc": True, "is_open": True},
                "BTCUSD_otc": {"name": "Bitcoin OTC", "payout": 80, "is_otc": True, "is_open": True},
            }
        if not self.is_connected:
            return {}
        try:
            return await self._client.get_available_assets()
        except Exception as e:
            print(f"[QuotexDataFetcher] get_available_assets error: {e}")
            return {}


# Singleton instance shared across the FastAPI app
quotex_fetcher = QuotexDataFetcher()
