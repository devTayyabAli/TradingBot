from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SignalSettings(BaseModel):
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    ema_fast: int = 9
    ema_medium: int = 21
    ema_slow: int = 50
    stoch_k: int = 14
    stoch_d: int = 3
    bb_period: int = 20
    bb_std: int = 2

class SignalResponse(BaseModel):
    asset: str
    timeframe: str
    signal: str  # UP, DOWN, NEUTRAL
    confidence: float
    strength: str  # STRONG, MODERATE, WEAK
    price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    timestamp: datetime
    indicators: dict

class SignalHistory(BaseModel):
    id: str
    timestamp: datetime
    asset: str
    signal: str
    price: float
    result: str = "pending"  # pending, win, loss
