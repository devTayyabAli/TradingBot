"""
Trade Notification System
Alerts when high-quality trading opportunities are found
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import winsound  # Windows sound notifications
import threading

class TradeNotifier:
    def __init__(self, notifications_file: str = "trade_notifications.json"):
        self.notifications_file = notifications_file
        self.notifications = []
        self.load_notifications()
        
    def load_notifications(self):
        """Load existing notifications"""
        if os.path.exists(self.notifications_file):
            try:
                with open(self.notifications_file, 'r') as f:
                    self.notifications = json.load(f)
            except:
                self.notifications = []
    
    def save_notifications(self):
        """Save notifications to file"""
        with open(self.notifications_file, 'w') as f:
            json.dump(self.notifications[-100:], f, indent=2)  # Keep last 100
    
    def check_signal_quality(self, signal_data: Dict[str, Any]) -> bool:
        """Check if signal meets high-quality criteria"""
        signal = signal_data.get('signal', 'NEUTRAL')
        
        # Only alert on strong UP/DOWN signals
        if signal == 'NEUTRAL':
            return False
        
        confidence = signal_data.get('confidence', 0)
        strength = signal_data.get('strength', 'WEAK')
        indicators_agreeing = signal_data.get('indicators_agreeing', 0)
        
        # High-quality criteria:
        # - Confidence >= 75%
        # - Strength is STRONG or MODERATE
        # - At least 10 indicators agreeing
        is_high_quality = (
            confidence >= 75 and
            strength in ['STRONG', 'MODERATE'] and
            indicators_agreeing >= 10
        )
        
        return is_high_quality
    
    def create_notification(self, signal_data: Dict[str, Any], asset: str, timeframe: str):
        """Create a new trade notification"""
        notification = {
            'id': len(self.notifications) + 1,
            'timestamp': datetime.now().isoformat(),
            'asset': asset,
            'timeframe': timeframe,
            'signal': signal_data.get('signal'),
            'confidence': signal_data.get('confidence'),
            'strength': signal_data.get('strength'),
            'price': signal_data.get('price'),
            'stop_loss': signal_data.get('stop_loss'),
            'take_profit': signal_data.get('take_profit'),
            'risk_reward': signal_data.get('risk_reward'),
            'reason': signal_data.get('reason'),
            'indicators_agreeing': signal_data.get('indicators_agreeing'),
            'total_indicators': signal_data.get('total_indicators'),
            'read': False
        }
        
        self.notifications.insert(0, notification)  # Add to front
        self.save_notifications()
        
        return notification
    
    def notify(self, signal_data: Dict[str, Any], asset: str, timeframe: str):
        """Send notification if signal is high quality"""
        if not self.check_signal_quality(signal_data):
            return None
        
        notification = self.create_notification(signal_data, asset, timeframe)
        
        # Play sound notification
        self.play_alert_sound()
        
        # Print alert to console
        self.print_alert(notification)
        
        return notification
    
    def play_alert_sound(self):
        """Play alert sound on Windows"""
        def play():
            try:
                # Play system alert sound 3 times
                for _ in range(3):
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    threading.Event().wait(0.5)
            except:
                pass  # Fail silently if sound doesn't work
        
        thread = threading.Thread(target=play)
        thread.daemon = True
        thread.start()
    
    def print_alert(self, notification: Dict[str, Any]):
        """Print formatted alert to console"""
        print("\n" + "="*60)
        print("🚨 HIGH-QUALITY TRADE ALERT 🚨")
        print("="*60)
        print(f"📊 Asset: {notification['asset']} ({notification['timeframe']})")
        print(f"📈 Signal: {notification['signal']} - {notification['strength']}")
        print(f"🎯 Confidence: {notification['confidence']}%")
        print(f"💰 Price: {notification['price']}")
        print(f"🛑 Stop Loss: {notification['stop_loss']}")
        print(f"🎯 Take Profit: {notification['take_profit']}")
        print(f"⚖️  Risk/Reward: 1:{notification['risk_reward']}")
        print(f"📋 Reason: {notification['reason']}")
        print(f"📊 Indicators: {notification['indicators_agreeing']}/{notification['total_indicators']} agree")
        print("="*60)
        print("⚠️  Check your trading platform and enter trade if conditions match")
        print("="*60 + "\n")
    
    def get_unread_notifications(self) -> list:
        """Get all unread notifications"""
        return [n for n in self.notifications if not n['read']]
    
    def mark_as_read(self, notification_id: int):
        """Mark notification as read"""
        for n in self.notifications:
            if n['id'] == notification_id:
                n['read'] = True
                break
        self.save_notifications()
    
    def get_recent_notifications(self, limit: int = 10) -> list:
        """Get recent notifications"""
        return self.notifications[:limit]

# Global notifier instance
trade_notifier = TradeNotifier()
