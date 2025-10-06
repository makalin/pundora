#!/usr/bin/env python3
"""
Advanced CLI for Pundora with all new features.
"""

import argparse
import asyncio
import sys
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from .joke_generator import JokeGenerator
from .tts_service import TTSService
from .database import PundoraDB
from .sharing import JokeSharing
from .translation import JokeTranslator
from .scheduler import JokeScheduler
from .gamification import PundoraGamification
from .cache import CacheManager
from .analytics import PundoraAnalytics
from .config import config

class AdvancedPundoraCLI:
    """Advanced CLI with all Pundora features."""
    
    def __init__(self):
        """Initialize the advanced CLI."""
        self.joke_generator = None
        self.tts_service = None
        self.db = None
        self.sharing = None
        self.translator = None
        self.scheduler = None
        self.gamification = None
        self.cache_manager = None
        self.analytics = None
        self.user_id = "cli_user"
    
    async def initialize_services(self):
        """Initialize all services."""
        try:
            self.joke_generator = JokeGenerator()
            print("✅ Joke generator initialized")
        except Exception as e:
            print(f"❌ Failed to initialize joke generator: {e}")
        
        try:
            self.tts_service = TTSService()
            print("✅ TTS service initialized")
        except Exception as e:
            print(f"❌ Failed to initialize TTS service: {e}")
        
        try:
            self.db = PundoraDB()
            self.sharing = JokeSharing()
            self.translator = JokeTranslator()
            self.scheduler = JokeScheduler(self.db)
            self.gamification = PundoraGamification(self.db)
            self.cache_manager = CacheManager()
            self.analytics = PundoraAnalytics()
            print("✅ Advanced services initialized")
        except Exception as e:
            print(f"❌ Failed to initialize advanced services: {e}")
    
    async def generate_joke_with_features(
        self,
        category: str = "general",
        humor_level: str = "medium",
        voice: bool = False,
        voice_type: str = "dad",
        custom_prompt: Optional[str] = None,
        translate_to: Optional[str] = None,
        save_to_favorites: bool = False
    ):
        """Generate a joke with advanced features."""
        
        if not self.joke_generator:
            print("❌ Joke generator not available")
            return
        
        try:
            # Check cache first
            cached_joke = None
            if self.cache_manager:
                cached_joke = await self.cache_manager.get_cached_joke(category, humor_level, custom_prompt)
            
            if cached_joke:
                joke_data = cached_joke
                print("📦 Using cached joke")
            else:
                # Generate new joke
                joke_data = await self.joke_generator.generate_joke(category, humor_level, custom_prompt)
                
                # Cache the joke
                if self.cache_manager:
                    await self.cache_manager.cache_joke(joke_data, category, humor_level, custom_prompt)
            
            # Display joke
            print(f"\n🎭 Pundora Dad Joke ({joke_data['category']} - {joke_data['humor_level']})")
            print("=" * 60)
            print(f"💬 {joke_data['joke']}")
            print(f"📊 Source: {joke_data['source']}")
            print("=" * 60)
            
            # Save to database
            joke_id = None
            if self.db:
                joke_id = await self.db.save_joke(joke_data)
                print(f"💾 Saved to database (ID: {joke_id})")
            
            # Generate voice if requested
            if voice and self.tts_service:
                try:
                    print("🔊 Generating voice...")
                    audio_data = await self.tts_service.generate_speech(joke_data['joke'], voice_type)
                    
                    filename = f"joke_{category}_{humor_level}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                    with open(filename, 'wb') as f:
                        f.write(audio_data)
                    
                    print(f"🎵 Audio saved as: {filename}")
                except Exception as e:
                    print(f"❌ Failed to generate voice: {e}")
            
            # Translate if requested
            if translate_to and self.translator:
                try:
                    print(f"🌍 Translating to {translate_to}...")
                    translation = await self.translator.translate_joke(
                        joke_data['joke'], translate_to, 'en'
                    )
                    
                    if translation['success']:
                        print(f"🌍 Translation: {translation['translated_joke']}")
                    else:
                        print(f"❌ Translation failed: {translation['error']}")
                except Exception as e:
                    print(f"❌ Translation error: {e}")
            
            # Add to favorites if requested
            if save_to_favorites and joke_id and self.db:
                try:
                    await self.db.toggle_favorite(joke_id)
                    print("❤️ Added to favorites")
                except Exception as e:
                    print(f"❌ Failed to add to favorites: {e}")
            
            # Track analytics
            if self.analytics:
                await self.analytics.track_event("joke_generated", self.user_id, {
                    "category": category,
                    "humor_level": humor_level,
                    "with_voice": voice,
                    "translated": bool(translate_to)
                })
            
            # Update gamification
            if self.gamification:
                await self.gamification.add_experience(self.user_id, 10, "generate_joke")
                print("🎮 Experience points added!")
            
            return joke_data
            
        except Exception as e:
            print(f"❌ Failed to generate joke: {e}")
            return None
    
    async def show_favorites(self):
        """Show favorite jokes."""
        if not self.db:
            print("❌ Database not available")
            return
        
        try:
            favorites = await self.db.get_favorite_jokes()
            
            if not favorites:
                print("📭 No favorite jokes yet")
                return
            
            print(f"\n❤️ Favorite Jokes ({len(favorites)})")
            print("=" * 50)
            
            for i, joke in enumerate(favorites, 1):
                print(f"{i}. {joke['content']}")
                print(f"   Category: {joke['category']} | Level: {joke['humor_level']}")
                print(f"   Rating: {joke['rating']}/5 | Plays: {joke['play_count']}")
                print()
                
        except Exception as e:
            print(f"❌ Failed to load favorites: {e}")
    
    async def show_statistics(self):
        """Show application statistics."""
        if not self.db:
            print("❌ Database not available")
            return
        
        try:
            stats = await self.db.get_statistics()
            
            print("\n📊 Pundora Statistics")
            print("=" * 40)
            print(f"Total Jokes: {stats['total_jokes']}")
            print(f"Total Plays: {stats['total_plays']}")
            print(f"Average Rating: {stats['average_rating']:.2f}")
            print(f"Top Jokes:")
            
            for joke in stats['top_jokes']:
                print(f"  • {joke['content'][:50]}... (Rating: {joke['rating']})")
            
            print(f"\nCategory Distribution:")
            for category, count in stats['category_counts'].items():
                print(f"  • {category}: {count}")
                
        except Exception as e:
            print(f"❌ Failed to load statistics: {e}")
    
    async def show_leaderboard(self, limit: int = 10):
        """Show user leaderboard."""
        if not self.gamification:
            print("❌ Gamification not available")
            return
        
        try:
            leaderboard = await self.gamification.get_global_leaderboard(limit)
            
            print(f"\n🏆 Top {limit} Users")
            print("=" * 40)
            
            for i, user in enumerate(leaderboard, 1):
                print(f"{i:2d}. {user['user_id']}")
                print(f"    Level: {user['level']} | XP: {user['experience_points']}")
                print(f"    Jokes: {user['jokes_generated']} | Plays: {user['total_plays']}")
                print()
                
        except Exception as e:
            print(f"❌ Failed to load leaderboard: {e}")
    
    async def show_competitions(self):
        """Show active competitions."""
        if not self.gamification:
            print("❌ Gamification not available")
            return
        
        try:
            competitions = await self.gamification.get_active_competitions()
            
            if not competitions:
                print("📭 No active competitions")
                return
            
            print(f"\n🏆 Active Competitions ({len(competitions)})")
            print("=" * 50)
            
            for comp in competitions:
                print(f"• {comp.name}")
                print(f"  Description: {comp.description}")
                print(f"  Category: {comp.category} | Level: {comp.humor_level}")
                print(f"  Participants: {comp.current_participants}/{comp.max_participants}")
                print(f"  Prize: {comp.prize}")
                print(f"  Ends: {comp.end_date}")
                print()
                
        except Exception as e:
            print(f"❌ Failed to load competitions: {e}")
    
    async def schedule_joke(self, joke_id: int, schedule_time: str, email: str):
        """Schedule a joke for delivery."""
        if not self.scheduler:
            print("❌ Scheduler not available")
            return
        
        try:
            from datetime import datetime
            schedule_dt = datetime.fromisoformat(schedule_time)
            
            schedule_id = await self.scheduler.schedule_joke(
                joke_id, schedule_dt, email, "email"
            )
            
            print(f"✅ Joke scheduled for {schedule_dt}")
            print(f"Schedule ID: {schedule_id}")
            
        except Exception as e:
            print(f"❌ Failed to schedule joke: {e}")
    
    async def export_data(self, format: str = "json"):
        """Export jokes data."""
        if not self.db:
            print("❌ Database not available")
            return
        
        try:
            filename = await self.db.export_jokes(format)
            print(f"✅ Data exported to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to export data: {e}")
    
    async def show_analytics(self, days: int = 7):
        """Show analytics summary."""
        if not self.analytics:
            print("❌ Analytics not available")
            return
        
        try:
            summary = await self.analytics.get_analytics_summary(days)
            
            print(f"\n📈 Analytics Summary (Last {days} days)")
            print("=" * 40)
            print(f"Total Events: {summary['total_events']}")
            print(f"Unique Users: {summary['unique_users']}")
            print(f"Average Response Time: {summary['performance']['avg_response_time']}s")
            print(f"Total Requests: {summary['performance']['total_requests']}")
            print(f"Errors: {summary['errors']}")
            
            print(f"\nEvent Breakdown:")
            for event_type, count in summary['event_counts'].items():
                print(f"  • {event_type}: {count}")
                
        except Exception as e:
            print(f"❌ Failed to load analytics: {e}")
    
    async def show_cache_stats(self):
        """Show cache statistics."""
        if not self.cache_manager:
            print("❌ Cache manager not available")
            return
        
        try:
            stats = self.cache_manager.get_cache_stats()
            
            print("\n🗄️ Cache Statistics")
            print("=" * 30)
            print(f"Joke Cache Hits: {stats['joke_cache']['hits']}")
            print(f"Joke Cache Misses: {stats['joke_cache']['misses']}")
            print(f"Hit Rate: {stats['joke_cache']['hit_rate']:.1%}")
            print(f"Memory Cache Size: {stats['joke_cache']['memory_cache_size']}")
            print(f"API Cache Size: {stats['api_cache_size']}")
            
        except Exception as e:
            print(f"❌ Failed to load cache stats: {e}")
    
    async def clear_cache(self):
        """Clear all cache."""
        if not self.cache_manager:
            print("❌ Cache manager not available")
            return
        
        try:
            await self.cache_manager.joke_cache.clear_cache()
            self.cache_manager.api_cache.clear()
            print("✅ Cache cleared successfully")
            
        except Exception as e:
            print(f"❌ Failed to clear cache: {e}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Pundora Advanced CLI - Full-featured dad joke generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Advanced Examples:
  pundora-advanced --joke --category puns --level extra --voice --voice-type robot
  pundora-advanced --joke --translate-to es --save-favorite
  pundora-advanced --favorites
  pundora-advanced --statistics
  pundora-advanced --leaderboard --limit 20
  pundora-advanced --competitions
  pundora-advanced --schedule 123 "2024-01-15T09:00:00" "user@example.com"
  pundora-advanced --export --format json
  pundora-advanced --analytics --days 30
  pundora-advanced --cache-stats
  pundora-advanced --clear-cache
        """
    )
    
    # Main actions
    parser.add_argument("--joke", action="store_true", help="Generate a dad joke")
    parser.add_argument("--favorites", action="store_true", help="Show favorite jokes")
    parser.add_argument("--statistics", action="store_true", help="Show statistics")
    parser.add_argument("--leaderboard", action="store_true", help="Show leaderboard")
    parser.add_argument("--competitions", action="store_true", help="Show competitions")
    parser.add_argument("--analytics", action="store_true", help="Show analytics")
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache")
    parser.add_argument("--export", action="store_true", help="Export data")
    parser.add_argument("--schedule", nargs=3, metavar=("JOKE_ID", "TIME", "EMAIL"), help="Schedule a joke")
    
    # Joke options
    parser.add_argument("--category", default="general", help="Joke category")
    parser.add_argument("--level", default="medium", help="Humor level")
    parser.add_argument("--prompt", help="Custom prompt")
    parser.add_argument("--voice", action="store_true", help="Generate voice")
    parser.add_argument("--voice-type", default="dad", help="Voice type")
    parser.add_argument("--translate-to", help="Translate to language code")
    parser.add_argument("--save-favorite", action="store_true", help="Save to favorites")
    
    # Other options
    parser.add_argument("--limit", type=int, default=10, help="Limit for lists")
    parser.add_argument("--days", type=int, default=7, help="Days for analytics")
    parser.add_argument("--format", default="json", help="Export format")
    parser.add_argument("--user-id", default="cli_user", help="User ID for tracking")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Run the CLI
    asyncio.run(run_advanced_cli(args))

async def run_advanced_cli(args):
    """Run the advanced CLI with given arguments."""
    cli = AdvancedPundoraCLI()
    cli.user_id = args.user_id
    
    # Initialize services
    await cli.initialize_services()
    
    # Handle different actions
    if args.joke:
        await cli.generate_joke_with_features(
            category=args.category,
            humor_level=args.level,
            voice=args.voice,
            voice_type=args.voice_type,
            custom_prompt=args.prompt,
            translate_to=args.translate_to,
            save_to_favorites=args.save_favorite
        )
    elif args.favorites:
        await cli.show_favorites()
    elif args.statistics:
        await cli.show_statistics()
    elif args.leaderboard:
        await cli.show_leaderboard(args.limit)
    elif args.competitions:
        await cli.show_competitions()
    elif args.analytics:
        await cli.show_analytics(args.days)
    elif args.cache_stats:
        await cli.show_cache_stats()
    elif args.clear_cache:
        await cli.clear_cache()
    elif args.export:
        await cli.export_data(args.format)
    elif args.schedule:
        joke_id, schedule_time, email = args.schedule
        await cli.schedule_joke(int(joke_id), schedule_time, email)
    else:
        print("Use --help for available options")

if __name__ == "__main__":
    main()