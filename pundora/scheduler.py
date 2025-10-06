"""
Joke scheduling and notification system for Pundora.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import sqlite3
from .database import PundoraDB

@dataclass
class JokeSchedule:
    """Represents a scheduled joke."""
    id: int
    joke_id: int
    schedule_time: datetime
    is_sent: bool
    created_at: datetime
    user_email: Optional[str] = None
    notification_type: str = "email"  # email, webhook, sms
    webhook_url: Optional[str] = None

class JokeScheduler:
    """Handle joke scheduling and notifications."""
    
    def __init__(self, db: PundoraDB):
        """Initialize the scheduler."""
        self.db = db
        self.running = False
        self.tasks = []
    
    async def schedule_joke(
        self,
        joke_id: int,
        schedule_time: datetime,
        user_email: Optional[str] = None,
        notification_type: str = "email",
        webhook_url: Optional[str] = None
    ) -> int:
        """Schedule a joke for delivery."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO scheduled_jokes (joke_id, schedule_time, user_email, notification_type, webhook_url)
            VALUES (?, ?, ?, ?, ?)
        """, (joke_id, schedule_time, user_email, notification_type, webhook_url))
        
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return schedule_id
    
    async def get_scheduled_jokes(self, limit: int = 50) -> List[JokeSchedule]:
        """Get upcoming scheduled jokes."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, joke_id, schedule_time, is_sent, created_at, user_email, notification_type, webhook_url
            FROM scheduled_jokes
            WHERE is_sent = FALSE
            ORDER BY schedule_time ASC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [JokeSchedule(
            id=row[0],
            joke_id=row[1],
            schedule_time=datetime.fromisoformat(row[2]),
            is_sent=bool(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            user_email=row[5],
            notification_type=row[6] or "email",
            webhook_url=row[7]
        ) for row in rows]
    
    async def mark_joke_sent(self, schedule_id: int) -> bool:
        """Mark a scheduled joke as sent."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scheduled_jokes SET is_sent = TRUE WHERE id = ?
        """, (schedule_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    async def cancel_scheduled_joke(self, schedule_id: int) -> bool:
        """Cancel a scheduled joke."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM scheduled_jokes WHERE id = ? AND is_sent = FALSE
        """, (schedule_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    async def start_scheduler(self):
        """Start the joke scheduler."""
        if self.running:
            return
        
        self.running = True
        print("🕐 Joke scheduler started")
        
        # Start the main scheduling loop
        task = asyncio.create_task(self._scheduler_loop())
        self.tasks.append(task)
    
    async def stop_scheduler(self):
        """Stop the joke scheduler."""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        self.tasks.clear()
        print("🛑 Joke scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._process_due_jokes()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def _process_due_jokes(self):
        """Process jokes that are due for delivery."""
        now = datetime.now()
        
        # Get jokes due in the next minute
        due_time = now + timedelta(minutes=1)
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, joke_id, user_email, notification_type, webhook_url
            FROM scheduled_jokes
            WHERE is_sent = FALSE AND schedule_time <= ?
        """, (due_time,))
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            schedule_id, joke_id, user_email, notification_type, webhook_url = row
            
            try:
                # Get the joke
                joke_data = await self.db.get_joke_by_id(joke_id)
                if not joke_data:
                    continue
                
                # Send notification
                success = await self._send_notification(
                    joke_data, user_email, notification_type, webhook_url
                )
                
                if success:
                    await self.mark_joke_sent(schedule_id)
                    print(f"✅ Joke {joke_id} sent successfully")
                else:
                    print(f"❌ Failed to send joke {joke_id}")
                    
            except Exception as e:
                print(f"Error processing joke {joke_id}: {e}")
    
    async def _send_notification(
        self,
        joke_data: Dict[str, Any],
        user_email: Optional[str],
        notification_type: str,
        webhook_url: Optional[str]
    ) -> bool:
        """Send notification for a joke."""
        try:
            if notification_type == "email" and user_email:
                return await self._send_email_notification(joke_data, user_email)
            elif notification_type == "webhook" and webhook_url:
                return await self._send_webhook_notification(joke_data, webhook_url)
            elif notification_type == "sms" and user_email:  # Using email as phone for demo
                return await self._send_sms_notification(joke_data, user_email)
            else:
                print(f"Invalid notification type or missing data: {notification_type}")
                return False
        except Exception as e:
            print(f"Notification error: {e}")
            return False
    
    async def _send_email_notification(self, joke_data: Dict[str, Any], user_email: str) -> bool:
        """Send email notification."""
        # This would integrate with an email service
        print(f"📧 Email notification sent to {user_email}: {joke_data['joke'][:50]}...")
        return True
    
    async def _send_webhook_notification(self, joke_data: Dict[str, Any], webhook_url: str) -> bool:
        """Send webhook notification."""
        try:
            import httpx
            
            payload = {
                "joke": joke_data['joke'],
                "category": joke_data['category'],
                "humor_level": joke_data['humor_level'],
                "source": joke_data['source'],
                "timestamp": datetime.now().isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
            
            print(f"🔗 Webhook notification sent to {webhook_url}")
            return True
        except Exception as e:
            print(f"Webhook error: {e}")
            return False
    
    async def _send_sms_notification(self, joke_data: Dict[str, Any], phone_number: str) -> bool:
        """Send SMS notification."""
        # This would integrate with an SMS service
        print(f"📱 SMS notification sent to {phone_number}: {joke_data['joke'][:50]}...")
        return True
    
    async def schedule_daily_jokes(
        self,
        user_email: str,
        time: str = "09:00",
        categories: List[str] = None,
        humor_level: str = "medium"
    ) -> int:
        """Schedule daily jokes for a user."""
        if categories is None:
            categories = ["general"]
        
        # Calculate next delivery time
        now = datetime.now()
        hour, minute = map(int, time.split(':'))
        next_delivery = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_delivery <= now:
            next_delivery += timedelta(days=1)
        
        # For demo, schedule one joke
        # In a real implementation, you'd schedule multiple jokes
        from .joke_generator import JokeGenerator
        
        joke_gen = JokeGenerator()
        joke_data = await joke_gen.generate_joke(
            category=categories[0],
            humor_level=humor_level
        )
        
        # Save joke to database
        joke_id = await self.db.save_joke(joke_data)
        
        # Schedule delivery
        schedule_id = await self.schedule_joke(
            joke_id=joke_id,
            schedule_time=next_delivery,
            user_email=user_email,
            notification_type="email"
        )
        
        return schedule_id
    
    async def get_user_schedules(self, user_email: str) -> List[JokeSchedule]:
        """Get all schedules for a user."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, joke_id, schedule_time, is_sent, created_at, user_email, notification_type, webhook_url
            FROM scheduled_jokes
            WHERE user_email = ?
            ORDER BY schedule_time DESC
        """, (user_email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [JokeSchedule(
            id=row[0],
            joke_id=row[1],
            schedule_time=datetime.fromisoformat(row[2]),
            is_sent=bool(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            user_email=row[5],
            notification_type=row[6] or "email",
            webhook_url=row[7]
        ) for row in rows]
    
    async def create_recurring_schedule(
        self,
        user_email: str,
        frequency: str,  # daily, weekly, monthly
        time: str = "09:00",
        categories: List[str] = None,
        humor_level: str = "medium"
    ) -> List[int]:
        """Create a recurring joke schedule."""
        if categories is None:
            categories = ["general"]
        
        schedule_ids = []
        
        if frequency == "daily":
            # Schedule for next 30 days
            for i in range(30):
                schedule_id = await self.schedule_daily_jokes(
                    user_email, time, categories, humor_level
                )
                schedule_ids.append(schedule_id)
        
        elif frequency == "weekly":
            # Schedule for next 12 weeks
            for i in range(12):
                schedule_id = await self.schedule_daily_jokes(
                    user_email, time, categories, humor_level
                )
                schedule_ids.append(schedule_id)
        
        elif frequency == "monthly":
            # Schedule for next 12 months
            for i in range(12):
                schedule_id = await self.schedule_daily_jokes(
                    user_email, time, categories, humor_level
                )
                schedule_ids.append(schedule_id)
        
        return schedule_ids