#!/usr/bin/env python3
"""
Campaign Memory Module

JSON-based short-term memory for campaign state.
Tracks current session, recent events, and active plot threads.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class CampaignMemory:
    """JSON-based campaign memory system."""
    
    def __init__(self, memory_dir: str = "ai_data"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_file = self.memory_dir / "campaign_memory.json"
        
        # Memory structure
        self.memory = {
            "campaign_name": "",
            "created": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "current_session": {
                "number": 1,
                "title": "",
                "in_progress": False
            },
            "recent_events": [],  # Last 10 events
            "active_threads": [],  # Ongoing plot threads
            "character_states": {},  # PC states
            "npc_relationships": {},  # NPC relationship states
            "location_states": {},  # Location states
            "session_history": [],  # Past session summaries
            "dm_notes": ""
        }
        
        # Load existing memory
        self._load_memory()
    
    def _load_memory(self) -> None:
        """Load memory from file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    self.memory = json.load(f)
                logger.info(f"Loaded campaign memory from {self.memory_file}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load memory: {e}")
                self._save_memory()  # Create fresh file
    
    def _save_memory(self) -> None:
        """Save memory to file."""
        self.memory["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
        logger.debug(f"Saved campaign memory")
    
    def set_campaign_name(self, name: str) -> None:
        """Set the campaign name."""
        self.memory["campaign_name"] = name
        self._save_memory()
    
    def start_session(self, session_number: int, title: str) -> None:
        """Start a new session."""
        self.memory["current_session"] = {
            "number": session_number,
            "title": title,
            "in_progress": True,
            "started": datetime.now(timezone.utc).isoformat()
        }
        self._save_memory()
        logger.info(f"Started session {session_number}: {title}")
    
    def end_session(self, summary: str, xp_awarded: Dict[str, int] = None) -> None:
        """End the current session."""
        session = self.memory["current_session"]
        
        session_record = {
            "number": session["number"],
            "title": session["title"],
            "ended": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "xp_awarded": xp_awarded or {}
        }
        
        self.memory["session_history"].append(session_record)
        self.memory["current_session"]["in_progress"] = False
        self._save_memory()
        logger.info(f"Ended session {session['number']}")
    
    def add_event(self, event: str, event_type: str = "general") -> None:
        """
        Add a recent event to memory.
        
        Args:
            event: Event description
            event_type: Type of event (combat, social, discovery, etc.)
        """
        event_record = {
            "description": event,
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session": self.memory["current_session"]["number"]
        }
        
        self.memory["recent_events"].append(event_record)
        
        # Keep only last 20 events
        if len(self.memory["recent_events"]) > 20:
            self.memory["recent_events"] = self.memory["recent_events"][-20:]
        
        self._save_memory()
    
    def add_plot_thread(self, thread: str, status: str = "active") -> None:
        """
        Add or update a plot thread.
        
        Args:
            thread: Thread description
            status: active, resolved, abandoned
        """
        thread_record = {
            "description": thread,
            "status": status,
            "added": datetime.now(timezone.utc).isoformat(),
            "session_introduced": self.memory["current_session"]["number"]
        }
        
        self.memory["active_threads"].append(thread_record)
        self._save_memory()
    
    def resolve_plot_thread(self, thread_description: str) -> bool:
        """Mark a plot thread as resolved."""
        for thread in self.memory["active_threads"]:
            if thread_description.lower() in thread["description"].lower():
                thread["status"] = "resolved"
                thread["resolved"] = datetime.now(timezone.utc).isoformat()
                self._save_memory()
                return True
        return False
    
    def update_character(self, name: str, state: Dict[str, Any]) -> None:
        """
        Update a character's state.
        
        Args:
            name: Character name
            state: State dict (level, hp, conditions, etc.)
        """
        self.memory["character_states"][name] = {
            **self.memory["character_states"].get(name, {}),
            **state,
            "updated": datetime.now(timezone.utc).isoformat()
        }
        self._save_memory()
    
    def update_npc_relationship(self, npc_name: str, party_relation: str) -> None:
        """
        Update NPC relationship with party.
        
        Args:
            npc_name: NPC name
            party_relation: friendly, neutral, hostile, etc.
        """
        self.memory["npc_relationships"][npc_name] = {
            "relation": party_relation,
            "updated": datetime.now(timezone.utc).isoformat()
        }
        self._save_memory()
    
    def update_location(self, location_name: str, state: Dict[str, Any]) -> None:
        """
        Update a location's state.
        
        Args:
            location_name: Location name
            state: State dict (cleared, dangerous, etc.)
        """
        self.memory["location_states"][location_name] = {
            **state,
            "updated": datetime.now(timezone.utc).isoformat()
        }
        self._save_memory()
    
    def get_recent_events(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent events."""
        return self.memory["recent_events"][-count:]
    
    def get_active_threads(self) -> List[Dict[str, Any]]:
        """Get active plot threads."""
        return [t for t in self.memory["active_threads"] if t["status"] == "active"]
    
    def get_character(self, name: str) -> Optional[Dict[str, Any]]:
        """Get character state."""
        return self.memory["character_states"].get(name)
    
    def get_npc_relation(self, npc_name: str) -> str:
        """Get NPC relationship status."""
        rel = self.memory["npc_relationships"].get(npc_name, {})
        return rel.get("relation", "unknown")
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """Get session history."""
        return self.memory["session_history"]
    
    def set_dm_note(self, note: str) -> None:
        """Set DM notes."""
        self.memory["dm_notes"] = note
        self._save_memory()
    
    def get_dm_notes(self) -> str:
        """Get DM notes."""
        return self.memory.get("dm_notes", "")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get memory summary."""
        return {
            "campaign": self.memory["campaign_name"],
            "current_session": self.memory["current_session"]["number"],
            "recent_events_count": len(self.memory["recent_events"]),
            "active_threads_count": len([t for t in self.memory["active_threads"] if t["status"] == "active"]),
            "characters_tracked": len(self.memory["character_states"]),
            "npcs_tracked": len(self.memory["npc_relationships"]),
            "sessions_completed": len(self.memory["session_history"])
        }
    
    def clear_memory(self) -> None:
        """Clear all memory (start fresh campaign)."""
        self.memory = {
            "campaign_name": "",
            "created": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "current_session": {"number": 1, "title": "", "in_progress": False},
            "recent_events": [],
            "active_threads": [],
            "character_states": {},
            "npc_relationships": {},
            "location_states": {},
            "session_history": [],
            "dm_notes": ""
        }
        self._save_memory()
        logger.info("Cleared campaign memory")
    
    def export_memory(self, filepath: str) -> bool:
        """Export memory to a different file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.memory, f, indent=2)
            logger.info(f"Exported memory to {filepath}")
            return True
        except IOError as e:
            logger.error(f"Failed to export: {e}")
            return False
    
    def import_memory(self, filepath: str) -> bool:
        """Import memory from a file."""
        try:
            with open(filepath, 'r') as f:
                self.memory = json.load(f)
            self._save_memory()
            logger.info(f"Imported memory from {filepath}")
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to import: {e}")
            return False
