"""
Email Notification System for Trading Signals
Sends email alerts when high-quality trading opportunities are found
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional
import json
import os

class EmailNotifier:
    def __init__(self, config_file: str = "email_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load email configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default configuration
        default_config = {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_email": "",
            "min_confidence": 75,
            "min_strength": ["STRONG", "MODERATE"],
            "min_indicators": 10
        }
        
        # Save default config
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def save_config(self):
        """Save email configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def configure_email(self, sender_email: str, sender_password: str, recipient_email: str):
        """Configure email settings"""
        self.config.update({
            "enabled": True,
            "sender_email": sender_email,
            "sender_password": sender_password,
            "recipient_email": recipient_email
        })
        self.save_config()
        return True
    
    def check_signal_quality(self, signal_data: Dict[str, Any]) -> bool:
        """Check if signal meets email notification criteria"""
        if not self.config.get("enabled", False):
            return False
        
        signal = signal_data.get('signal', 'NEUTRAL')
        if signal == 'NEUTRAL':
            return False
        
        confidence = signal_data.get('confidence', 0)
        strength = signal_data.get('strength', 'WEAK')
        indicators_agreeing = signal_data.get('indicators_agreeing', 0)
        
        # Check against criteria
        meets_confidence = confidence >= self.config.get("min_confidence", 75)
        meets_strength = strength in self.config.get("min_strength", ["STRONG", "MODERATE"])
        meets_indicators = indicators_agreeing >= self.config.get("min_indicators", 10)
        
        return meets_confidence and meets_strength and meets_indicators
    
    def create_email_content(self, signal_data: Dict[str, Any], asset: str, timeframe: str) -> tuple[str, str]:
        """Create email subject and content"""
        signal = signal_data.get('signal', 'NEUTRAL')
        confidence = signal_data.get('confidence', 0)
        strength = signal_data.get('strength', 'WEAK')
        price = signal_data.get('price', 0)
        stop_loss = signal_data.get('stop_loss', 0)
        take_profit = signal_data.get('take_profit', 0)
        risk_reward = signal_data.get('risk_reward', 0)
        reason = signal_data.get('reason', 'Signal generated')
        indicators_agreeing = signal_data.get('indicators_agreeing', 0)
        total_indicators = signal_data.get('total_indicators', 12)
        
        # Subject
        subject = f"AI TRADING ALERT: {signal} {asset} - {confidence}% Confidence"
        
        # HTML Content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #1a1a1a;
                    color: #ffffff;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: linear-gradient(135deg, #2d2d2d, #3d3d3d);
                    border-radius: 15px;
                    padding: 30px;
                    border: 1px solid #444;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .alert-badge {{
                    display: inline-block;
                    padding: 10px 20px;
                    border-radius: 25px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    font-size: 18px;
                }}
                .signal-up {{
                    background: linear-gradient(45deg, #00d4ff, #00ff88);
                    color: #000;
                }}
                .signal-down {{
                    background: linear-gradient(45deg, #ff4444, #ff8888);
                    color: #fff;
                }}
                .signal-neutral {{
                    background: linear-gradient(45deg, #888888, #aaaaaa);
                    color: #fff;
                }}
                .trade-details {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 10px;
                    background: rgba(255,255,255,0.05);
                    border-radius: 5px;
                }}
                .detail-label {{
                    color: #aaa;
                    font-size: 14px;
                }}
                .detail-value {{
                    font-weight: bold;
                    font-size: 16px;
                }}
                .confidence-meter {{
                    width: 100%;
                    height: 30px;
                    background: #333;
                    border-radius: 15px;
                    overflow: hidden;
                    margin: 20px 0;
                }}
                .confidence-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #ff4444, #ffaa00, #00ff88);
                    transition: width 0.3s ease;
                }}
                .warning {{
                    background: rgba(255, 100, 0, 0.2);
                    border: 1px solid #ff6400;
                    border-radius: 10px;
                    padding: 15px;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #888;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Trading Bot Alert</h1>
                    <div class="alert-badge signal-{signal.lower()}">
                        {signal} SIGNAL DETECTED
                    </div>
                </div>
                
                <div class="trade-details">
                    <h3>Trading Opportunity</h3>
                    <div class="detail-row">
                        <span class="detail-label">Asset</span>
                        <span class="detail-value">{asset} ({timeframe})</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Signal</span>
                        <span class="detail-value">{signal} - {strength}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Entry Price</span>
                        <span class="detail-value">{price}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Stop Loss</span>
                        <span class="detail-value" style="color: #ff6b6b;">{stop_loss}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Take Profit</span>
                        <span class="detail-value" style="color: #51cf66;">{take_profit}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Risk/Reward</span>
                        <span class="detail-value">1:{risk_reward}</span>
                    </div>
                </div>
                
                <div>
                    <h3>Signal Strength</h3>
                    <div class="confidence-meter">
                        <div class="confidence-fill" style="width: {confidence}%"></div>
                    </div>
                    <p style="text-align: center; font-size: 24px; font-weight: bold; margin: 10px 0;">
                        {confidence}% Confidence
                    </p>
                    <p style="text-align: center; color: #aaa;">
                        {indicators_agreeing}/{total_indicators} indicators agree
                    </p>
                </div>
                
                <div class="trade-details">
                    <h3>Analysis Summary</h3>
                    <p style="color: #ccc; line-height: 1.6;">{reason}</p>
                </div>
                
                <div class="warning">
                    <p><strong>Important:</strong> This is an automated trading signal. Always verify market conditions before entering any trade. Past performance does not guarantee future results.</p>
                </div>
                
                <div class="footer">
                    <p>Generated by AI Trading Bot • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Ultra-Conservative Mode • High-Quality Signals Only</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def send_email(self, signal_data: Dict[str, Any], asset: str, timeframe: str) -> bool:
        """Send email notification"""
        if not self.check_signal_quality(signal_data):
            return False
        
        try:
            # Create message
            subject, html_content = self.create_email_content(signal_data, asset, timeframe)
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.config["sender_email"]
            message["To"] = self.config["recipient_email"]
            
            # Attach HTML content with proper encoding
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Create SMTP session
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
            server.starttls(context=context)
            server.login(self.config["sender_email"], self.config["sender_password"])
            
            # Send email
            server.sendmail(self.config["sender_email"], self.config["recipient_email"], message.as_string())
            server.quit()
            
            print(f"Email alert sent: {subject}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

# Global email notifier instance
email_notifier = EmailNotifier()
