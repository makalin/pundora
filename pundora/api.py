"""
FastAPI backend for Pundora dad joke generator.
"""

import asyncio
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import io

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

# Initialize FastAPI app
app = FastAPI(
    title="Pundora - Dad Joke Generator",
    description="AI-powered dad joke generator with text and voice modes",
    version="1.0.0"
)

# Initialize services
joke_generator = None
tts_service = None
db = None
sharing = None
translator = None
scheduler = None
gamification = None
cache_manager = None
analytics = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global joke_generator, tts_service, db, sharing, translator, scheduler, gamification, cache_manager, analytics
    
    try:
        # Initialize core services
        joke_generator = JokeGenerator()
        tts_service = TTSService()
        
        # Initialize new services
        db = PundoraDB()
        sharing = JokeSharing()
        translator = JokeTranslator()
        scheduler = JokeScheduler(db)
        gamification = PundoraGamification(db)
        cache_manager = CacheManager()
        analytics = PundoraAnalytics()
        
        # Start scheduler
        await scheduler.start_scheduler()
        
        print("✅ All services initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        # Initialize with fallback mode
        joke_generator = None
        tts_service = None
        db = None
        sharing = None
        translator = None
        scheduler = None
        gamification = None
        cache_manager = None
        analytics = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global scheduler, cache_manager
    
    if scheduler:
        await scheduler.stop_scheduler()
    
    if cache_manager:
        await cache_manager.shutdown()
    
    print("🛑 Services shutdown complete")

# Pydantic models
class JokeRequest(BaseModel):
    category: str = "general"
    humor_level: str = "medium"
    custom_prompt: Optional[str] = None

class JokeResponse(BaseModel):
    joke: str
    category: str
    humor_level: str
    source: str

class VoiceRequest(BaseModel):
    text: str
    voice: str = "dad"

class JokeRatingRequest(BaseModel):
    joke_id: int
    rating: int
    comment: str = ""

class TranslationRequest(BaseModel):
    joke: str
    target_language: str
    source_language: str = "en"

class ScheduleRequest(BaseModel):
    joke_id: int
    schedule_time: str
    user_email: str
    notification_type: str = "email"

class CompetitionRequest(BaseModel):
    name: str
    description: str
    category: str
    humor_level: str
    duration_days: int = 7
    max_participants: int = 100
    prize: str = "Bragging Rights"

# API Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main web interface."""
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the advanced dashboard."""
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "joke_generator": joke_generator is not None,
            "tts_service": tts_service is not None
        }
    }

@app.get("/api/joke", response_model=JokeResponse)
async def get_joke(
    category: str = Query("general", description="Joke category"),
    humor_level: str = Query("medium", description="Humor level"),
    custom_prompt: Optional[str] = Query(None, description="Custom prompt")
):
    """Generate a dad joke."""
    if not joke_generator:
        raise HTTPException(status_code=503, detail="Joke generator not available")
    
    try:
        result = await joke_generator.generate_joke(category, humor_level, custom_prompt)
        return JokeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate joke: {str(e)}")

@app.post("/api/joke", response_model=JokeResponse)
async def create_joke(request: JokeRequest):
    """Generate a dad joke with POST request."""
    if not joke_generator:
        raise HTTPException(status_code=503, detail="Joke generator not available")
    
    try:
        result = await joke_generator.generate_joke(
            request.category, 
            request.humor_level, 
            request.custom_prompt
        )
        return JokeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate joke: {str(e)}")

@app.get("/api/voice")
async def get_voice(
    text: str = Query(..., description="Text to convert to speech"),
    voice: str = Query("dad", description="Voice type")
):
    """Generate speech audio from text."""
    if not tts_service:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    try:
        audio_data = await tts_service.generate_speech(text, voice)
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=joke.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate speech: {str(e)}")

@app.post("/api/voice")
async def create_voice(request: VoiceRequest):
    """Generate speech audio with POST request."""
    if not tts_service:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    try:
        audio_data = await tts_service.generate_speech(request.text, request.voice)
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=joke.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate speech: {str(e)}")

@app.get("/api/categories")
async def get_categories():
    """Get available joke categories."""
    if not joke_generator:
        return {"categories": config.CATEGORIES}
    
    return {"categories": joke_generator.get_categories()}

@app.get("/api/humor-levels")
async def get_humor_levels():
    """Get available humor levels."""
    if not joke_generator:
        return {"humor_levels": config.HUMOR_LEVELS}
    
    return {"humor_levels": joke_generator.get_humor_levels()}

@app.get("/api/voices")
async def get_voices():
    """Get available voice configurations."""
    if not tts_service:
        return {"voices": config.VOICES}
    
    voice_configs = tts_service.get_voice_configs()
    return {"voices": voice_configs}

@app.get("/api/joke-with-voice")
async def get_joke_with_voice(
    category: str = Query("general"),
    humor_level: str = Query("medium"),
    voice: str = Query("dad"),
    custom_prompt: Optional[str] = Query(None)
):
    """Generate a joke and return both text and audio."""
    if not joke_generator or not tts_service:
        raise HTTPException(status_code=503, detail="Services not available")
    
    try:
        # Check cache first
        cached_joke = None
        if cache_manager:
            cached_joke = await cache_manager.get_cached_joke(category, humor_level, custom_prompt)
        
        if cached_joke:
            joke_result = cached_joke
        else:
            # Generate joke
            joke_result = await joke_generator.generate_joke(category, humor_level, custom_prompt)
            
            # Cache the joke
            if cache_manager:
                await cache_manager.cache_joke(joke_result, category, humor_level, custom_prompt)
        
        # Generate speech
        audio_data = await tts_service.generate_speech(joke_result["joke"], voice)
        
        # Track analytics
        if analytics:
            await analytics.track_event("joke_generated", "web_user", {
                "category": category,
                "humor_level": humor_level,
                "with_voice": True
            })
        
        return {
            "joke": joke_result["joke"],
            "category": joke_result["category"],
            "humor_level": joke_result["humor_level"],
            "source": joke_result["source"],
            "audio_url": f"/api/voice?text={joke_result['joke']}&voice={voice}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate joke with voice: {str(e)}")

# Database and Favorites Endpoints
@app.post("/api/jokes/{joke_id}/favorite")
async def toggle_favorite(joke_id: int):
    """Toggle favorite status of a joke."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        success = await db.toggle_favorite(joke_id)
        if success:
            return {"message": "Favorite status updated"}
        else:
            raise HTTPException(status_code=404, detail="Joke not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update favorite: {str(e)}")

@app.get("/api/favorites")
async def get_favorites():
    """Get all favorite jokes."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        favorites = await db.get_favorite_jokes()
        return {"favorites": favorites}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get favorites: {str(e)}")

@app.post("/api/jokes/{joke_id}/rate")
async def rate_joke(joke_id: int, request: JokeRatingRequest):
    """Rate a joke."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        success = await db.rate_joke(joke_id, request.rating, request.comment)
        if success:
            return {"message": "Joke rated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid rating")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rate joke: {str(e)}")

@app.get("/api/jokes/{joke_id}")
async def get_joke_by_id(joke_id: int):
    """Get a specific joke by ID."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        joke = await db.get_joke_by_id(joke_id)
        if joke:
            return joke
        else:
            raise HTTPException(status_code=404, detail="Joke not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get joke: {str(e)}")

@app.get("/api/statistics")
async def get_statistics():
    """Get application statistics."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        stats = await db.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# Sharing Endpoints
@app.get("/api/jokes/{joke_id}/share")
async def get_share_options(joke_id: int):
    """Get sharing options for a joke."""
    if not db or not sharing:
        raise HTTPException(status_code=503, detail="Services not available")
    
    try:
        joke = await db.get_joke_by_id(joke_id)
        if not joke:
            raise HTTPException(status_code=404, detail="Joke not found")
        
        share_options = sharing.get_all_share_options(joke)
        return share_options
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get share options: {str(e)}")

@app.get("/api/jokes/{joke_id}/qr")
async def get_qr_code(joke_id: int):
    """Get QR code for joke sharing."""
    if not db or not sharing:
        raise HTTPException(status_code=503, detail="Services not available")
    
    try:
        joke = await db.get_joke_by_id(joke_id)
        if not joke:
            raise HTTPException(status_code=404, detail="Joke not found")
        
        qr_code = sharing.generate_qr_code(joke)
        return {"qr_code": qr_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate QR code: {str(e)}")

# Translation Endpoints
@app.post("/api/translate")
async def translate_joke(request: TranslationRequest):
    """Translate a joke."""
    if not translator:
        raise HTTPException(status_code=503, detail="Translation service not available")
    
    try:
        result = await translator.translate_joke(
            request.joke, 
            request.target_language, 
            request.source_language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to translate joke: {str(e)}")

@app.get("/api/languages")
async def get_supported_languages():
    """Get supported languages for translation."""
    if not translator:
        raise HTTPException(status_code=503, detail="Translation service not available")
    
    try:
        languages = translator.get_supported_languages()
        return {"languages": languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get languages: {str(e)}")

# Scheduling Endpoints
@app.post("/api/schedule")
async def schedule_joke(request: ScheduleRequest):
    """Schedule a joke for delivery."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        from datetime import datetime
        schedule_time = datetime.fromisoformat(request.schedule_time)
        
        schedule_id = await scheduler.schedule_joke(
            request.joke_id,
            schedule_time,
            request.user_email,
            request.notification_type
        )
        
        return {"schedule_id": schedule_id, "message": "Joke scheduled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule joke: {str(e)}")

@app.get("/api/schedules")
async def get_user_schedules(user_email: str = Query(...)):
    """Get user's scheduled jokes."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        schedules = await scheduler.get_user_schedules(user_email)
        return {"schedules": schedules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schedules: {str(e)}")

# Gamification Endpoints
@app.get("/api/user/{user_id}/score")
async def get_user_score(user_id: str):
    """Get user score and statistics."""
    if not gamification:
        raise HTTPException(status_code=503, detail="Gamification not available")
    
    try:
        score = await gamification.get_user_score(user_id)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user score: {str(e)}")

@app.get("/api/leaderboard")
async def get_leaderboard(limit: int = Query(50)):
    """Get global leaderboard."""
    if not gamification:
        raise HTTPException(status_code=503, detail="Gamification not available")
    
    try:
        leaderboard = await gamification.get_global_leaderboard(limit)
        return {"leaderboard": leaderboard}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")

@app.get("/api/competitions")
async def get_competitions():
    """Get active competitions."""
    if not gamification:
        raise HTTPException(status_code=503, detail="Gamification not available")
    
    try:
        competitions = await gamification.get_active_competitions()
        return {"competitions": competitions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get competitions: {str(e)}")

@app.post("/api/competitions")
async def create_competition(request: CompetitionRequest):
    """Create a new competition."""
    if not gamification:
        raise HTTPException(status_code=503, detail="Gamification not available")
    
    try:
        competition_id = await gamification.create_competition(
            request.name,
            request.description,
            request.category,
            request.humor_level,
            request.duration_days,
            request.max_participants,
            request.prize
        )
        
        return {"competition_id": competition_id, "message": "Competition created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create competition: {str(e)}")

# Analytics Endpoints
@app.get("/api/analytics/summary")
async def get_analytics_summary(days: int = Query(7)):
    """Get analytics summary."""
    if not analytics:
        raise HTTPException(status_code=503, detail="Analytics not available")
    
    try:
        summary = await analytics.get_analytics_summary(days)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@app.get("/api/analytics/performance")
async def get_performance_report(hours: int = Query(24)):
    """Get performance report."""
    if not analytics:
        raise HTTPException(status_code=503, detail="Analytics not available")
    
    try:
        report = await analytics.get_performance_report(hours)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance report: {str(e)}")

@app.get("/api/analytics/real-time")
async def get_real_time_stats():
    """Get real-time statistics."""
    if not analytics:
        raise HTTPException(status_code=503, detail="Analytics not available")
    
    try:
        stats = analytics.get_real_time_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time stats: {str(e)}")

# Cache Management Endpoints
@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Cache manager not available")
    
    try:
        stats = cache_manager.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all cache."""
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Cache manager not available")
    
    try:
        await cache_manager.joke_cache.clear_cache()
        cache_manager.api_cache.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

# Export/Import Endpoints
@app.get("/api/export/jokes")
async def export_jokes(format: str = Query("json")):
    """Export jokes."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        filename = await db.export_jokes(format)
        return {"filename": filename, "message": "Export completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export jokes: {str(e)}")

@app.post("/api/import/jokes")
async def import_jokes(file_path: str = Query(...)):
    """Import jokes from file."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        imported_count = await db.import_jokes(file_path)
        return {"imported_count": imported_count, "message": "Import completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import jokes: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return {"error": "Not found", "path": str(request.url)}

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    return {"error": "Internal server error", "path": str(request.url)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG)