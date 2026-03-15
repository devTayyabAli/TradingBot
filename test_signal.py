import requests
r = requests.get('http://127.0.0.1:8000/api/signal?asset=EURUSD&timeframe=1m')
d = r.json()
print(f"Signal: {d.get('signal', 'N/A')}, Confidence: {d.get('confidence', 0)}%, Score: {d.get('score', 0)}")
print(f"Patterns detected: {list(d.get('patterns', {}).keys())}")
print(f"Indicators: VWAP={d['indicators'].get('vwap')}, Ichimoku={d['indicators'].get('tenkan_sen')}")
