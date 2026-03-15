import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class SignalTracker:
    def __init__(self, filename: str = "signals.json"):
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)

    def load_signals(self) -> List[Dict]:
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_signal(self, signal_data: Dict):
        signals = self.load_signals()
        # Add basic tracking fields if not present
        if "id" not in signal_data:
            signal_data["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        if "outcome" not in signal_data:
            signal_data["outcome"] = None # win, loss, or None
        
        signals.insert(0, signal_data)
        with open(self.filename, 'w') as f:
            json.dump(signals[:500], f, indent=4) # Keep last 500
        return signal_data["id"]

    def update_outcome(self, signal_id: str, outcome: str, exit_price: Optional[float] = None):
        signals = self.load_signals()
        for s in signals:
            if s["id"] == signal_id:
                s["outcome"] = outcome
                if exit_price is not None:
                    s["exit_price"] = exit_price
                break
        
        with open(self.filename, 'w') as f:
            json.dump(signals, f, indent=4)
        return True

    def calculate_stats(self) -> Dict:
        signals = self.load_signals()
        completed = [s for s in signals if s.get("outcome") in ["win", "loss"]]
        
        if not completed:
            return {
                "accuracy": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "profit_factor": 0,
                "net_pnl": 0,
                "message": "No completed trades"
            }

        wins = [s for s in completed if s["outcome"] == "win"]
        losses = [s for s in completed if s["outcome"] == "loss"]
        
        accuracy = (len(wins) / len(completed)) * 100
        
        # Simple P&L calculation (assuming $100 per trade, 85% payout)
        total_profit = len(wins) * 85
        total_loss = len(losses) * 100
        net_pnl = total_profit - total_loss
        profit_factor = total_profit / total_loss if total_loss > 0 else total_profit

        return {
            "accuracy": round(accuracy, 1),
            "total_trades": len(completed),
            "wins": len(wins),
            "losses": len(losses),
            "profit_factor": round(profit_factor, 2),
            "net_pnl": round(net_pnl, 2)
        }
