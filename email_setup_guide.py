"""
Email Setup Guide for Trading Bot Notifications
Instructions for setting up Gmail App Password
"""

def print_email_setup_guide():
    print("""
EMAIL NOTIFICATION SETUP GUIDE
================================

To receive email alerts for high-quality trading signals, you need to configure Gmail App Password.

STEP 1: Enable 2-Factor Authentication
-----------------------------------------
1. Go to your Google Account: https://myaccount.google.com/
2. Click on "Security" in the left menu
3. Enable "2-Step Verification" if not already enabled
4. Follow the setup process

STEP 2: Generate App Password
--------------------------------
1. After 2FA is enabled, go to: https://myaccount.google.com/apppasswords
2. Select "Mail" from the app dropdown
3. Select "Other (Custom name)" and enter "Trading Bot"
4. Click "Generate"
5. Copy the 16-character password (e.g., xxxx xxxx xxxx xxxx)
6. Save this password - you'll need it for the bot

STEP 3: Configure in Trading Bot
----------------------------------
1. Open the trading bot interface
2. Click the bell icon in the top right
3. Enter your Gmail address
4. Enter the App Password (NOT your regular password)
5. Enter recipient email (can be same or different)
6. Click "Save Configuration"
7. Click "Test" to verify it works

What You'll Receive:
----------------------
- Beautiful HTML email alerts for high-quality signals
- Complete trade details (entry, SL, TP, risk/reward)
- Signal strength and confidence indicators
- Professional trading analysis summary

Email Criteria:
------------------
- Confidence >= 75%
- Strength: STRONG or MODERATE  
- 10+ indicators agreeing
- Only UP/DOWN signals (no NEUTRAL)

Automatic Notifications:
--------------------------
Emails are sent automatically when:
- You manually generate a signal that meets criteria
- The system detects a high-quality opportunity
- Real-time alerts for immediate action

Important Notes:
------------------
- Use App Password, NOT regular Gmail password
- Emails only sent for HIGH-QUALITY signals
- Your credentials are stored locally and securely
- You can test the setup before saving

Need Help?
-------------
If you have issues:
1. Verify 2FA is enabled
2. Generate a fresh App Password
3. Check email addresses are correct
4. Use the "Test" button to verify

Ready to receive trading alerts via email!
""")

if __name__ == "__main__":
    print_email_setup_guide()
