"""
Startup script for Windows that properly configures asyncio for Playwright
Python 3.14+ compatible
"""
import sys
import asyncio

# For Windows + Python 3.14, force ProactorEventLoop
if sys.platform == "win32":
    from asyncio.windows_events import ProactorEventLoop

import uvicorn

if __name__ == "__main__":
    # Create and set the event loop BEFORE importing main
    if sys.platform == "win32":
        loop = ProactorEventLoop()
        asyncio.set_event_loop(loop)
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable reload to prevent loop issues
        loop="asyncio"
    )
