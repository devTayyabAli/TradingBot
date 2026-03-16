import openai
import os
from typing import Dict, Any, List
import json
from datetime import datetime

class OpenAIEnhancer:
    """Enhance trading signals using OpenAI GPT for professional analysis"""
    
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY', 'your-openai-key-here')
        )
    
    async def enhance_signal(self, signal_data: Dict[str, Any], asset: str, timeframe: str) -> Dict[str, Any]:
        """Enhance trading signal with AI analysis for 90% accuracy"""
        
        # Only enhance high-quality signals
        if signal_data.get('confidence', 0) < 85:
            # Return neutral for low confidence signals
            return {
                **signal_data,
                'signal': 'NEUTRAL',
                'confidence': 50,
                'strength': 'WEAK',
                'ai_analysis': 'Signal filtered out - confidence below 85% threshold',
                'ai_recommendation': 'HOLD',
                'is_ai_enhanced': True
            }
        
        # Prepare market context for AI
        market_context = {
            'asset': asset,
            'timeframe': timeframe,
            'current_signal': signal_data.get('signal', 'NEUTRAL'),
            'confidence': signal_data.get('confidence', 0),
            'price': signal_data.get('price', 0),
            'indicators': signal_data.get('indicators_agreeing', 0),
            'total_indicators': signal_data.get('total_indicators', 12),
            'strength': signal_data.get('strength', 'UNKNOWN')
        }
        
        # Create AI prompt for 90% accuracy analysis
        prompt = f"""
        You are a conservative trading analyst focused on 90%+ accuracy. Analyze this signal:
        
        MARKET DATA:
        Asset: {market_context['asset']}
        Timeframe: {market_context['timeframe']}
        Signal: {market_context['current_signal']}
        Confidence: {market_context['confidence']}%
        Price: ${market_context['price']}
        Technical Indicators: {market_context['indicators']}/{market_context['total_indicators']} agreeing
        Signal Strength: {market_context['strength']}
        
        CRITICAL: Only recommend STRONG BUY or STRONG SELL if you believe this has 90%+ success probability.
        Otherwise, recommend HOLD.
        
        Respond in JSON format:
        {{
            "analysis": "detailed analysis",
            "risk_score": 1-10,
            "stop_loss": price,
            "take_profit": price,
            "sentiment": "bullish/bearish/neutral",
            "key_factors": ["factor1", "factor2"],
            "risks": ["risk1", "risk2"],
            "recommendation": "STRONG BUY/STRONG SELL/HOLD",
            "confidence_boost": 0-10,
            "success_probability": 85-100
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a conservative trading analyst with 20+ years experience. Your goal is 90%+ accuracy. Be extremely selective."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.1  # Lower temperature for more consistent results
            )
            
            ai_analysis = json.loads(response.choices[0].message.content)
            
            # Apply 90% accuracy filter
            if ai_analysis['success_probability'] < 90 or ai_analysis['recommendation'] == 'HOLD':
                return {
                    **signal_data,
                    'signal': 'NEUTRAL',
                    'confidence': 50,
                    'strength': 'WEAK',
                    'ai_analysis': ai_analysis['analysis'],
                    'ai_recommendation': 'HOLD',
                    'ai_risk_score': ai_analysis['risk_score'],
                    'is_ai_enhanced': True
                }
            
            # Enhance signal with AI insights for high-confidence trades
            enhanced_signal = signal_data.copy()
            enhanced_signal.update({
                'ai_analysis': ai_analysis['analysis'],
                'ai_risk_score': ai_analysis['risk_score'],
                'ai_stop_loss': ai_analysis['stop_loss'],
                'ai_take_profit': ai_analysis['take_profit'],
                'ai_sentiment': ai_analysis['sentiment'],
                'ai_key_factors': ai_analysis['key_factors'],
                'ai_risks': ai_analysis['risks'],
                'ai_recommendation': ai_analysis['recommendation'],
                'ai_confidence_boost': ai_analysis['confidence_boost'],
                'enhanced_confidence': min(95, signal_data.get('confidence', 0) + ai_analysis['confidence_boost']),
                'is_ai_enhanced': True,
                'ai_timestamp': datetime.now().isoformat()
            })
            
            return enhanced_signal
            
        except Exception as e:
            print(f"[OpenAI] Error enhancing signal: {e}")
            # Return conservative neutral signal if AI fails
            return {
                **signal_data,
                'signal': 'NEUTRAL',
                'confidence': 50,
                'strength': 'WEAK',
                'ai_analysis': 'AI analysis unavailable - using conservative approach',
                'ai_recommendation': 'HOLD',
                'is_ai_enhanced': True
            }
    
    async def get_market_sentiment(self, asset: str) -> Dict[str, Any]:
        """Get overall market sentiment for an asset"""
        
        prompt = f"""
        Analyze the current market sentiment for {asset} considering:
        - Recent price action trends
        - Key economic factors affecting this asset
        - Market psychology
        - Technical vs fundamental factors
        
        Provide sentiment analysis in JSON:
        {{
            "overall_sentiment": "strongly_bullish/bullish/neutral/bearish/strongly_bearish",
            "sentiment_score": 1-100,
            "key_drivers": ["driver1", "driver2"],
            "market_outlook": "short_term_outlook",
            "volatility_expectation": "low/medium/high"
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a market sentiment analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.4
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"[OpenAI] Error getting sentiment: {e}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 50,
                "key_drivers": ["Market analysis unavailable"],
                "market_outlook": "stable",
                "volatility_expectation": "medium"
            }
