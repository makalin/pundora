#!/usr/bin/env python3
"""
Main entry point for Pundora - AI-powered Dad Joke Generator
"""

import uvicorn
from pundora.api import app
from pundora.config import config

if __name__ == "__main__":
    print("🎭 Starting Pundora - Dad Joke Generator")
    print("=" * 50)
    print(f"🌐 Server: http://{config.HOST}:{config.PORT}")
    print(f"🔧 Debug: {config.DEBUG}")
    print("=" * 50)
    
    uvicorn.run(
        "pundora.api:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )