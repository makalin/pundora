"""
Database models and management for Pundora.
"""

import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiofiles

class PundoraDB:
    """Database management for Pundora."""
    
    def __init__(self, db_path: str = "pundora.db"):
        """Initialize the database."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Jokes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jokes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                humor_level TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rating INTEGER DEFAULT 0,
                play_count INTEGER DEFAULT 0,
                is_favorite BOOLEAN DEFAULT FALSE
            )
        """)
        
        # User feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                joke_id INTEGER,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (joke_id) REFERENCES jokes (id)
            )
        """)
        
        # Joke history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS joke_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                joke_id INTEGER,
                user_session TEXT,
                action TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (joke_id) REFERENCES jokes (id)
            )
        """)
        
        # Statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT UNIQUE NOT NULL,
                metric_value INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Scheduled jokes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_jokes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                joke_id INTEGER,
                schedule_time TIMESTAMP NOT NULL,
                is_sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (joke_id) REFERENCES jokes (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def save_joke(self, joke_data: Dict[str, Any]) -> int:
        """Save a joke to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO jokes (content, category, humor_level, source)
            VALUES (?, ?, ?, ?)
        """, (
            joke_data['joke'],
            joke_data['category'],
            joke_data['humor_level'],
            joke_data['source']
        ))
        
        joke_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return joke_id
    
    async def get_joke_by_id(self, joke_id: int) -> Optional[Dict[str, Any]]:
        """Get a joke by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM jokes WHERE id = ?
        """, (joke_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'content': row[1],
                'category': row[2],
                'humor_level': row[3],
                'source': row[4],
                'created_at': row[5],
                'rating': row[6],
                'play_count': row[7],
                'is_favorite': bool(row[8])
            }
        return None
    
    async def get_favorite_jokes(self) -> List[Dict[str, Any]]:
        """Get all favorite jokes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM jokes WHERE is_favorite = TRUE
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'content': row[1],
            'category': row[2],
            'humor_level': row[3],
            'source': row[4],
            'created_at': row[5],
            'rating': row[6],
            'play_count': row[7],
            'is_favorite': bool(row[8])
        } for row in rows]
    
    async def toggle_favorite(self, joke_id: int) -> bool:
        """Toggle favorite status of a joke."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE jokes SET is_favorite = NOT is_favorite
            WHERE id = ?
        """, (joke_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    async def rate_joke(self, joke_id: int, rating: int, comment: str = "") -> bool:
        """Rate a joke (1-5 stars)."""
        if not 1 <= rating <= 5:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add feedback
        cursor.execute("""
            INSERT INTO feedback (joke_id, rating, comment)
            VALUES (?, ?, ?)
        """, (joke_id, rating, comment))
        
        # Update joke average rating
        cursor.execute("""
            UPDATE jokes SET rating = (
                SELECT AVG(rating) FROM feedback WHERE joke_id = ?
            ) WHERE id = ?
        """, (joke_id, joke_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    async def increment_play_count(self, joke_id: int):
        """Increment play count for a joke."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE jokes SET play_count = play_count + 1
            WHERE id = ?
        """, (joke_id,))
        
        conn.commit()
        conn.close()
    
    async def log_joke_action(self, joke_id: int, action: str, user_session: str = "default"):
        """Log a joke action."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO joke_history (joke_id, user_session, action)
            VALUES (?, ?, ?)
        """, (joke_id, user_session, action))
        
        conn.commit()
        conn.close()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get application statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get joke counts by category
        cursor.execute("""
            SELECT category, COUNT(*) FROM jokes GROUP BY category
        """)
        category_counts = dict(cursor.fetchall())
        
        # Get total jokes
        cursor.execute("SELECT COUNT(*) FROM jokes")
        total_jokes = cursor.fetchone()[0]
        
        # Get total plays
        cursor.execute("SELECT SUM(play_count) FROM jokes")
        total_plays = cursor.fetchone()[0] or 0
        
        # Get average rating
        cursor.execute("SELECT AVG(rating) FROM jokes WHERE rating > 0")
        avg_rating = cursor.fetchone()[0] or 0
        
        # Get top rated jokes
        cursor.execute("""
            SELECT content, rating FROM jokes 
            WHERE rating > 0 
            ORDER BY rating DESC 
            LIMIT 5
        """)
        top_jokes = [{'content': row[0], 'rating': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_jokes': total_jokes,
            'total_plays': total_plays,
            'average_rating': round(avg_rating, 2),
            'category_counts': category_counts,
            'top_jokes': top_jokes
        }
    
    async def get_recent_jokes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent jokes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM jokes 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'content': row[1],
            'category': row[2],
            'humor_level': row[3],
            'source': row[4],
            'created_at': row[5],
            'rating': row[6],
            'play_count': row[7],
            'is_favorite': bool(row[8])
        } for row in rows]
    
    async def search_jokes(self, query: str) -> List[Dict[str, Any]]:
        """Search jokes by content."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM jokes 
            WHERE content LIKE ? 
            ORDER BY created_at DESC
        """, (f"%{query}%",))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'content': row[1],
            'category': row[2],
            'humor_level': row[3],
            'source': row[4],
            'created_at': row[5],
            'rating': row[6],
            'play_count': row[7],
            'is_favorite': bool(row[8])
        } for row in rows]
    
    async def export_jokes(self, format: str = "json") -> str:
        """Export jokes to file."""
        jokes = await self.get_recent_jokes(1000)  # Export last 1000 jokes
        
        if format == "json":
            data = {
                'export_date': datetime.now().isoformat(),
                'total_jokes': len(jokes),
                'jokes': jokes
            }
            filename = f"pundora_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            async with aiofiles.open(filename, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            return filename
        
        elif format == "csv":
            import csv
            filename = f"pundora_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Content', 'Category', 'Humor Level', 'Source', 'Rating', 'Play Count', 'Favorite', 'Created At'])
                for joke in jokes:
                    writer.writerow([
                        joke['id'], joke['content'], joke['category'], 
                        joke['humor_level'], joke['source'], joke['rating'],
                        joke['play_count'], joke['is_favorite'], joke['created_at']
                    ])
            return filename
        
        return ""
    
    async def import_jokes(self, file_path: str) -> int:
        """Import jokes from file."""
        imported_count = 0
        
        if file_path.endswith('.json'):
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
                jokes = data.get('jokes', [])
                
                for joke in jokes:
                    await self.save_joke({
                        'joke': joke['content'],
                        'category': joke['category'],
                        'humor_level': joke['humor_level'],
                        'source': joke['source']
                    })
                    imported_count += 1
        
        return imported_count