"""
Command-line interface for Pundora.
"""

import argparse
import asyncio
import sys
import os
from typing import Optional

from .joke_generator import JokeGenerator
from .tts_service import TTSService
from .config import config

class PundoraCLI:
    """Command-line interface for Pundora."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.joke_generator = None
        self.tts_service = None
    
    async def initialize_services(self):
        """Initialize the joke generator and TTS service."""
        try:
            self.joke_generator = JokeGenerator()
            print("✅ Joke generator initialized")
        except Exception as e:
            print(f"❌ Failed to initialize joke generator: {e}")
            print("Running in fallback mode...")
        
        try:
            self.tts_service = TTSService()
            print("✅ TTS service initialized")
        except Exception as e:
            print(f"❌ Failed to initialize TTS service: {e}")
            print("Voice mode will not be available")
    
    async def generate_joke(
        self, 
        category: str = "general",
        humor_level: str = "medium",
        voice: bool = False,
        voice_type: str = "dad",
        custom_prompt: Optional[str] = None
    ):
        """Generate and display a joke."""
        
        if not self.joke_generator:
            print("❌ Joke generator not available")
            return
        
        try:
            # Generate joke
            result = await self.joke_generator.generate_joke(category, humor_level, custom_prompt)
            
            # Display joke
            print(f"\n🎭 Pundora Dad Joke ({result['category']} - {result['humor_level']})")
            print("=" * 50)
            print(f"💬 {result['joke']}")
            print(f"📊 Source: {result['source']}")
            print("=" * 50)
            
            # Generate voice if requested
            if voice and self.tts_service:
                try:
                    print("🔊 Generating voice...")
                    audio_data = await self.tts_service.generate_speech(result['joke'], voice_type)
                    
                    # Save audio file
                    filename = f"joke_{category}_{humor_level}.mp3"
                    with open(filename, 'wb') as f:
                        f.write(audio_data)
                    
                    print(f"🎵 Audio saved as: {filename}")
                    print("💡 Play the file to hear the joke!")
                    
                except Exception as e:
                    print(f"❌ Failed to generate voice: {e}")
            elif voice and not self.tts_service:
                print("❌ TTS service not available for voice generation")
                
        except Exception as e:
            print(f"❌ Failed to generate joke: {e}")
    
    def list_categories(self):
        """List available joke categories."""
        if self.joke_generator:
            categories = self.joke_generator.get_categories()
        else:
            categories = config.CATEGORIES
        
        print("\n📂 Available Categories:")
        print("=" * 30)
        for i, category in enumerate(categories, 1):
            print(f"{i:2d}. {category}")
    
    def list_humor_levels(self):
        """List available humor levels."""
        if self.joke_generator:
            levels = self.joke_generator.get_humor_levels()
        else:
            levels = config.HUMOR_LEVELS
        
        print("\n😄 Humor Levels:")
        print("=" * 20)
        for i, level in enumerate(levels, 1):
            print(f"{i}. {level}")
    
    def list_voices(self):
        """List available voice types."""
        if self.tts_service:
            voices = self.tts_service.get_voice_configs()
        else:
            voices = config.VOICES
        
        print("\n🎙️ Available Voices:")
        print("=" * 25)
        for voice, description in voices.items():
            print(f"• {voice}: {description}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Pundora - AI-powered Dad Joke Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pundora --joke                           # Generate a random joke
  pundora --joke --category puns           # Generate a pun joke
  pundora --joke --level extra --voice     # Generate extra cringy joke with voice
  pundora --joke --voice --voice-type robot # Generate joke with robot voice
  pundora --list-categories                # List all categories
  pundora --list-levels                    # List humor levels
  pundora --list-voices                    # List voice types

Advanced Features:
  pundora-advanced --joke --voice --translate-to es --save-favorite
  pundora-advanced --favorites --statistics --leaderboard
  pundora-advanced --competitions --analytics --cache-stats
        """
    )
    
    # Main action
    parser.add_argument(
        "--joke", 
        action="store_true", 
        help="Generate a dad joke"
    )
    
    # Joke options
    parser.add_argument(
        "--category", 
        default="general",
        help="Joke category (default: general)"
    )
    parser.add_argument(
        "--level", 
        default="medium",
        help="Humor level: mild, medium, extra (default: medium)"
    )
    parser.add_argument(
        "--prompt",
        help="Custom prompt for joke generation"
    )
    
    # Voice options
    parser.add_argument(
        "--voice", 
        action="store_true",
        help="Generate voice for the joke"
    )
    parser.add_argument(
        "--voice-type",
        default="dad",
        help="Voice type: dad, robot, dramatic, cheerful (default: dad)"
    )
    
    # List options
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available joke categories"
    )
    parser.add_argument(
        "--list-levels",
        action="store_true",
        help="List available humor levels"
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available voice types"
    )
    
    # Configuration
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Run the CLI
    asyncio.run(run_cli(args))

async def run_cli(args):
    """Run the CLI with given arguments."""
    cli = PundoraCLI()
    
    # Initialize services
    await cli.initialize_services()
    
    # Handle list commands
    if args.list_categories:
        cli.list_categories()
        return
    
    if args.list_levels:
        cli.list_humor_levels()
        return
    
    if args.list_voices:
        cli.list_voices()
        return
    
    # Handle joke generation
    if args.joke:
        await cli.generate_joke(
            category=args.category,
            humor_level=args.level,
            voice=args.voice,
            voice_type=args.voice_type,
            custom_prompt=args.prompt
        )
    else:
        print("Use --joke to generate a joke or --help for more options")

if __name__ == "__main__":
    main()