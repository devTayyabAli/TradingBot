import asyncio
import sys

# Fix for Windows: Use ProactorEventLoop to support subprocesses (required by Playwright)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import json
from datetime import datetime
from typing import List, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data_fetcher import quotex_fetcher          # ← Quotex singleton
from ultra_conservative_engine import UltraConservativeSignalEngine
from trade_notifier import trade_notifier
from email_notifier import email_notifier
from signal_tracker import SignalTracker
from models import SignalSettings, SignalResponse, SignalHistory

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup: connect Quotex WebSocket ──────────────────────────────────
    print("[Server] Connecting to Quotex API…")
    connected = await quotex_fetcher.connect()
    if not connected:
        print(
            "[Server] WARNING: Quotex connection failed. "
            "Make sure API-Quotex-main/sessions/config.json has valid credentials."
        )

    # Start background broadcast loop
    task = asyncio.create_task(broadcast_signal())
    yield

    # ── Shutdown ────────────────────────────────────────────────────────────
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await quotex_fetcher.disconnect()
    print("[Server] Shutdown complete.")


app = FastAPI(title="Trading Signal Generator API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global State ────────────────────────────────────────────────────────────
tracker = SignalTracker()
current_settings = SignalSettings()
signal_history: List[SignalHistory] = []
connected_clients: List[WebSocket] = []
current_asset = "EURUSD_otc"
current_timeframe = "1m"

# ── Asset Map: UI display name → Quotex asset symbol ───────────────────────
ASSET_MAP: Dict[str, str] = {
    # Forex OTC (available 24/7 on weekends — best for binary options)
    "EURUSD":       "EURUSD_otc",
    "EURUSD (OTC)": "EURUSD_otc",
    "GBPUSD":       "GBPUSD_otc",
    "GBPUSD (OTC)": "GBPUSD_otc",
    "USDJPY":       "USDJPY_otc",
    "USDJPY (OTC)": "USDJPY_otc",
    "AUDUSD":       "AUDUSD_otc",
    "AUDUSD (OTC)": "AUDUSD_otc",
    "USDCAD":       "USDCAD_otc",
    "USDCAD (OTC)": "USDCAD_otc",
    "USDCHF":       "USDCHF_otc",
    "USDCHF (OTC)": "USDCHF_otc",
    "NZDUSD":       "NZDUSD_otc",
    "NZDUSD (OTC)": "NZDUSD_otc",
    "EURJPY":       "EURJPY_otc",
    "EURJPY (OTC)": "EURJPY_otc",
    "GBPJPY":       "GBPJPY_otc",
    "GBPJPY (OTC)": "GBPJPY_otc",
    "EURGBP":       "EURGBP_otc",
    "EURGBP (OTC)": "EURGBP_otc",
    "USDBRL":       "USDBRL_otc",
    "USDBRL (OTC)": "USDBRL_otc",
    "USDTRY":       "USDTRY_otc",
    "USDTRY (OTC)": "USDTRY_otc",
    "USDINR":       "USDINR_otc",
    "USDINR (OTC)": "USDINR_otc",
    "CHFJPY":       "CHFJPY_otc",
    "CHFJPY (OTC)": "CHFJPY_otc",

    # Commodities OTC
    "Gold":         "Gold_otc",
    "Gold (OTC)":   "Gold_otc",
    "Silver":       "Silver_otc",
    "Silver (OTC)": "Silver_otc",
    "UKBrent":      "UKBrent_otc",
    "UKBrent (OTC)":"UKBrent_otc",
    "USCrude":      "USCrude_otc",
    "USCrude (OTC)":"USCrude_otc",

    # Crypto OTC
    "Bitcoin":      "BTCUSD_otc",
    "Ethereum":     "ETHUSD_otc",
    "Litecoin":     "LTCUSD_otc",
    "Ripple":       "XRPUSD_otc",

    # Stocks OTC
    "Apple (OTC)":    "AAPL_otc",
    "Boeing (OTC)":   "BA_otc",
    "Facebook (OTC)": "META_otc",
    "Google (OTC)":   "GOOGL_otc",
    "Intel (OTC)":    "INTC_otc",
    "Microsoft (OTC)":"MSFT_otc",
    "Netflix (OTC)":  "NFLX_otc",
    "Tesla (OTC)":    "TSLA_otc",
}

# Timeframe label → seconds (for Quotex API)
TF_TO_SECS: Dict[str, int] = {
    "1s": 5, "5s": 5, "30s": 30,
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400,
}


def _resolve(asset: str, timeframe: str):
    """Resolve frontend values into Quotex symbol and seconds."""
    symbol = ASSET_MAP.get(asset, asset if asset.endswith("_otc") else f"{asset}_otc")
    secs = TF_TO_SECS.get(timeframe, 60)
    return symbol, secs


# ── API Routes ──────────────────────────────────────────────────────────────

@app.get("/api/signal")
async def get_signal(asset: str = "EURUSD", timeframe: str = "1m"):
    symbol, _ = _resolve(asset, timeframe)
    df = await quotex_fetcher.fetch_data(symbol, timeframe=timeframe, count=150)
    if df is None:
        raise HTTPException(status_code=404, detail=f"Asset data not found: {symbol}")

    engine = UltraConservativeSignalEngine(current_settings.model_dump())
    result = engine.calculate_signals(df)
    
    # Check for high-quality trade and notify
    notification = trade_notifier.notify(result, asset, timeframe)
    
    # Send email notification for high-quality trades
    if notification:
        email_notifier.send_email(result, asset, timeframe)

    response = SignalResponse(
        asset=asset,
        timeframe=timeframe,
        timestamp=datetime.now(),
        **result
    )

    tracker.save_signal({
        "timestamp": datetime.now().isoformat(),
        "asset": asset,
        "signal": result["signal"],
        "price": result["price"],
        "confidence": result["confidence"],
    })

    return response


@app.get("/api/accuracy")
async def get_accuracy_stats():
    return tracker.calculate_stats()


@app.post("/api/signal/outcome")
async def mark_outcome(data: Dict):
    signal_id = data.get("id")
    outcome = data.get("outcome")
    if not signal_id or outcome not in ["win", "loss"]:
        raise HTTPException(status_code=400, detail="Invalid signal ID or outcome")
    tracker.update_outcome(signal_id, outcome)
    return {"status": "success"}


@app.get("/api/history")
async def get_history():
    return tracker.load_signals()[:50]


@app.get("/api/notifications")
async def get_notifications():
    """Get recent trade notifications"""
    return {
        "notifications": trade_notifier.get_recent_notifications(20),
        "unread_count": len(trade_notifier.get_unread_notifications())
    }


@app.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark notification as read"""
    trade_notifier.mark_as_read(notification_id)
    return {"status": "success"}


@app.post("/api/email/configure")
async def configure_email(data: Dict[str, str]):
    """Configure email notification settings"""
    sender_email = data.get("sender_email")
    sender_password = data.get("sender_password")
    recipient_email = data.get("recipient_email")
    
    if not all([sender_email, sender_password, recipient_email]):
        raise HTTPException(status_code=400, detail="All email fields are required")
    
    try:
        success = email_notifier.configure_email(sender_email, sender_password, recipient_email)
        if success:
            return {"status": "success", "message": "Email configured successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to configure email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email configuration failed: {str(e)}")


@app.get("/api/email/status")
async def get_email_status():
    """Get email configuration status"""
    config = email_notifier.config
    return {
        "enabled": config.get("enabled", False),
        "sender_email": config.get("sender_email", ""),
        "recipient_email": config.get("recipient_email", ""),
        "configured": bool(config.get("sender_email") and config.get("recipient_email"))
    }


@app.post("/api/email/test")
async def test_email():
    """Send test email"""
    try:
        # Create test signal data
        test_signal = {
            "signal": "UP",
            "confidence": 85.5,
            "strength": "STRONG",
            "price": 1.0850,
            "stop_loss": 1.0820,
            "take_profit": 1.0910,
            "risk_reward": 1.67,
            "reason": "Test signal - 11/12 indicators bullish (Score: 330)",
            "indicators_agreeing": 11,
            "total_indicators": 12
        }
        
        success = email_notifier.send_email(test_signal, "EUR/USD", "1m")
        if success:
            return {"status": "success", "message": "Test email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test email failed: {str(e)}")


@app.get("/api/chart")
async def get_chart_data(asset: str = "EURUSD", timeframe: str = "1m"):
    symbol, _ = _resolve(asset, timeframe)
    df = await quotex_fetcher.fetch_data(symbol, timeframe=timeframe, count=200)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"Chart data not found: {symbol}")

    chart_data = []
    for ts, row in df.iterrows():
        chart_data.append({
            "time":  int(ts.timestamp()),
            "open":  float(row["Open"]),
            "high":  float(row["High"]),
            "low":   float(row["Low"]),
            "close": float(row["Close"]),
        })
    return chart_data


@app.get("/api/assets")
async def get_assets():
    """Return live Quotex asset list with payouts (open assets only)."""
    assets = await quotex_fetcher.get_available_assets()
    result = []
    for symbol, info in assets.items():
        if info.get("is_open") and info.get("payout", 0) > 0:
            result.append({
                "symbol":  symbol,
                "name":    info.get("name", symbol),
                "payout":  info.get("payout", 0),
                "is_otc":  info.get("is_otc", False),
            })
    return sorted(result, key=lambda x: x["symbol"])


@app.post("/api/settings")
async def update_settings(settings: SignalSettings):
    global current_settings
    current_settings = settings
    return {"status": "success", "message": "Settings updated"}


@app.get("/api/status")
async def get_status():
    return {
        "quotex_connected": quotex_fetcher.is_connected,
        "current_asset":    current_asset,
        "current_timeframe": current_timeframe,
    }


# ── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    print(f"WS Client connected: {client_id}")
    connected_clients.append(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "asset": current_asset,
            "quotex_connected": quotex_fetcher.is_connected,
        }))
        while True:
            data = await websocket.receive_text()
            print(f"Message from {client_id}: {data}")
    except WebSocketDisconnect:
        print(f"WS Client disconnected: {client_id}")
    except Exception as e:
        print(f"WS Error for {client_id}: {str(e)}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)


async def broadcast_signal():
    """Periodically push live signals to all connected WebSocket clients."""
    while True:
        if connected_clients and quotex_fetcher.is_connected:
            try:
                symbol, _ = _resolve(current_asset, current_timeframe)
                df = await quotex_fetcher.fetch_data(symbol, timeframe=current_timeframe, count=150)
                if df is not None:
                    engine = UltraConservativeSignalEngine(current_settings.model_dump())
                    result = engine.calculate_signals(df)
                    response = SignalResponse(
                        asset=current_asset,
                        timeframe=current_timeframe,
                        timestamp=datetime.now(),
                        **result
                    )
                    message = response.model_dump_json()
                    dead_clients = []
                    for client in connected_clients:
                        try:
                            await client.send_text(message)
                        except Exception:
                            dead_clients.append(client)
                    for c in dead_clients:
                        connected_clients.remove(c)
            except Exception as e:
                print(f"[broadcast_signal] Error: {e}")
        await asyncio.sleep(30)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
