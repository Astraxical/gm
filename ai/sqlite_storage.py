#!/usr/bin/env python3
"""
SQLite Storage Module

Long-term storage for campaign data, generated content, and AI learning.
Provides powerful querying and archival capabilities.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SQLiteStorage:
    """SQLite-based long-term storage."""
    
    def __init__(self, db_path: str = "ai_data/gm_campaign.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self) -> None:
        """Connect to database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        logger.debug(f"Connected to {self.db_path}")
    
    def _create_tables(self) -> None:
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Generated content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL,
                title TEXT NOT NULL,
                theme TEXT,
                created_at TEXT NOT NULL,
                data TEXT NOT NULL,
                used_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                tags TEXT
            )
        ''')
        
        # Campaign sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT NOT NULL,
                session_number INTEGER NOT NULL,
                title TEXT,
                date_played TEXT,
                summary TEXT,
                data TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Characters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                campaign_name TEXT,
                char_class TEXT,
                level INTEGER DEFAULT 1,
                player_name TEXT,
                created_at TEXT NOT NULL,
                last_updated TEXT,
                data TEXT
            )
        ''')
        
        # NPCs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS npcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                campaign_name TEXT,
                race TEXT,
                char_class TEXT,
                disposition TEXT DEFAULT 'neutral',
                created_at TEXT NOT NULL,
                last_seen TEXT,
                data TEXT
            )
        ''')
        
        # Locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                campaign_name TEXT,
                location_type TEXT,
                description TEXT,
                created_at TEXT NOT NULL,
                data TEXT
            )
        ''')
        
        # Plot threads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plot_threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                introduced_session INTEGER,
                resolved_session INTEGER,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            )
        ''')
        
        # AI feedback table (for learning)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                content_type TEXT,
                rating INTEGER,
                feedback_text TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (content_id) REFERENCES generated_content(id)
            )
        ''')
        
        # Pattern storage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_used TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    # ==================== Generated Content ====================
    
    def save_generated_content(
        self,
        content_type: str,
        title: str,
        data: Dict[str, Any],
        theme: str = "",
        tags: Optional[List[str]] = None
    ) -> int:
        """Save generated content."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO generated_content (content_type, title, theme, created_at, data, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            content_type,
            title,
            theme,
            datetime.now(timezone.utc).isoformat(),
            json.dumps(data),
            json.dumps(tags or [])
        ))
        
        self.conn.commit()
        content_id = cursor.lastrowid
        logger.debug(f"Saved {content_type}: {title} (id={content_id})")
        return content_id
    
    def get_generated_content(
        self,
        content_type: Optional[str] = None,
        theme: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get generated content with optional filters."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM generated_content WHERE 1=1"
        params = []
        
        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)
        
        if theme:
            query += " AND theme = ?"
            params.append(theme)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def rate_content(self, content_id: int, rating: int, feedback: str = "") -> None:
        """Rate generated content for AI learning."""
        cursor = self.conn.cursor()
        
        # Update content rating
        cursor.execute('''
            UPDATE generated_content 
            SET rating = (
                SELECT (AVG(rating) * used_count + ?) / (used_count + 1)
                FROM ai_feedback WHERE content_id = ?
            ),
            used_count = used_count + 1
            WHERE id = ?
        ''', (rating, content_id, content_id))
        
        # Save feedback
        cursor.execute('''
            INSERT INTO ai_feedback (content_id, rating, feedback_text, created_at)
            VALUES (?, ?, ?, ?)
        ''', (content_id, rating, feedback, datetime.now(timezone.utc).isoformat()))
        
        self.conn.commit()
        logger.debug(f"Rated content {content_id}: {rating}")
    
    # ==================== Campaign Sessions ====================
    
    def save_session(
        self,
        campaign_name: str,
        session_number: int,
        title: str,
        summary: str,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Save a campaign session."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO campaign_sessions 
            (campaign_name, session_number, title, date_played, summary, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            campaign_name,
            session_number,
            title,
            datetime.now(timezone.utc).isoformat(),
            summary,
            json.dumps(data or {}),
            datetime.now(timezone.utc).isoformat()
        ))
        
        self.conn.commit()
        logger.debug(f"Saved session {session_number} for {campaign_name}")
        return cursor.lastrowid
    
    def get_campaign_sessions(self, campaign_name: str) -> List[Dict[str, Any]]:
        """Get all sessions for a campaign."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM campaign_sessions 
            WHERE campaign_name = ?
            ORDER BY session_number
        ''', (campaign_name,))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Characters ====================
    
    def save_character(
        self,
        name: str,
        campaign_name: str,
        char_class: str,
        level: int,
        player_name: str = "",
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Save or update a character."""
        cursor = self.conn.cursor()
        
        # Check if exists
        cursor.execute('SELECT id FROM characters WHERE name = ? AND campaign_name = ?', 
                      (name, campaign_name))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE characters 
                SET level = ?, last_updated = ?, data = ?
                WHERE id = ?
            ''', (level, datetime.now(timezone.utc).isoformat(), 
                  json.dumps(data or {}), existing['id']))
            content_id = existing['id']
        else:
            cursor.execute('''
                INSERT INTO characters 
                (name, campaign_name, char_class, level, player_name, created_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, campaign_name, char_class, level, player_name,
                  datetime.now(timezone.utc).isoformat(), json.dumps(data or {})))
            content_id = cursor.lastrowid
        
        self.conn.commit()
        return content_id
    
    def get_characters(self, campaign_name: str) -> List[Dict[str, Any]]:
        """Get all characters for a campaign."""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM characters WHERE campaign_name = ?', 
                      (campaign_name,))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== NPCs ====================
    
    def save_npc(
        self,
        name: str,
        campaign_name: str,
        race: str = "",
        char_class: str = "",
        disposition: str = "neutral",
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Save or update an NPC."""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT id FROM npcs WHERE name = ? AND campaign_name = ?',
                      (name, campaign_name))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE npcs 
                SET disposition = ?, last_seen = ?, data = ?
                WHERE id = ?
            ''', (disposition, datetime.now(timezone.utc).isoformat(),
                  json.dumps(data or {}), existing['id']))
            content_id = existing['id']
        else:
            cursor.execute('''
                INSERT INTO npcs 
                (name, campaign_name, race, char_class, disposition, created_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, campaign_name, race, char_class, disposition,
                  datetime.now(timezone.utc).isoformat(), json.dumps(data or {})))
            content_id = cursor.lastrowid
        
        self.conn.commit()
        return content_id
    
    def get_npcs(self, campaign_name: str, disposition: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get NPCs for a campaign."""
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM npcs WHERE campaign_name = ?'
        params = [campaign_name]
        
        if disposition:
            query += ' AND disposition = ?'
            params.append(disposition)
        
        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Locations ====================
    
    def save_location(
        self,
        name: str,
        campaign_name: str,
        location_type: str,
        description: str = "",
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Save a location."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO locations 
            (name, campaign_name, location_type, description, created_at, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, campaign_name, location_type, description,
              datetime.now(timezone.utc).isoformat(), json.dumps(data or {})))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_locations(self, campaign_name: str) -> List[Dict[str, Any]]:
        """Get locations for a campaign."""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM locations WHERE campaign_name = ?',
                      (campaign_name,))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Plot Threads ====================
    
    def add_plot_thread(
        self,
        description: str,
        campaign_name: str = "",
        introduced_session: int = 1
    ) -> int:
        """Add a plot thread."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO plot_threads 
            (campaign_name, description, introduced_session, created_at)
            VALUES (?, ?, ?, ?)
        ''', (campaign_name, description, introduced_session,
              datetime.now(timezone.utc).isoformat()))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def resolve_plot_thread(self, thread_id: int, resolved_session: int) -> bool:
        """Mark a plot thread as resolved."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE plot_threads 
            SET status = 'resolved', resolved_session = ?, resolved_at = ?
            WHERE id = ?
        ''', (resolved_session, datetime.now(timezone.utc).isoformat(), thread_id))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_active_threads(self, campaign_name: str = "") -> List[Dict[str, Any]]:
        """Get active plot threads."""
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM plot_threads WHERE status = "active"'
        params = []
        
        if campaign_name:
            query += ' AND campaign_name = ?'
            params.append(campaign_name)
        
        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Patterns ====================
    
    def save_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        frequency: int = 1
    ) -> int:
        """Save a learned pattern."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO learned_patterns 
            (pattern_type, pattern_data, frequency, last_used, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (pattern_type, json.dumps(pattern_data), frequency,
              datetime.now(timezone.utc).isoformat(),
              datetime.now(timezone.utc).isoformat()))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_patterns(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Get patterns by type."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM learned_patterns 
            WHERE pattern_type = ?
            ORDER BY frequency DESC
        ''', (pattern_type,))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Utilities ====================
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to dictionary."""
        result = dict(row)
        
        # Parse JSON fields
        for key in ['data', 'pattern_data']:
            if key in result and result[key]:
                try:
                    result[key] = json.loads(result[key])
                except json.JSONDecodeError:
                    pass
        
        # Parse tags
        if 'tags' in result and result['tags']:
            try:
                result['tags'] = json.loads(result['tags'])
            except json.JSONDecodeError:
                pass
        
        return result
    
    def search_content(self, query: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search generated content."""
        cursor = self.conn.cursor()
        
        sql_query = '''
            SELECT * FROM generated_content 
            WHERE (title LIKE ? OR theme LIKE ? OR data LIKE ?)
        '''
        params = [f'%{query}%', f'%{query}%', f'%{query}%']
        
        if content_type:
            sql_query += ' AND content_type = ?'
            params.append(content_type)
        
        cursor.execute(sql_query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        tables = ['generated_content', 'campaign_sessions', 'characters', 
                  'npcs', 'locations', 'plot_threads', 'learned_patterns']
        
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            stats[table] = cursor.fetchone()[0]
        
        return stats
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()
