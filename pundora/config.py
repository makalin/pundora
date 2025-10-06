"""
Configuration management for Pundora.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for Pundora."""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: Optional[str] = os.getenv("ELEVENLABS_VOICE_ID")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Joke Configuration
    DEFAULT_HUMOR_LEVEL: str = "medium"
    DEFAULT_CATEGORY: str = "general"
    MAX_JOKE_LENGTH: int = 500
    
    # Voice Configuration
    DEFAULT_VOICE: str = "dad"
    VOICE_SPEED: float = 1.0
    VOICE_STABILITY: float = 0.5
    
    # Available Categories
    CATEGORIES = [
        "general",
        "puns",
        "knock-knock",
        "wordplay",
        "dad-classics",
        "food",
        "animals",
        "technology"
    ]
    
    # Humor Levels
    HUMOR_LEVELS = ["mild", "medium", "extra"]
    
    # Voice Options
    VOICES = {
        "dad": "A warm, fatherly voice perfect for dad jokes",
        "robot": "A mechanical voice for tech jokes",
        "dramatic": "An overly dramatic narrator voice",
        "cheerful": "An upbeat, happy voice"
    }

config = Config()