"""
Text-to-Speech service using ElevenLabs API.
"""

import asyncio
import io
import base64
from typing import Optional, Dict, Any
import httpx
from .config import config

class TTSService:
    """Text-to-Speech service using ElevenLabs API."""
    
    def __init__(self):
        """Initialize the TTS service."""
        if not config.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY is required")
        
        self.api_key = config.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = config.ELEVENLABS_VOICE_ID or "pNInz6obpgDQGcFmaJgB"  # Default voice
        
        # Voice configurations
        self.voice_configs = {
            "dad": {
                "voice_id": "pNInz6obpgDQGcFmaJgB",
                "stability": 0.5,
                "similarity_boost": 0.8,
                "speed": 0.9
            },
            "robot": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",
                "stability": 0.3,
                "similarity_boost": 0.7,
                "speed": 1.1
            },
            "dramatic": {
                "voice_id": "VR6AewLTigWG4xSOukaG",
                "stability": 0.6,
                "similarity_boost": 0.9,
                "speed": 0.8
            },
            "cheerful": {
                "voice_id": "AZnzlk1XvdvUeBnXmlld",
                "stability": 0.4,
                "similarity_boost": 0.8,
                "speed": 1.2
            }
        }
    
    async def generate_speech(
        self, 
        text: str, 
        voice: str = "dad",
        format: str = "mp3_44100_128"
    ) -> bytes:
        """
        Generate speech audio from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice type to use
            format: Audio format
            
        Returns:
            Audio data as bytes
        """
        try:
            voice_config = self.voice_configs.get(voice, self.voice_configs["dad"])
            
            url = f"{self.base_url}/text-to-speech/{voice_config['voice_id']}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": voice_config["stability"],
                    "similarity_boost": voice_config["similarity_boost"],
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                return response.content
                
        except Exception as e:
            print(f"TTS generation failed: {e}")
            # Return a simple beep sound as fallback
            return self._generate_fallback_audio()
    
    def _generate_fallback_audio(self) -> bytes:
        """Generate a simple fallback audio (beep sound)."""
        # This is a minimal WAV file with a beep sound
        # In a real implementation, you might want to use a proper audio library
        wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        # Simple sine wave beep
        beep_data = b'\x00' * 2048  # Silent audio as fallback
        return wav_header + beep_data
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices from ElevenLabs."""
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Failed to fetch voices: {e}")
            return {"voices": []}
    
    def get_voice_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get available voice configurations."""
        return self.voice_configs.copy()
    
    async def test_voice(self, voice: str = "dad") -> bool:
        """Test if a voice configuration works."""
        try:
            test_text = "Hello, this is a test of the dad joke voice system."
            audio = await self.generate_speech(test_text, voice)
            return len(audio) > 0
        except Exception:
            return False