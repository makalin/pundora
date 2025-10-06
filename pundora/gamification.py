"""
Gamification and competition system for Pundora.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import sqlite3
from .database import PundoraDB

@dataclass
class UserScore:
    """User score and statistics."""
    user_id: str
    total_jokes_generated: int
    total_plays: int
    total_shares: int
    total_ratings: int
    average_rating: float
    favorite_count: int
    level: int
    experience_points: int
    badges: List[str]
    last_active: datetime

@dataclass
class Competition:
    """Joke competition."""
    id: int
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    category: str
    humor_level: str
    max_participants: int
    current_participants: int
    prize: str
    is_active: bool

@dataclass
class CompetitionEntry:
    """Competition entry."""
    id: int
    competition_id: int
    user_id: str
    joke_id: int
    votes: int
    created_at: datetime

class PundoraGamification:
    """Gamification system for Pundora."""
    
    def __init__(self, db: PundoraDB):
        """Initialize gamification system."""
        self.db = db
        self.init_gamification_tables()
        
        # Badge definitions
        self.badges = {
            'first_joke': {'name': 'First Laugh', 'description': 'Generated your first joke'},
            'joke_master': {'name': 'Joke Master', 'description': 'Generated 100 jokes'},
            'pun_lord': {'name': 'Pun Lord', 'description': 'Generated 50 pun jokes'},
            'voice_enthusiast': {'name': 'Voice Enthusiast', 'description': 'Generated 25 voice jokes'},
            'sharing_king': {'name': 'Sharing King', 'description': 'Shared 20 jokes'},
            'rating_expert': {'name': 'Rating Expert', 'description': 'Rated 50 jokes'},
            'daily_user': {'name': 'Daily User', 'description': 'Used Pundora for 7 consecutive days'},
            'category_explorer': {'name': 'Category Explorer', 'description': 'Generated jokes in all categories'},
            'humor_leveler': {'name': 'Humor Leveler', 'description': 'Generated jokes in all humor levels'},
            'competition_winner': {'name': 'Competition Winner', 'description': 'Won a joke competition'}
        }
        
        # Level requirements (XP needed for each level)
        self.level_requirements = {
            1: 0, 2: 100, 3: 250, 4: 500, 5: 1000,
            6: 2000, 7: 4000, 8: 8000, 9: 15000, 10: 30000
        }
    
    def init_gamification_tables(self):
        """Initialize gamification database tables."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # User scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_scores (
                user_id TEXT PRIMARY KEY,
                total_jokes_generated INTEGER DEFAULT 0,
                total_plays INTEGER DEFAULT 0,
                total_shares INTEGER DEFAULT 0,
                total_ratings INTEGER DEFAULT 0,
                average_rating REAL DEFAULT 0,
                favorite_count INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                experience_points INTEGER DEFAULT 0,
                badges TEXT DEFAULT '[]',
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Competitions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                category TEXT NOT NULL,
                humor_level TEXT NOT NULL,
                max_participants INTEGER DEFAULT 100,
                current_participants INTEGER DEFAULT 0,
                prize TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Competition entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competition_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                joke_id INTEGER NOT NULL,
                votes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (competition_id) REFERENCES competitions (id),
                FOREIGN KEY (joke_id) REFERENCES jokes (id)
            )
        """)
        
        # User achievements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                achievement_type TEXT NOT NULL,
                achievement_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def get_user_score(self, user_id: str) -> UserScore:
        """Get user score and statistics."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM user_scores WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return UserScore(
                user_id=row[0],
                total_jokes_generated=row[1],
                total_plays=row[2],
                total_shares=row[3],
                total_ratings=row[4],
                average_rating=row[5],
                favorite_count=row[6],
                level=row[7],
                experience_points=row[8],
                badges=json.loads(row[9]) if row[9] else [],
                last_active=datetime.fromisoformat(row[10])
            )
        else:
            # Create new user score
            return await self.create_user_score(user_id)
    
    async def create_user_score(self, user_id: str) -> UserScore:
        """Create a new user score."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_scores (user_id) VALUES (?)
        """, (user_id,))
        
        conn.commit()
        conn.close()
        
        return await self.get_user_score(user_id)
    
    async def add_experience(self, user_id: str, xp: int, action: str) -> Dict[str, Any]:
        """Add experience points to user."""
        score = await self.get_user_score(user_id)
        
        # Calculate XP multiplier based on action
        multipliers = {
            'generate_joke': 10,
            'play_joke': 5,
            'share_joke': 15,
            'rate_joke': 8,
            'favorite_joke': 12,
            'win_competition': 100,
            'daily_login': 20
        }
        
        xp_gained = xp * multipliers.get(action, 1)
        new_xp = score.experience_points + xp_gained
        new_level = self._calculate_level(new_xp)
        
        # Update user score
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_scores 
            SET experience_points = ?, level = ?, last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_xp, new_level, user_id))
        
        conn.commit()
        conn.close()
        
        # Check for level up
        level_up = new_level > score.level
        new_badges = []
        
        if level_up:
            new_badges = await self._check_badges(user_id, new_level)
        
        return {
            'xp_gained': xp_gained,
            'new_xp': new_xp,
            'new_level': new_level,
            'level_up': level_up,
            'new_badges': new_badges
        }
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate level based on XP."""
        level = 1
        for req_level, req_xp in self.level_requirements.items():
            if xp >= req_xp:
                level = req_level
        return level
    
    async def _check_badges(self, user_id: str, level: int) -> List[str]:
        """Check for new badges."""
        score = await self.get_user_score(user_id)
        new_badges = []
        
        # Check level-based badges
        if level >= 5 and 'joke_master' not in score.badges:
            new_badges.append('joke_master')
        
        if level >= 10 and 'pun_lord' not in score.badges:
            new_badges.append('pun_lord')
        
        # Add new badges to user
        if new_badges:
            all_badges = score.badges + new_badges
            
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_scores SET badges = ? WHERE user_id = ?
            """, (json.dumps(all_badges), user_id))
            
            conn.commit()
            conn.close()
        
        return new_badges
    
    async def create_competition(
        self,
        name: str,
        description: str,
        category: str,
        humor_level: str,
        duration_days: int = 7,
        max_participants: int = 100,
        prize: str = "Bragging Rights"
    ) -> int:
        """Create a new joke competition."""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO competitions 
            (name, description, start_date, end_date, category, humor_level, max_participants, prize)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, start_date, end_date, category, humor_level, max_participants, prize))
        
        competition_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return competition_id
    
    async def join_competition(self, competition_id: int, user_id: str, joke_id: int) -> bool:
        """Join a competition with a joke."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Check if competition is active and has space
        cursor.execute("""
            SELECT is_active, current_participants, max_participants
            FROM competitions WHERE id = ?
        """, (competition_id,))
        
        row = cursor.fetchone()
        if not row or not row[0] or row[1] >= row[2]:
            conn.close()
            return False
        
        # Check if user already joined
        cursor.execute("""
            SELECT id FROM competition_entries 
            WHERE competition_id = ? AND user_id = ?
        """, (competition_id, user_id))
        
        if cursor.fetchone():
            conn.close()
            return False
        
        # Add entry
        cursor.execute("""
            INSERT INTO competition_entries (competition_id, user_id, joke_id)
            VALUES (?, ?, ?)
        """, (competition_id, user_id, joke_id))
        
        # Update participant count
        cursor.execute("""
            UPDATE competitions SET current_participants = current_participants + 1
            WHERE id = ?
        """, (competition_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    async def vote_on_competition_entry(self, entry_id: int, user_id: str) -> bool:
        """Vote on a competition entry."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Add vote
        cursor.execute("""
            UPDATE competition_entries SET votes = votes + 1 WHERE id = ?
        """, (entry_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    async def get_competition_leaderboard(self, competition_id: int) -> List[Dict[str, Any]]:
        """Get competition leaderboard."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ce.id, ce.user_id, ce.votes, j.content, j.category, j.humor_level
            FROM competition_entries ce
            JOIN jokes j ON ce.joke_id = j.id
            WHERE ce.competition_id = ?
            ORDER BY ce.votes DESC
        """, (competition_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'entry_id': row[0],
            'user_id': row[1],
            'votes': row[2],
            'joke': row[3],
            'category': row[4],
            'humor_level': row[5]
        } for row in rows]
    
    async def get_active_competitions(self) -> List[Competition]:
        """Get active competitions."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, start_date, end_date, category, humor_level,
                   max_participants, current_participants, prize, is_active
            FROM competitions
            WHERE is_active = TRUE AND end_date > CURRENT_TIMESTAMP
            ORDER BY start_date ASC
        """, ())
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Competition(
            id=row[0],
            name=row[1],
            description=row[2],
            start_date=datetime.fromisoformat(row[3]),
            end_date=datetime.fromisoformat(row[4]),
            category=row[5],
            humor_level=row[6],
            max_participants=row[7],
            current_participants=row[8],
            prize=row[9],
            is_active=bool(row[10])
        ) for row in rows]
    
    async def get_global_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get global leaderboard."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, total_jokes_generated, total_plays, total_shares,
                   average_rating, level, experience_points
            FROM user_scores
            ORDER BY experience_points DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'user_id': row[0],
            'jokes_generated': row[1],
            'total_plays': row[2],
            'total_shares': row[3],
            'average_rating': row[4],
            'level': row[5],
            'experience_points': row[6]
        } for row in rows]
    
    async def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user achievements."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT achievement_type, achievement_data, created_at
            FROM user_achievements
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'type': row[0],
            'data': json.loads(row[1]) if row[1] else {},
            'created_at': row[2]
        } for row in rows]
    
    async def record_achievement(self, user_id: str, achievement_type: str, data: Dict[str, Any] = None):
        """Record a user achievement."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_achievements (user_id, achievement_type, achievement_data)
            VALUES (?, ?, ?)
        """, (user_id, achievement_type, json.dumps(data or {})))
        
        conn.commit()
        conn.close()
    
    def get_badge_info(self, badge_id: str) -> Dict[str, str]:
        """Get badge information."""
        return self.badges.get(badge_id, {'name': 'Unknown Badge', 'description': 'Unknown'})
    
    async def get_daily_challenges(self) -> List[Dict[str, Any]]:
        """Get daily challenges for users."""
        return [
            {
                'id': 'daily_joke',
                'name': 'Daily Joke',
                'description': 'Generate a joke today',
                'xp_reward': 20,
                'type': 'generate_joke'
            },
            {
                'id': 'share_joke',
                'name': 'Share the Laugh',
                'description': 'Share a joke with friends',
                'xp_reward': 30,
                'type': 'share_joke'
            },
            {
                'id': 'rate_jokes',
                'name': 'Joke Critic',
                'description': 'Rate 5 jokes today',
                'xp_reward': 40,
                'type': 'rate_jokes'
            },
            {
                'id': 'explore_categories',
                'name': 'Category Explorer',
                'description': 'Generate jokes in 3 different categories',
                'xp_reward': 50,
                'type': 'explore_categories'
            }
        ]