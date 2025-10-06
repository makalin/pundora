"""
Analytics and monitoring system for Pundora.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import sqlite3
from collections import defaultdict, Counter
import asyncio

@dataclass
class AnalyticsEvent:
    """Analytics event."""
    event_type: str
    user_id: str
    timestamp: datetime
    data: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    """Performance metrics."""
    endpoint: str
    response_time: float
    status_code: int
    timestamp: datetime
    user_id: Optional[str] = None

class PundoraAnalytics:
    """Analytics and monitoring system."""
    
    def __init__(self, db_path: str = "pundora_analytics.db"):
        """Initialize analytics system."""
        self.db_path = db_path
        self.init_analytics_db()
        self.real_time_stats = defaultdict(int)
        self.performance_metrics = []
    
    def init_analytics_db(self):
        """Initialize analytics database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                response_time REAL NOT NULL,
                status_code INTEGER NOT NULL,
                user_id TEXT,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER,
                page_views INTEGER DEFAULT 0,
                jokes_generated INTEGER DEFAULT 0,
                jokes_played INTEGER DEFAULT 0,
                jokes_shared INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Error logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                user_id TEXT,
                endpoint TEXT,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON analytics_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON analytics_events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON analytics_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_endpoint ON performance_metrics(endpoint)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_metrics(timestamp)")
        
        conn.commit()
        conn.close()
    
    async def track_event(
        self, 
        event_type: str, 
        user_id: str, 
        data: Dict[str, Any] = None
    ):
        """Track an analytics event."""
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            timestamp=datetime.now(),
            data=data or {}
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO analytics_events (event_type, user_id, timestamp, data)
            VALUES (?, ?, ?, ?)
        """, (event.event_type, event.user_id, event.timestamp, json.dumps(event.data)))
        
        conn.commit()
        conn.close()
        
        # Update real-time stats
        self.real_time_stats[event_type] += 1
    
    async def track_performance(
        self, 
        endpoint: str, 
        response_time: float, 
        status_code: int, 
        user_id: str = None
    ):
        """Track performance metrics."""
        metric = PerformanceMetrics(
            endpoint=endpoint,
            response_time=response_time,
            status_code=status_code,
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance_metrics (endpoint, response_time, status_code, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (metric.endpoint, metric.response_time, metric.status_code, metric.user_id, metric.timestamp))
        
        conn.commit()
        conn.close()
        
        # Keep recent metrics in memory for quick access
        self.performance_metrics.append(metric)
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-500:]
    
    async def track_error(
        self, 
        error_type: str, 
        error_message: str, 
        stack_trace: str = None,
        user_id: str = None,
        endpoint: str = None
    ):
        """Track error occurrences."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO error_logs (error_type, error_message, stack_trace, user_id, endpoint, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (error_type, error_message, stack_trace, user_id, endpoint, datetime.now()))
        
        conn.commit()
        conn.close()
    
    async def start_user_session(self, user_id: str, session_id: str) -> int:
        """Start a user session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_sessions (user_id, session_id, start_time)
            VALUES (?, ?, ?)
        """, (user_id, session_id, datetime.now()))
        
        session_db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_db_id
    
    async def end_user_session(self, session_id: str):
        """End a user session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get session start time
        cursor.execute("""
            SELECT start_time FROM user_sessions WHERE session_id = ? AND end_time IS NULL
        """, (session_id,))
        
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row[0])
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            cursor.execute("""
                UPDATE user_sessions 
                SET end_time = ?, duration = ?
                WHERE session_id = ?
            """, (end_time, duration, session_id))
        
        conn.commit()
        conn.close()
    
    async def update_session_metrics(self, session_id: str, **metrics):
        """Update session metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        for key, value in metrics.items():
            if key in ['page_views', 'jokes_generated', 'jokes_played', 'jokes_shared']:
                update_fields.append(f"{key} = {key} + ?")
                values.append(value)
        
        if update_fields:
            values.append(session_id)
            query = f"UPDATE user_sessions SET {', '.join(update_fields)} WHERE session_id = ?"
            cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    async def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics summary for specified days."""
        start_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Event counts by type
        cursor.execute("""
            SELECT event_type, COUNT(*) FROM analytics_events
            WHERE timestamp >= ? GROUP BY event_type
        """, (start_date,))
        event_counts = dict(cursor.fetchall())
        
        # Total events
        cursor.execute("""
            SELECT COUNT(*) FROM analytics_events WHERE timestamp >= ?
        """, (start_date,))
        total_events = cursor.fetchone()[0]
        
        # Unique users
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM analytics_events WHERE timestamp >= ?
        """, (start_date,))
        unique_users = cursor.fetchone()[0]
        
        # Performance metrics
        cursor.execute("""
            SELECT AVG(response_time), COUNT(*) FROM performance_metrics
            WHERE timestamp >= ?
        """, (start_date,))
        avg_response_time, total_requests = cursor.fetchone()
        
        # Error count
        cursor.execute("""
            SELECT COUNT(*) FROM error_logs WHERE timestamp >= ?
        """, (start_date,))
        error_count = cursor.fetchone()[0]
        
        # Session statistics
        cursor.execute("""
            SELECT COUNT(*), AVG(duration), SUM(jokes_generated), SUM(jokes_played), SUM(jokes_shared)
            FROM user_sessions WHERE start_time >= ?
        """, (start_date,))
        session_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'period_days': days,
            'total_events': total_events,
            'unique_users': unique_users,
            'event_counts': event_counts,
            'performance': {
                'avg_response_time': round(avg_response_time or 0, 3),
                'total_requests': total_requests or 0
            },
            'errors': error_count,
            'sessions': {
                'total_sessions': session_stats[0] or 0,
                'avg_duration': round(session_stats[1] or 0, 2),
                'total_jokes_generated': session_stats[2] or 0,
                'total_jokes_played': session_stats[3] or 0,
                'total_jokes_shared': session_stats[4] or 0
            },
            'real_time_stats': dict(self.real_time_stats)
        }
    
    async def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for a specific user."""
        start_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User events
        cursor.execute("""
            SELECT event_type, COUNT(*) FROM analytics_events
            WHERE user_id = ? AND timestamp >= ? GROUP BY event_type
        """, (user_id, start_date))
        user_events = dict(cursor.fetchall())
        
        # User sessions
        cursor.execute("""
            SELECT COUNT(*), AVG(duration), SUM(jokes_generated), SUM(jokes_played), SUM(jokes_shared)
            FROM user_sessions WHERE user_id = ? AND start_time >= ?
        """, (user_id, start_date))
        session_stats = cursor.fetchone()
        
        # User performance
        cursor.execute("""
            SELECT AVG(response_time), COUNT(*) FROM performance_metrics
            WHERE user_id = ? AND timestamp >= ?
        """, (user_id, start_date))
        perf_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'user_id': user_id,
            'period_days': days,
            'events': user_events,
            'sessions': {
                'total_sessions': session_stats[0] or 0,
                'avg_duration': round(session_stats[1] or 0, 2),
                'jokes_generated': session_stats[2] or 0,
                'jokes_played': session_stats[3] or 0,
                'jokes_shared': session_stats[4] or 0
            },
            'performance': {
                'avg_response_time': round(perf_stats[0] or 0, 3),
                'total_requests': perf_stats[1] or 0
            }
        }
    
    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance report."""
        start_time = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance by endpoint
        cursor.execute("""
            SELECT endpoint, AVG(response_time), COUNT(*), 
                   MIN(response_time), MAX(response_time)
            FROM performance_metrics
            WHERE timestamp >= ? GROUP BY endpoint
        """, (start_time,))
        
        endpoint_stats = []
        for row in cursor.fetchall():
            endpoint_stats.append({
                'endpoint': row[0],
                'avg_response_time': round(row[1], 3),
                'request_count': row[2],
                'min_response_time': round(row[3], 3),
                'max_response_time': round(row[4], 3)
            })
        
        # Status code distribution
        cursor.execute("""
            SELECT status_code, COUNT(*) FROM performance_metrics
            WHERE timestamp >= ? GROUP BY status_code
        """, (start_time,))
        status_codes = dict(cursor.fetchall())
        
        # Recent errors
        cursor.execute("""
            SELECT error_type, COUNT(*) FROM error_logs
            WHERE timestamp >= ? GROUP BY error_type
        """, (start_time,))
        recent_errors = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'period_hours': hours,
            'endpoint_performance': endpoint_stats,
            'status_codes': status_codes,
            'recent_errors': recent_errors,
            'memory_metrics': self.performance_metrics[-100:] if self.performance_metrics else []
        }
    
    async def get_trending_data(self, metric: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get trending data for a metric."""
        start_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if metric == 'events':
            cursor.execute("""
                SELECT DATE(timestamp) as date, event_type, COUNT(*) as count
                FROM analytics_events
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp), event_type
                ORDER BY date
            """, (start_date,))
        elif metric == 'performance':
            cursor.execute("""
                SELECT DATE(timestamp) as date, AVG(response_time) as avg_time, COUNT(*) as count
                FROM performance_metrics
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (start_date,))
        elif metric == 'sessions':
            cursor.execute("""
                SELECT DATE(start_time) as date, COUNT(*) as count, AVG(duration) as avg_duration
                FROM user_sessions
                WHERE start_time >= ?
                GROUP BY DATE(start_time)
                ORDER BY date
            """, (start_date,))
        else:
            conn.close()
            return []
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    async def export_analytics(self, format: str = "json", days: int = 30) -> str:
        """Export analytics data."""
        start_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all events
        cursor.execute("""
            SELECT event_type, user_id, timestamp, data
            FROM analytics_events WHERE timestamp >= ?
            ORDER BY timestamp
        """, (start_date,))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'event_type': row[0],
                'user_id': row[1],
                'timestamp': row[2],
                'data': json.loads(row[3])
            })
        
        conn.close()
        
        if format == "json":
            filename = f"pundora_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'export_date': datetime.now().isoformat(),
                    'period_days': days,
                    'events': events
                }, f, indent=2)
            return filename
        
        return ""
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics."""
        return {
            'current_stats': dict(self.real_time_stats),
            'performance_metrics_count': len(self.performance_metrics),
            'timestamp': datetime.now().isoformat()
        }
    
    async def cleanup_old_data(self, days: int = 90):
        """Clean up old analytics data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clean up old events
        cursor.execute("DELETE FROM analytics_events WHERE timestamp < ?", (cutoff_date,))
        events_deleted = cursor.rowcount
        
        # Clean up old performance metrics
        cursor.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_date,))
        metrics_deleted = cursor.rowcount
        
        # Clean up old error logs
        cursor.execute("DELETE FROM error_logs WHERE timestamp < ?", (cutoff_date,))
        errors_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {
            'events_deleted': events_deleted,
            'metrics_deleted': metrics_deleted,
            'errors_deleted': errors_deleted
        }