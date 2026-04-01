#!/usr/bin/env python3
"""
DnD GM Toolkit - Enhanced Database Manager

Shared database layer for both TUI and GUI frontends.
Provides high-level operations for campaign data access.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Enhanced database manager for GM Toolkit."""
    
    DEFAULT_DB_PATH = "ai_data/gm_campaign.db"
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path or self.DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_cursor(self):
        """Get database cursor with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database tables."""
        with self.get_cursor() as cursor:
            # Campaigns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    last_played TEXT,
                    settings TEXT
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    session_number INTEGER NOT NULL,
                    title TEXT,
                    date_played TEXT,
                    summary TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                )
            ''')
            
            # Characters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    name TEXT NOT NULL,
                    player_name TEXT,
                    char_class TEXT,
                    race TEXT,
                    level INTEGER DEFAULT 1,
                    hp_max INTEGER,
                    hp_current INTEGER,
                    ac INTEGER,
                    data TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                )
            ''')
            
            # NPCs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS npcs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    name TEXT NOT NULL,
                    race TEXT,
                    char_class TEXT,
                    disposition TEXT DEFAULT 'neutral',
                    location TEXT,
                    description TEXT,
                    data TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                )
            ''')
            
            # Locations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    name TEXT NOT NULL,
                    location_type TEXT,
                    description TEXT,
                    parent_location TEXT,
                    data TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                )
            ''')
            
            # Plot threads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plot_threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    priority TEXT DEFAULT 'normal',
                    introduced_session INTEGER,
                    resolved_session INTEGER,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                )
            ''')
            
            # Generated content library
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_library (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    theme TEXT,
                    difficulty TEXT,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    used_count INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0,
                    tags TEXT,
                    campaign_id INTEGER,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                )
            ''')
            
            # Session events log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    round_num INTEGER,
                    participants TEXT,
                    result TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            ''')
            
            logger.info(f"Database initialized at {self.db_path}")
    
    # ==================== Campaign Operations ====================
    
    def create_campaign(self, name: str, description: str = "", settings: Dict = None) -> int:
        """Create a new campaign."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO campaigns (name, description, created_at, settings)
                VALUES (?, ?, ?, ?)
            ''', (name, description, datetime.now(timezone.utc).isoformat(),
                  json.dumps(settings or {})))
            return cursor.lastrowid
    
    def get_campaign(self, campaign_id: int = None, name: str = None) -> Optional[Dict]:
        """Get campaign by ID or name."""
        with self.get_cursor() as cursor:
            if campaign_id:
                cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
            elif name:
                cursor.execute('SELECT * FROM campaigns WHERE name = ?', (name,))
            else:
                return None
            
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
        return None
    
    def list_campaigns(self) -> List[Dict]:
        """List all campaigns."""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM campaigns ORDER BY last_played DESC')
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def delete_campaign(self, campaign_id: int) -> bool:
        """Delete a campaign and all related data."""
        with self.get_cursor() as cursor:
            # Delete related data first (foreign keys)
            cursor.execute('DELETE FROM sessions WHERE campaign_id = ?', (campaign_id,))
            cursor.execute('DELETE FROM characters WHERE campaign_id = ?', (campaign_id,))
            cursor.execute('DELETE FROM npcs WHERE campaign_id = ?', (campaign_id,))
            cursor.execute('DELETE FROM locations WHERE campaign_id = ?', (campaign_id,))
            cursor.execute('DELETE FROM plot_threads WHERE campaign_id = ?', (campaign_id,))
            cursor.execute('DELETE FROM content_library WHERE campaign_id = ?', (campaign_id,))
            cursor.execute('DELETE FROM campaigns WHERE id = ?', (campaign_id,))
            return cursor.rowcount > 0
    
    # ==================== Session Operations ====================
    
    def create_session(self, campaign_id: int, session_number: int, 
                       title: str = "", notes: str = "") -> int:
        """Create a new session."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO sessions (campaign_id, session_number, title, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (campaign_id, session_number, title, notes,
                  datetime.now(timezone.utc).isoformat()))
            
            # Update campaign's last_played
            cursor.execute('''
                UPDATE campaigns SET last_played = ? WHERE id = ?
            ''', (datetime.now(timezone.utc).isoformat(), campaign_id))
            
            return cursor.lastrowid
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """Get session by ID."""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
        return None
    
    def get_campaign_sessions(self, campaign_id: int) -> List[Dict]:
        """Get all sessions for a campaign."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM sessions 
                WHERE campaign_id = ? 
                ORDER BY session_number
            ''', (campaign_id,))
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def update_session(self, session_id: int, **kwargs) -> bool:
        """Update session fields."""
        allowed_fields = ['title', 'date_played', 'summary', 'notes']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [session_id]
        
        with self.get_cursor() as cursor:
            cursor.execute(f'UPDATE sessions SET {set_clause} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    # ==================== Character Operations ====================
    
    def create_character(self, campaign_id: int, name: str, 
                         player_name: str = "", char_class: str = "",
                         race: str = "", level: int = 1,
                         hp_max: int = 0, hp_current: int = 0,
                         ac: int = 10, data: Dict = None) -> int:
        """Create a new character."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO characters 
                (campaign_id, name, player_name, char_class, race, level, 
                 hp_max, hp_current, ac, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (campaign_id, name, player_name, char_class, race, level,
                  hp_max, hp_current or hp_max, ac, json.dumps(data or {}),
                  datetime.now(timezone.utc).isoformat(),
                  datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid
    
    def get_character(self, character_id: int) -> Optional[Dict]:
        """Get character by ID."""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM characters WHERE id = ?', (character_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
        return None
    
    def get_campaign_characters(self, campaign_id: int) -> List[Dict]:
        """Get all characters for a campaign."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM characters 
                WHERE campaign_id = ? 
                ORDER BY name
            ''', (campaign_id,))
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def update_character(self, character_id: int, **kwargs) -> bool:
        """Update character fields."""
        allowed_fields = ['name', 'player_name', 'char_class', 'race', 
                          'level', 'hp_max', 'hp_current', 'ac', 'data']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        if 'data' in updates and isinstance(updates['data'], dict):
            updates['data'] = json.dumps(updates['data'])
        
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [character_id]
        
        with self.get_cursor() as cursor:
            cursor.execute(f'UPDATE characters SET {set_clause} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    def delete_character(self, character_id: int) -> bool:
        """Delete a character."""
        with self.get_cursor() as cursor:
            cursor.execute('DELETE FROM characters WHERE id = ?', (character_id,))
            return cursor.rowcount > 0
    
    # ==================== NPC Operations ====================
    
    def create_npc(self, campaign_id: int, name: str, race: str = "",
                   char_class: str = "", disposition: str = "neutral",
                   location: str = "", description: str = "",
                   data: Dict = None) -> int:
        """Create a new NPC."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO npcs 
                (campaign_id, name, race, char_class, disposition, 
                 location, description, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (campaign_id, name, race, char_class, disposition,
                  location, description, json.dumps(data or {}),
                  datetime.now(timezone.utc).isoformat(),
                  datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid
    
    def get_npc(self, npc_id: int) -> Optional[Dict]:
        """Get NPC by ID."""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM npcs WHERE id = ?', (npc_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
        return None
    
    def get_campaign_npcs(self, campaign_id: int, 
                          disposition: str = None) -> List[Dict]:
        """Get NPCs for a campaign."""
        with self.get_cursor() as cursor:
            query = 'SELECT * FROM npcs WHERE campaign_id = ?'
            params = [campaign_id]
            
            if disposition:
                query += ' AND disposition = ?'
                params.append(disposition)
            
            query += ' ORDER BY name'
            cursor.execute(query, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def update_npc_disposition(self, npc_id: int, disposition: str) -> bool:
        """Update NPC disposition."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE npcs SET disposition = ?, updated_at = ? WHERE id = ?
            ''', (disposition, datetime.now(timezone.utc).isoformat(), npc_id))
            return cursor.rowcount > 0
    
    # ==================== Location Operations ====================
    
    def create_location(self, campaign_id: int, name: str,
                        location_type: str = "", description: str = "",
                        parent_location: str = "", data: Dict = None) -> int:
        """Create a new location."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO locations 
                (campaign_id, name, location_type, description, 
                 parent_location, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (campaign_id, name, location_type, description,
                  parent_location, json.dumps(data or {}),
                  datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid
    
    def get_campaign_locations(self, campaign_id: int) -> List[Dict]:
        """Get locations for a campaign."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM locations 
                WHERE campaign_id = ? 
                ORDER BY name
            ''', (campaign_id,))
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Plot Thread Operations ====================
    
    def create_plot_thread(self, campaign_id: int, title: str,
                           description: str = "", status: str = "active",
                           priority: str = "normal",
                           introduced_session: int = 1) -> int:
        """Create a new plot thread."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO plot_threads 
                (campaign_id, title, description, status, priority, 
                 introduced_session, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (campaign_id, title, description, status, priority,
                  introduced_session, datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid
    
    def get_campaign_plot_threads(self, campaign_id: int,
                                   status: str = None) -> List[Dict]:
        """Get plot threads for a campaign."""
        with self.get_cursor() as cursor:
            query = 'SELECT * FROM plot_threads WHERE campaign_id = ?'
            params = [campaign_id]
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY created_at DESC'
            cursor.execute(query, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def resolve_plot_thread(self, plot_thread_id: int, 
                            resolved_session: int) -> bool:
        """Mark a plot thread as resolved."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE plot_threads 
                SET status = 'resolved', 
                    resolved_session = ?, 
                    resolved_at = ? 
                WHERE id = ?
            ''', (resolved_session, datetime.now(timezone.utc).isoformat(),
                  plot_thread_id))
            return cursor.rowcount > 0
    
    # ==================== Content Library Operations ====================
    
    def save_to_library(self, campaign_id: int, content_type: str,
                        title: str, data: Dict, theme: str = "",
                        difficulty: str = "", tags: List[str] = None) -> int:
        """Save generated content to library."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO content_library 
                (campaign_id, content_type, title, theme, difficulty, 
                 data, created_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (campaign_id, content_type, title, theme, difficulty,
                  json.dumps(data), datetime.now(timezone.utc).isoformat(),
                  json.dumps(tags or [])))
            return cursor.lastrowid
    
    def search_library(self, campaign_id: int = None,
                       content_type: str = None,
                       query: str = None) -> List[Dict]:
        """Search content library."""
        with self.get_cursor() as cursor:
            query_parts = ['1=1']
            params = []
            
            if campaign_id:
                query_parts.append('campaign_id = ?')
                params.append(campaign_id)
            
            if content_type:
                query_parts.append('content_type = ?')
                params.append(content_type)
            
            if query:
                query_parts.append('(title LIKE ? OR theme LIKE ?)')
                params.extend([f'%{query}%', f'%{query}%'])
            
            sql = f'SELECT * FROM content_library WHERE {" AND ".join(query_parts)}'
            sql += ' ORDER BY created_at DESC'
            
            cursor.execute(sql, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Session Events Operations ====================
    
    def log_session_event(self, session_id: int, event_type: str,
                          description: str, round_num: int = None,
                          participants: str = "", result: str = "") -> int:
        """Log an event during a session."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO session_events 
                (session_id, event_type, description, round_num, 
                 participants, result, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, event_type, description, round_num,
                  participants, result, datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid
    
    def get_session_events(self, session_id: int) -> List[Dict]:
        """Get events for a session."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM session_events 
                WHERE session_id = ? 
                ORDER BY created_at
            ''', (session_id,))
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Statistics ====================
    
    def get_campaign_stats(self, campaign_id: int) -> Dict[str, Any]:
        """Get statistics for a campaign."""
        with self.get_cursor() as cursor:
            stats = {}
            
            # Session count
            cursor.execute('SELECT COUNT(*) FROM sessions WHERE campaign_id = ?', 
                          (campaign_id,))
            stats['sessions'] = cursor.fetchone()[0]
            
            # Character count
            cursor.execute('SELECT COUNT(*) FROM characters WHERE campaign_id = ?',
                          (campaign_id,))
            stats['characters'] = cursor.fetchone()[0]
            
            # NPC count
            cursor.execute('SELECT COUNT(*) FROM npcs WHERE campaign_id = ?',
                          (campaign_id,))
            stats['npcs'] = cursor.fetchone()[0]
            
            # Location count
            cursor.execute('SELECT COUNT(*) FROM locations WHERE campaign_id = ?',
                          (campaign_id,))
            stats['locations'] = cursor.fetchone()[0]
            
            # Active plot threads
            cursor.execute('''
                SELECT COUNT(*) FROM plot_threads 
                WHERE campaign_id = ? AND status = 'active'
            ''', (campaign_id,))
            stats['active_threads'] = cursor.fetchone()[0]
            
            # Content library count
            cursor.execute('SELECT COUNT(*) FROM content_library WHERE campaign_id = ?',
                          (campaign_id,))
            stats['saved_content'] = cursor.fetchone()[0]
            
            return stats
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global database statistics."""
        with self.get_cursor() as cursor:
            stats = {}
            tables = ['campaigns', 'sessions', 'characters', 'npcs', 
                      'locations', 'plot_threads', 'content_library']
            
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                stats[table] = cursor.fetchone()[0]
            
            return stats
    
    # ==================== Utility Methods ====================
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to dictionary."""
        result = dict(row)
        
        # Parse JSON fields
        json_fields = ['data', 'settings', 'tags']
        for field in json_fields:
            if field in result and result[field]:
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    pass
        
        return result
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        import shutil
        try:
            shutil.copy2(str(self.db_path), backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except IOError as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def export_campaign(self, campaign_id: int, filepath: str) -> bool:
        """Export a campaign to JSON file."""
        campaign = self.get_campaign(campaign_id=campaign_id)
        if not campaign:
            return False
        
        export_data = {
            'campaign': campaign,
            'sessions': self.get_campaign_sessions(campaign_id),
            'characters': self.get_campaign_characters(campaign_id),
            'npcs': self.get_campaign_npcs(campaign_id),
            'locations': self.get_campaign_locations(campaign_id),
            'plot_threads': self.get_campaign_plot_threads(campaign_id),
            'content': self.search_library(campaign_id=campaign_id)
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Campaign exported to {filepath}")
            return True
        except IOError as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def close(self):
        """Close database connection (cleanup)."""
        pass  # Context manager handles this
