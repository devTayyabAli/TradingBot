@app.get("/api/signal")
async def get_signal(asset: str = "EURUSD", timeframe: str = "1m"):
    try:
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

    except Exception as e:
        print(f"[Signal API] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {str(e)}")
