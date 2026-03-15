import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, WilliamsRIndicator
from ta.trend import MACD, EMAIndicator, ADXIndicator, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class BacktestResult:
    """Results from backtesting a strategy"""
    total_trades: int
    wins: int
    losses: int
    accuracy: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    best_threshold: int
    win_rate_by_signal: Dict[str, float]


class SignalEngine:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.pattern_history = []
        self.optimal_threshold = 25
        self.weights = {
            'ema_trend': 40, 'macd': 40, 'rsi': 30, 'bollinger': 30,
            'ema_cross': 20, 'stoch_rsi': 20, 'adx': 20,
            'vwap': 25, 'ichimoku': 35, 'fibonacci': 25, 'williams_r': 20, 'pattern_ml': 50
        }

    def calculate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df is None or len(df) < 50:
            return {"signal": "NEUTRAL", "confidence": 50.0, "strength": "WEAK",
                    "price": 0.0, "stop_loss": 0.0, "take_profit": 0.0,
                    "risk_reward": 0.0, "indicators": {}}

        close = df["Close"]
        high  = df["High"]
        low   = df["Low"]

        # ── Standard Indicators ─────────────────────────────────────────────

        # RSI
        rsi_ind = RSIIndicator(close, window=self.settings.get("rsi_period", 14))
        df["RSI"] = rsi_ind.rsi()

        # MACD
        macd_ind = MACD(
            close,
            window_fast=self.settings.get("macd_fast", 12),
            window_slow=self.settings.get("macd_slow", 26),
            window_sign=self.settings.get("macd_signal", 9),
        )
        df["MACD"]        = macd_ind.macd()
        df["MACD_Signal"] = macd_ind.macd_signal()
        df["MACD_Hist"]   = macd_ind.macd_diff()

        # EMAs
        df["EMA_9"]  = EMAIndicator(close, window=self.settings.get("ema_fast",   9)).ema_indicator()
        df["EMA_21"] = EMAIndicator(close, window=self.settings.get("ema_medium", 21)).ema_indicator()
        df["EMA_50"] = EMAIndicator(close, window=self.settings.get("ema_slow",   50)).ema_indicator()

        # Bollinger Bands
        bb = BollingerBands(
            close,
            window=self.settings.get("bb_period", 20),
            window_dev=self.settings.get("bb_std", 2),
        )
        df["BBU"] = bb.bollinger_hband()
        df["BBL"] = bb.bollinger_lband()
        df["BBM"] = bb.bollinger_mavg()
        df["BB_Width"] = (df["BBU"] - df["BBL"]) / df["BBM"]

        # Stochastic
        stoch = StochasticOscillator(
            high, low, close,
            window=self.settings.get("stoch_k", 14),
            smooth_window=self.settings.get("stoch_d", 3),
        )
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = stoch.stoch_signal()

        # Stochastic RSI
        try:
            srsi = StochRSIIndicator(close, window=14, smooth1=3, smooth2=3)
            df["STOCH_RSI_K"] = srsi.stochrsi_k()
            df["STOCH_RSI_D"] = srsi.stochrsi_d()
        except Exception:
            df["STOCH_RSI_K"] = np.nan
            df["STOCH_RSI_D"] = np.nan

        # ATR
        df["ATR"] = AverageTrueRange(high, low, close, window=14).average_true_range()

        # ADX
        try:
            adx_ind = ADXIndicator(high, low, close, window=14)
            df["ADX"]    = adx_ind.adx()
            df["ADX_POS"] = adx_ind.adx_pos()
            df["ADX_NEG"] = adx_ind.adx_neg()
        except Exception:
            df["ADX"] = df["ADX_POS"] = df["ADX_NEG"] = np.nan

        # OBV
        try:
            volume = df["Volume"] if "Volume" in df.columns else pd.Series(0, index=df.index)
            obv_ind = OnBalanceVolumeIndicator(close, volume)
            df["OBV"] = obv_ind.on_balance_volume()
        except Exception:
            df["OBV"] = np.nan

        # ── NEW: Advanced Indicators ─────────────────────────────────────────

        # VWAP
        df["VWAP"] = self.calculate_vwap(df)

        # Ichimoku Cloud
        ichimoku = self.calculate_ichimoku(df)
        df["TENKAN_SEN"] = ichimoku['tenkan_sen']
        df["KIJUN_SEN"] = ichimoku['kijun_sen']
        df["SENKOU_A"] = ichimoku['senkou_span_a']
        df["SENKOU_B"] = ichimoku['senkou_span_b']

        # Williams %R
        try:
            williams = WilliamsRIndicator(high, low, close, lbp=14)
            df["WILLIAMS_R"] = williams.williams_r()
        except Exception:
            df["WILLIAMS_R"] = np.nan

        # Fibonacci Levels
        fib_levels = self.calculate_fibonacci_levels(df)

        # Pattern Detection
        patterns = self.detect_price_patterns(df)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # ── Enhanced Scoring System ─────────────────────────────────────────
        score = 0

        # 1. EMA Trend alignment
        if latest["EMA_9"] > latest["EMA_21"] > latest["EMA_50"]:
            score += self.weights['ema_trend']
        elif latest["EMA_9"] < latest["EMA_21"] < latest["EMA_50"]:
            score -= self.weights['ema_trend']

        # 2. MACD
        if latest["MACD"] > latest["MACD_Signal"] and latest["MACD_Hist"] > 0:
            score += self.weights['macd']
        elif latest["MACD"] < latest["MACD_Signal"] and latest["MACD_Hist"] < 0:
            score -= self.weights['macd']

        # 3. RSI
        rsi = latest["RSI"]
        if rsi < 30:
            score += self.weights['rsi']
        elif rsi > 70:
            score -= self.weights['rsi']
        elif 40 <= rsi < 50:
            score += self.weights['rsi'] * 0.33
        elif 50 < rsi <= 60:
            score -= self.weights['rsi'] * 0.33

        # 4. Bollinger Bands
        if latest["Close"] <= latest["BBL"]:
            score += self.weights['bollinger']
        elif latest["Close"] >= latest["BBU"]:
            score -= self.weights['bollinger']

        # 5. EMA 9 / 21 Cross
        if prev["EMA_9"] <= prev["EMA_21"] and latest["EMA_9"] > latest["EMA_21"]:
            score += self.weights['ema_cross']
        elif prev["EMA_9"] >= prev["EMA_21"] and latest["EMA_9"] < latest["EMA_21"]:
            score -= self.weights['ema_cross']

        # 6. Stochastic RSI
        srsi_k = latest.get("STOCH_RSI_K", np.nan)
        srsi_d = latest.get("STOCH_RSI_D", np.nan)
        if not np.isnan(srsi_k) and not np.isnan(srsi_d):
            if srsi_k < 0.2 and srsi_k > srsi_d:
                score += self.weights['stoch_rsi']
            elif srsi_k > 0.8 and srsi_k < srsi_d:
                score -= self.weights['stoch_rsi']

        # 7. ADX trend filter
        adx = latest.get("ADX", np.nan)
        if not np.isnan(adx) and adx > 25:
            adx_pos = latest.get("ADX_POS", np.nan)
            adx_neg = latest.get("ADX_NEG", np.nan)
            if not np.isnan(adx_pos) and not np.isnan(adx_neg):
                score += self.weights['adx'] if adx_pos > adx_neg else -self.weights['adx']

        # 8. VWAP
        vwap = latest.get("VWAP", np.nan)
        if not np.isnan(vwap):
            if latest["Close"] > vwap and latest["Close"] > latest["EMA_9"]:
                score += self.weights['vwap']
            elif latest["Close"] < vwap and latest["Close"] < latest["EMA_9"]:
                score -= self.weights['vwap']

        # 9. Ichimoku Cloud
        tenkan = latest.get("TENKAN_SEN", np.nan)
        kijun = latest.get("KIJUN_SEN", np.nan)
        senkou_a = latest.get("SENKOU_A", np.nan)
        senkou_b = latest.get("SENKOU_B", np.nan)
        if not np.isnan(tenkan) and not np.isnan(kijun):
            score += self.weights['ichimoku'] * 0.5 if tenkan > kijun else -self.weights['ichimoku'] * 0.5
            if not np.isnan(senkou_a) and not np.isnan(senkou_b):
                cloud_top, cloud_bottom = max(senkou_a, senkou_b), min(senkou_a, senkou_b)
                if latest["Close"] > cloud_top:
                    score += self.weights['ichimoku'] * 0.5
                elif latest["Close"] < cloud_bottom:
                    score -= self.weights['ichimoku'] * 0.5

        # 10. Williams %R
        williams_r = latest.get("WILLIAMS_R", np.nan)
        if not np.isnan(williams_r):
            if williams_r < -80:
                score += self.weights['williams_r']
            elif williams_r > -20:
                score -= self.weights['williams_r']

        # 11. Fibonacci Levels
        fib_pos = fib_levels['price_position']
        if fib_pos < 0.382:
            score += self.weights['fibonacci']
        elif fib_pos > 0.618:
            score -= self.weights['fibonacci']

        # 12. ML Pattern Recognition
        pattern_score = patterns.get('net_score', 0)
        pattern_confidence = patterns.get('confidence', 0)
        score += pattern_score * self.weights['pattern_ml'] * pattern_confidence

        # ── Signal & Confidence ─────────────────────────────────────────────
        threshold = self.optimal_threshold
        
        if score >= threshold:
            signal = "UP"
        elif score <= -threshold:
            signal = "DOWN"
        else:
            signal = "NEUTRAL"

        # Confidence calculation
        base_confidence = 50 + (abs(score) / 200 * 49)
        confidence = round(min(base_confidence, 99.0), 1)

        strength = "WEAK"
        if confidence >= 85:
            strength = "STRONG"
        elif confidence >= 70:
            strength = "MODERATE"

        # ── SL / TP with Fibonacci levels ─────────────────────────────────
        atr = latest["ATR"]
        price = latest["Close"]
        
        if signal == "UP":
            sl = max(price - (2 * atr), fib_levels['levels']['0.618'])
            tp = fib_levels['levels']['0.0']
        elif signal == "DOWN":
            sl = min(price + (2 * atr), fib_levels['levels']['0.382'])
            tp = fib_levels['levels']['1.0']
        else:
            sl = price * 0.99
            tp = price * 1.01

        rr = abs(tp - price) / abs(price - sl) if abs(price - sl) != 0 else 0

        # Store pattern for learning
        self.pattern_history.append({
            'timestamp': datetime.now().isoformat(),
            'patterns': patterns,
            'signal': signal,
            'score': score,
            'price': float(price)
        })

        return {
            "signal": signal,
            "confidence": confidence,
            "strength": strength,
            "score": score,
            "threshold": threshold,
            "price": float(price),
            "stop_loss": float(sl),
            "take_profit": float(tp),
            "risk_reward": round(rr, 2),
            "indicators": {
                "rsi": round(float(rsi), 2),
                "macd": round(float(latest["MACD"]), 6),
                "macd_hist": round(float(latest["MACD_Hist"]), 6),
                "ema9": round(float(latest["EMA_9"]), 6),
                "ema21": round(float(latest["EMA_21"]), 6),
                "ema50": round(float(latest["EMA_50"]), 6),
                "bb_upper": round(float(latest["BBU"]), 6),
                "bb_lower": round(float(latest["BBL"]), 6),
                "stoch_k": round(float(latest["STOCH_K"]), 2),
                "stoch_d": round(float(latest["STOCH_D"]), 2),
                "stoch_rsi_k": round(float(srsi_k), 4) if not np.isnan(srsi_k) else None,
                "adx": round(float(adx), 2) if not np.isnan(adx) else None,
                "vwap": round(float(vwap), 6) if not np.isnan(vwap) else None,
                "tenkan_sen": round(float(tenkan), 6) if not np.isnan(tenkan) else None,
                "kijun_sen": round(float(kijun), 6) if not np.isnan(kijun) else None,
                "williams_r": round(float(williams_r), 2) if not np.isnan(williams_r) else None,
                "fib_position": round(fib_pos, 3),
            },
            "patterns": {k: v for k, v in patterns.items() if k not in ['net_score', 'confidence'] and isinstance(v, dict) and v.get('detected', False)},
            "fibonacci_levels": {k: round(v, 6) for k, v in fib_levels['levels'].items()}
        }

    # ── Helper Methods ────────────────────────────────────────────────────

    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Volume Weighted Average Price"""
        volume = df.get("Volume", pd.Series(1, index=df.index))
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap

    def calculate_ichimoku(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Ichimoku Cloud indicator"""
        high, low, close = df["High"], df["Low"], df["Close"]
        tenkan_sen = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
        kijun_sen = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        senkou_span_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
        chikou_span = close.shift(-26)
        return {'tenkan_sen': tenkan_sen, 'kijun_sen': kijun_sen, 'senkou_span_a': senkou_span_a,
                'senkou_span_b': senkou_span_b, 'chikou_span': chikou_span}

    def calculate_fibonacci_levels(self, df: pd.DataFrame, lookback: int = 50) -> Dict[str, Any]:
        """Calculate Fibonacci retracement levels"""
        recent = df.tail(lookback)
        high, low = recent["High"].max(), recent["Low"].min()
        diff = high - low
        current = df["Close"].iloc[-1]
        levels = {'0.0': high, '0.236': high - 0.236 * diff, '0.382': high - 0.382 * diff,
                  '0.5': high - 0.5 * diff, '0.618': high - 0.618 * diff, '0.786': high - 0.786 * diff, '1.0': low}
        price_position = (high - current) / diff if diff > 0 else 0.5
        return {'levels': levels, 'price_position': price_position}

    def detect_price_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Pattern detection for reversal signals"""
        patterns = {
            'bullish_engulfing': self._detect_bullish_engulfing(df),
            'bearish_engulfing': self._detect_bearish_engulfing(df),
            'hammer': self._detect_hammer(df),
            'shooting_star': self._detect_shooting_star(df),
            'morning_star': self._detect_morning_star(df),
            'evening_star': self._detect_evening_star(df),
        }
        bullish = sum(1 for p in patterns.values() if p.get('bullish'))
        bearish = sum(1 for p in patterns.values() if p.get('bearish'))
        patterns['net_score'] = bullish - bearish
        patterns['confidence'] = max(bullish, bearish) / max(1, bullish + bearish)
        return patterns

    def _detect_bullish_engulfing(self, df: pd.DataFrame) -> Dict:
        if len(df) < 2: return {'detected': False}
        prev, curr = df.iloc[-2], df.iloc[-1]
        if prev['Close'] < prev['Open'] and curr['Close'] > curr['Open'] and curr['Open'] < prev['Close'] and curr['Close'] > prev['Open']:
            return {'detected': True, 'bullish': True, 'strength': 0.8}
        return {'detected': False}

    def _detect_bearish_engulfing(self, df: pd.DataFrame) -> Dict:
        if len(df) < 2: return {'detected': False}
        prev, curr = df.iloc[-2], df.iloc[-1]
        if prev['Close'] > prev['Open'] and curr['Close'] < curr['Open'] and curr['Open'] > prev['Close'] and curr['Close'] < prev['Open']:
            return {'detected': True, 'bearish': True, 'strength': 0.8}
        return {'detected': False}

    def _detect_hammer(self, df: pd.DataFrame) -> Dict:
        if len(df) < 5: return {'detected': False}
        curr = df.iloc[-1]
        body = abs(curr['Close'] - curr['Open'])
        lower_wick = min(curr['Open'], curr['Close']) - curr['Low']
        upper_wick = curr['High'] - max(curr['Open'], curr['Close'])
        recent_lows = df['Low'].tail(5).values
        if lower_wick > body * 2 and upper_wick < body * 0.5 and recent_lows[-1] <= min(recent_lows[:-1]) * 1.001:
            return {'detected': True, 'bullish': True, 'strength': 0.75}
        return {'detected': False}

    def _detect_shooting_star(self, df: pd.DataFrame) -> Dict:
        if len(df) < 5: return {'detected': False}
        curr = df.iloc[-1]
        body = abs(curr['Close'] - curr['Open'])
        upper_wick = curr['High'] - max(curr['Open'], curr['Close'])
        lower_wick = min(curr['Open'], curr['Close']) - curr['Low']
        recent_highs = df['High'].tail(5).values
        if upper_wick > body * 2 and lower_wick < body * 0.5 and recent_highs[-1] >= max(recent_highs[:-1]) * 0.999:
            return {'detected': True, 'bearish': True, 'strength': 0.75}
        return {'detected': False}

    def _detect_morning_star(self, df: pd.DataFrame) -> Dict:
        if len(df) < 3: return {'detected': False}
        first, second, third = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        first_bearish = first['Open'] > first['Close']
        second_body = abs(second['Open'] - second['Close'])
        first_body = abs(first['Open'] - first['Close'])
        third_bullish = third['Close'] > third['Open']
        if first_bearish and second_body < first_body * 0.3 and third_bullish and third['Close'] > (first['Open'] + first['Close']) / 2:
            return {'detected': True, 'bullish': True, 'strength': 0.9}
        return {'detected': False}

    def _detect_evening_star(self, df: pd.DataFrame) -> Dict:
        if len(df) < 3: return {'detected': False}
        first, second, third = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        first_bullish = first['Close'] > first['Open']
        second_body = abs(second['Open'] - second['Close'])
        first_body = abs(first['Open'] - first['Close'])
        third_bearish = third['Close'] < third['Open']
        if first_bullish and second_body < first_body * 0.3 and third_bearish and third['Close'] < (first['Open'] + first['Close']) / 2:
            return {'detected': True, 'bearish': True, 'strength': 0.9}
        return {'detected': False}

    # ── Backtesting Methods ─────────────────────────────────────────────

    def backtest_thresholds(self, historical_data: pd.DataFrame, thresholds: List[int] = None) -> Dict[str, Any]:
        """Backtest different signal thresholds"""
        if thresholds is None:
            thresholds = list(range(10, 71, 5))
        
        results = []
        for threshold in thresholds:
            trades = []
            for i in range(50, len(historical_data) - 10):
                window = historical_data.iloc[:i+1]
                signal_data = self.calculate_signals(window)
                if signal_data['signal'] in ['UP', 'DOWN'] and signal_data['confidence'] >= 50:
                    future = historical_data.iloc[i+1:i+6]
                    entry = signal_data['price']
                    exit_price = future['Close'].iloc[-1]
                    profit = exit_price - entry if signal_data['signal'] == 'UP' else entry - exit_price
                    trades.append({'profit': profit, 'outcome': 'win' if profit > 0 else 'loss', 'signal': signal_data['signal']})
            
            if trades:
                wins = sum(1 for t in trades if t['outcome'] == 'win')
                accuracy = wins / len(trades)
                results.append({'threshold': threshold, 'accuracy': accuracy, 'total_trades': len(trades)})
        
        if results:
            best = max(results, key=lambda x: x['accuracy'])
            self.optimal_threshold = best['threshold']
            return {'best_threshold': best['threshold'], 'accuracy': best['accuracy'], 'total_trades': best['total_trades'], 'all_results': results}
        return {'best_threshold': 25, 'accuracy': 0, 'total_trades': 0}

    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get pattern detection statistics"""
        if not self.pattern_history:
            return {"message": "No patterns recorded"}
        recent = self.pattern_history[-100:]
        return {
            "total_signals": len(self.pattern_history),
            "signal_distribution": {
                "UP": sum(1 for e in recent if e['signal'] == 'UP'),
                "DOWN": sum(1 for e in recent if e['signal'] == 'DOWN'),
                "NEUTRAL": sum(1 for e in recent if e['signal'] == 'NEUTRAL')
            },
            "avg_score": np.mean([e['score'] for e in recent])
        }

    def export_patterns(self, filename: str = "pattern_history.json"):
        """Export pattern history for ML training"""
        with open(filename, 'w') as f:
            json.dump(self.pattern_history, f, indent=2, default=str)
        return filename
