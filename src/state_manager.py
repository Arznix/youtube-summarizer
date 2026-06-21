import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging


class StateManager:
    """Manages SQLite state for tracking video processing."""
    
    def __init__(self, db_path: Path):
        """
        Initialize state manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    channel_name TEXT NOT NULL,
                    video_title TEXT NOT NULL,
                    published_timestamp TEXT NOT NULL,
                    summary_status TEXT NOT NULL DEFAULT 'PENDING',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_status 
                ON videos(summary_status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_videos_channel 
                ON videos(channel_name)
            ''')
            
            conn.commit()
            
            self.logger.info(f"Database initialized at {self.db_path}")
    
    def video_exists(self, video_id: str) -> bool:
        """
        Check if video exists in database.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if video exists, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM videos WHERE video_id = ?",
                (video_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0
    
    def add_video(
        self,
        video_id: str,
        channel_name: str,
        video_title: str,
        published_timestamp: str,
        summary_status: str = "PENDING"
    ) -> bool:
        """
        Add a new video to the database.
        
        Args:
            video_id: YouTube video ID
            channel_name: Name of the YouTube channel
            video_title: Title of the video
            published_timestamp: When the video was published
            summary_status: Initial status (PENDING, PROCESSING, COMPLETED, FAILED)
            
        Returns:
            True if video was added, False if it already exists
        """
        if self.video_exists(video_id):
            self.logger.debug(f"Video {video_id} already exists in database")
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            now = datetime.utcnow().isoformat()
            
            cursor.execute('''
                INSERT INTO videos (
                    video_id, channel_name, video_title, 
                    published_timestamp, summary_status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id, channel_name, video_title,
                published_timestamp, summary_status,
                now, now
            ))
            
            conn.commit()
            
            self.logger.info(f"Added video {video_id} to database")
            return True
    
    def update_video_status(self, video_id: str, status: str) -> bool:
        """
        Update video processing status.
        
        Args:
            video_id: YouTube video ID
            video_id: New status (PENDING, PROCESSING, COMPLETED, FAILED)
            
        Returns:
            True if video was updated, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            now = datetime.utcnow().isoformat()
            
            cursor.execute('''
                UPDATE videos 
                SET summary_status = ?, updated_at = ?
                WHERE video_id = ?
            ''', (status, now, video_id))
            
            conn.commit()
            
            updated = cursor.rowcount > 0
            if updated:
                self.logger.info(f"Updated video {video_id} status to {status}")
            else:
                self.logger.warning(f"Video {video_id} not found for status update")
            
            return updated
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video information from database.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video information dictionary or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM videos WHERE video_id = ?",
                (video_id,)
            )
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_videos_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get all videos with a specific status.
        
        Args:
            status: Status to filter by (PENDING, PROCESSING, COMPLETED, FAILED)
            
        Returns:
            List of video information dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM videos WHERE summary_status = ?",
                (status,)
            )
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_pending_videos(self) -> List[Dict[str, Any]]:
        """Get all videos with PENDING status."""
        return self.get_videos_by_status("PENDING")
    
    def get_failed_videos(self) -> List[Dict[str, Any]]:
        """Get all videos with FAILED status."""
        return self.get_videos_by_status("FAILED")
    
    def get_completed_videos(self) -> List[Dict[str, Any]]:
        """Get all videos with COMPLETED status."""
        return self.get_videos_by_status("COMPLETED")
    
    def delete_video(self, video_id: str) -> bool:
        """
        Delete a video from the database.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if video was deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM videos WHERE video_id = ?",
                (video_id,)
            )
            
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.info(f"Deleted video {video_id} from database")
            else:
                self.logger.warning(f"Video {video_id} not found for deletion")
            
            return deleted
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Statistics dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total videos
            cursor.execute("SELECT COUNT(*) FROM videos")
            total_videos = cursor.fetchone()[0]
            
            # Videos by status
            cursor.execute('''
                SELECT summary_status, COUNT(*) 
                FROM videos 
                GROUP BY summary_status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # Videos by channel
            cursor.execute('''
                SELECT channel_name, COUNT(*) 
                FROM videos 
                GROUP BY channel_name
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''')
            channel_counts = dict(cursor.fetchall())
            
            return {
                "total_videos": total_videos,
                "pending": status_counts.get("PENDING", 0),
                "processing": status_counts.get("PROCESSING", 0),
                "completed": status_counts.get("COMPLETED", 0),
                "failed": status_counts.get("FAILED", 0),
                "channels": channel_counts
            }
    
    def reset_failed_videos(self) -> int:
        """
        Reset all failed videos to PENDING status.
        
        Returns:
            Number of videos reset
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            now = datetime.utcnow().isoformat()
            
            cursor.execute('''
                UPDATE videos 
                SET summary_status = 'PENDING', updated_at = ?
                WHERE summary_status = 'FAILED'
            ''', (now,))
            
            conn.commit()
            
            reset_count = cursor.rowcount
            if reset_count > 0:
                self.logger.info(f"Reset {reset_count} failed videos to PENDING")
            
            return reset_count
    
    def get_old_videos(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get videos older than specified days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of old video information dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cutoff_date = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            from datetime import timedelta
            cutoff_date -= timedelta(days=days)
            cutoff_iso = cutoff_date.isoformat()
            
            cursor.execute('''
                SELECT * FROM videos 
                WHERE created_at < ?
                ORDER BY created_at ASC
            ''', (cutoff_iso,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]