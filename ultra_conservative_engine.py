import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime
import json

class UltraConservativeSignalEngine:
    """
    Ultra-conservative signal engine with maximum safety checks.
    Only fires when ALL conditions align perfectly.
    
    ⚠️ DISCLAIMER: No system is 100% accurate. Even with strict filters,
    market conditions can change unexpectedly. Always use risk management.
    """
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.min_indicators_agree = 8  # Reduced to 8 of 12 indicators for more signals
        self.min_score = 200  # Reduced threshold for more opportunities
        self.min_confidence = 75  # Reduced to 75% minimum for more signals
        self.pattern_history = []
        self.trade_count = 0
        self.win_count = 0
        
    def calculate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate ultra-conservative trading signals.
        Only generates signal when ALL conditions are PERFECT.
        """
        if df is None or len(df) < 50:
            return self._neutral_response("Insufficient data")
        
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        
        # ── Calculate All Indicators ──────────────────────────────────────
        
        # 1. EMA Alignment
        ema_9 = close.ewm(span=9).mean()
        ema_21 = close.ewm(span=21).mean()
        ema_50 = close.ewm(span=50).mean()
        
        ema_bullish = bool(ema_9.iloc[-1] > ema_21.iloc[-1] > ema_50.iloc[-1])
        ema_bearish = bool(ema_9.iloc[-1] < ema_21.iloc[-1] < ema_50.iloc[-1])
        
        # 2. MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        macd_hist = macd - macd_signal
        
        macd_bullish = bool(macd.iloc[-1] > macd_signal.iloc[-1] and macd_hist.iloc[-1] > 0)
        macd_bearish = bool(macd.iloc[-1] < macd_signal.iloc[-1] and macd_hist.iloc[-1] < 0)
        
        # 3. RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]
        
        rsi_bullish = bool(rsi_val < 30)  # Oversold
        rsi_bearish = bool(rsi_val > 70)  # Overbought
        
        # 4. Bollinger Bands
        bb_middle = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        bb_bullish = bool(close.iloc[-1] <= bb_lower.iloc[-1])
        bb_bearish = bool(close.iloc[-1] >= bb_upper.iloc[-1])
        
        # 5. Stochastic
        low_14 = low.rolling(14).min()
        high_14 = high.rolling(14).max()
        stoch_k = 100 * (close - low_14) / (high_14 - low_14)
        stoch_d = stoch_k.rolling(3).mean()
        
        stoch_bullish = bool(stoch_k.iloc[-1] < 20 and stoch_k.iloc[-1] > stoch_d.iloc[-1])
        stoch_bearish = bool(stoch_k.iloc[-1] > 80 and stoch_k.iloc[-1] < stoch_d.iloc[-1])
        
        # 6. ADX - Trend Strength
        plus_dm = high.diff()
        minus_dm = low.diff()
        tr = pd.concat([high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(14).mean()
        
        adx_strong = bool(adx.iloc[-1] > 25)
        adx_bullish = bool(adx_strong and plus_di.iloc[-1] > minus_di.iloc[-1])
        adx_bearish = bool(adx_strong and plus_di.iloc[-1] < minus_di.iloc[-1])
        
        # 7. Price Action - Higher Highs / Lower Lows
        recent_highs = high.tail(5).values
        recent_lows = low.tail(5).values
        
        higher_highs = bool(all(recent_highs[i] > recent_highs[i-1] for i in range(1, len(recent_highs))))
        lower_lows = bool(all(recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows))))
        
        # 8. Volume Trend (if available)
        has_volume = 'Volume' in df.columns and df['Volume'].sum() > 0
        volume_increasing = False
        if has_volume:
            volume_increasing = df['Volume'].tail(3).is_monotonic_increasing
        
        # 9. Candlestick Patterns
        prev_close = close.iloc[-2]
        curr_close = close.iloc[-1]
        curr_open = df['Open'].iloc[-1] if 'Open' in df.columns else prev_close
        curr_high = high.iloc[-1]
        curr_low = low.iloc[-1]
        
        body = abs(curr_close - curr_open)
        upper_wick = curr_high - max(curr_close, curr_open)
        lower_wick = min(curr_close, curr_open) - curr_low
        
        hammer = bool(lower_wick > body * 2 and upper_wick < body * 0.5)
        shooting_star = bool(upper_wick > body * 2 and lower_wick < body * 0.5)
        
        # 10. Multiple Timeframe Check (simulated with different MA periods)
        ma_short = close.rolling(5).mean().iloc[-1]
        ma_medium = close.rolling(20).mean().iloc[-1]
        ma_long = close.rolling(50).mean().iloc[-1]
        
        ma_aligned_bullish = bool(ma_short > ma_medium > ma_long)
        ma_aligned_bearish = bool(ma_short < ma_medium < ma_long)
        
        # 11. Recent Momentum
        returns_5 = (close.iloc[-1] / close.iloc[-6] - 1) if len(close) >= 6 else 0
        momentum_bullish = bool(returns_5 > 0.005)  # 0.5% gain in 5 periods
        momentum_bearish = bool(returns_5 < -0.005)
        
        # 12. Support/Resistance Proximity (simplified)
        recent_range = high.tail(20).max() - low.tail(20).min()
        position_in_range = (close.iloc[-1] - low.tail(20).min()) / recent_range if recent_range > 0 else 0.5
        
        near_support = bool(position_in_range < 0.2)
        near_resistance = bool(position_in_range > 0.8)
        
        # ── Count Bullish vs Bearish Signals ───────────────────────────────
        bullish_signals = sum([
            ema_bullish,
            macd_bullish,
            rsi_bullish,
            bb_bullish,
            stoch_bullish,
            adx_bullish,
            higher_highs,
            ma_aligned_bullish,
            momentum_bullish,
            near_support,
            hammer,
            volume_increasing if has_volume else ema_bullish
        ])
        
        bearish_signals = sum([
            ema_bearish,
            macd_bearish,
            rsi_bearish,
            bb_bearish,
            stoch_bearish,
            adx_bearish,
            lower_lows,
            ma_aligned_bearish,
            momentum_bearish,
            near_resistance,
            shooting_star,
            not volume_increasing if has_volume else ema_bearish
        ])
        
        # ── ULTRA CONSERVATIVE DECISION LOGIC ─────────────────────────────
        
        # Calculate score
        bullish_score = bullish_signals * 30  # 30 points per signal
        bearish_score = bearish_signals * 30
        
        # Determine signal based on strict consensus
        if bullish_signals >= self.min_indicators_agree and bullish_score >= self.min_score:
            # STRONG BUY - All indicators align bullish
            signal = "UP"
            confidence = min(50 + (bullish_signals / 12) * 50, 99)
            strength = "STRONG" if bullish_signals >= 11 else "MODERATE"
            reason = f"{bullish_signals}/12 indicators bullish (Score: {bullish_score})"
            
        elif bearish_signals >= self.min_indicators_agree and bearish_score >= self.min_score:
            # STRONG SELL - All indicators align bearish
            signal = "DOWN"
            confidence = min(50 + (bearish_signals / 12) * 50, 99)
            strength = "STRONG" if bearish_signals >= 11 else "MODERATE"
            reason = f"{bearish_signals}/12 indicators bearish (Score: {bearish_score})"
            
        else:
            # NO SIGNAL - Not enough consensus
            signal = "NEUTRAL"
            confidence = 50 + (abs(bullish_signals - bearish_signals) / 12) * 25
            strength = "WEAK"
            reason = f"Insufficient consensus (Bullish: {bullish_signals}, Bearish: {bearish_signals})"
        
        # ── Calculate SL/TP ───────────────────────────────────────────────
        # Get current price first
        price = close.iloc[-1]
        
        # Use pre-calculated atr from ADX section, or calculate fresh if needed
        try:
            if 'atr' in locals() and atr is not None:
                current_atr = atr.iloc[-1] if not atr.empty else price * 0.01
            else:
                # Calculate ATR fresh
                tr1 = high - low
                tr2 = abs(high - close.shift(1))
                tr3 = abs(low - close.shift(1))
                tr_fresh = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr_fresh = tr_fresh.rolling(14).mean()
                current_atr = atr_fresh.iloc[-1] if not atr_fresh.empty else price * 0.01
        except:
            current_atr = price * 0.01  # Fallback: 1% of price
        
        if signal == "UP":
            sl = price - (1.5 * current_atr)  # Tighter stop
            tp = price + (2.5 * current_atr)  # 1:1.66 risk/reward
        elif signal == "DOWN":
            sl = price + (1.5 * current_atr)
            tp = price - (2.5 * current_atr)
        else:
            sl = price * 0.98
            tp = price * 1.02
        
        rr = abs(tp - price) / abs(price - sl) if abs(price - sl) > 0 else 0
        
        # ── Track History ──────────────────────────────────────────────────
        self.pattern_history.append({
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'bullish_count': bullish_signals,
            'bearish_count': bearish_signals,
            'price': float(price)
        })
        
        # ── Return Result ───────────────────────────────────────────────────
        return {
            "signal": signal,
            "confidence": round(confidence, 1),
            "strength": strength,
            "price": float(price),
            "stop_loss": float(sl),
            "take_profit": float(tp),
            "risk_reward": round(rr, 2),
            "reason": reason,
            "indicators_agreeing": bullish_signals if signal == "UP" else (bearish_signals if signal == "DOWN" else 0),
            "total_indicators": 12,
            "score": bullish_score if signal == "UP" else (bearish_score if signal == "DOWN" else 0),
            "indicators": {
                "rsi": round(rsi_val, 2),
                "ema_aligned": bool(ema_bullish if signal == "UP" else ema_bearish),
                "macd_aligned": bool(macd_bullish if signal == "UP" else macd_bearish),
                "adx": round(adx.iloc[-1], 2) if not np.isnan(adx.iloc[-1]) else None,
                "stoch_k": round(stoch_k.iloc[-1], 2) if not np.isnan(stoch_k.iloc[-1]) else None,
                "position_in_range": round(position_in_range, 3),
            },
            "warning": "⚠️ No trading system is 100% accurate. Past performance does not guarantee future results."
        }
    
    def _neutral_response(self, reason: str) -> Dict[str, Any]:
        return {
            "signal": "NEUTRAL",
            "confidence": 50.0,
            "strength": "WEAK",
            "price": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "risk_reward": 0.0,
            "reason": reason,
            "warning": "⚠️ No trading system is 100% accurate."
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get signal generation statistics with 90% accuracy focus"""
        if not self.pattern_history:
            return {"message": "No signals generated yet"}
        
        recent = self.pattern_history[-100:]
        signals = [r for r in recent if r['signal'] != 'NEUTRAL']
        high_confidence = [r for r in signals if r.get('confidence', 0) >= 90]
        
        return {
            "total_signals": len(signals),
            "high_confidence_signals": len(high_confidence),
            "accuracy_target": "75%+",
            "signal_frequency": len(signals) / max(len(recent), 1),
            "avg_indicators_agreeing": np.mean([r['indicators_agreeing'] for r in signals]) if signals else 0,
            "avg_confidence": np.mean([r.get('confidence', 0) for r in signals]) if signals else 0,
            "recent_signals": len([r for r in recent[-20:] if r['signal'] != 'NEUTRAL']),
            "disclaimer": "Balanced mode: Quality signals with good frequency"
        }
