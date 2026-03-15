import requests
import json

try:
    r = requests.get('http://127.0.0.1:8000/api/signal?asset=EURUSD_otc&timeframe=1m', timeout=10)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        d = r.json()
        print(f"Signal: {d.get('signal')}")
        print(f"Confidence: {d.get('confidence')}%")
    else:
        print(f'Error: {r.text[:500]}')
except Exception as e:
    print(f'Exception: {e}')
    print('Server may not be running')
