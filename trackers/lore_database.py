#!/usr/bin/env python3
"""
DnD Lore Database v1.0

Store, organize, and retrieve campaign knowledge.
Never forget important NPCs, locations, or plot points again.

Features:
- Categorized entries (NPCs, locations, factions, events, items)
- Full-text search
- Relationship linking
- Timeline integration
- Export/import campaigns
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EntryType(str, Enum):
    NPC = "npc"
    LOCATION = "location"
    FACTION = "faction"
    EVENT = "event"
    ITEM = "item"
    QUEST = "quest"
    LORE = "lore"
    MONSTER = "monster"
    DEITY = "deity"
    CUSTOM = "custom"


@dataclass
class LoreEntry:
    """A single lore entry."""
    id: str
    title: str
    entry_type: str
    content: str
    tags: List[str] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_secret: bool = False  # DM eyes only
    session_revealed: int = 0
    importance: int = 3  # 1-5 scale
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "entry_type": self.entry_type,
            "content": self.content,
            "tags": self.tags,
            "related_entries": self.related_entries,
            "created": self.created,
            "updated": self.updated,
            "is_secret": self.is_secret,
            "session_revealed": self.session_revealed,
            "importance": self.importance
        }


class LoreDatabase:
    """Campaign lore database."""

    def __init__(self, campaign_name: str = "My Campaign"):
        self.campaign_name = campaign_name
        self.entries: Dict[str, LoreEntry] = {}
        self.created = datetime.now(timezone.utc).isoformat()
        self.last_updated = self.created

    def add_entry(
        self,
        title: str,
        entry_type: str,
        content: str,
        tags: Optional[List[str]] = None,
        is_secret: bool = False,
        importance: int = 3
    ) -> LoreEntry:
        """Add a new lore entry."""
        entry_id = title.lower().replace(" ", "_")
        
        # Handle duplicates
        counter = 1
        original_id = entry_id
        while entry_id in self.entries:
            entry_id = f"{original_id}_{counter}"
            counter += 1
        
        entry = LoreEntry(
            id=entry_id,
            title=title,
            entry_type=entry_type,
            content=content,
            tags=tags or [],
            is_secret=is_secret,
            importance=importance
        )
        
        self.entries[entry_id] = entry
        self._update_timestamp()
        logger.info(f"Added entry: {title} ({entry_type})")
        return entry

    def get_entry(self, entry_id: str) -> Optional[LoreEntry]:
        """Get entry by ID."""
        return self.entries.get(entry_id)

    def search(self, query: str, entry_type: Optional[str] = None) -> List[LoreEntry]:
        """Search entries by text."""
        query_lower = query.lower()
        results = []
        
        for entry in self.entries.values():
            if entry_type and entry.entry_type != entry_type:
                continue
            
            # Search in title, content, and tags
            searchable = f"{entry.title} {entry.content} {' '.join(entry.tags)}".lower()
            if query_lower in searchable:
                results.append(entry)
        
        # Sort by relevance (importance, then title match)
        results.sort(key=lambda e: (e.importance, query_lower in e.title.lower()), reverse=True)
        return results

    def get_by_type(self, entry_type: str) -> List[LoreEntry]:
        """Get all entries of a specific type."""
        return [e for e in self.entries.values() if e.entry_type == entry_type]

    def get_by_tag(self, tag: str) -> List[LoreEntry]:
        """Get all entries with a specific tag."""
        return [e for e in self.entries.values() if tag in e.tags]

    def link_entries(self, entry_id1: str, entry_id2: str) -> bool:
        """Create a relationship between two entries."""
        if entry_id1 not in self.entries or entry_id2 not in self.entries:
            return False
        
        if entry_id2 not in self.entries[entry_id1].related_entries:
            self.entries[entry_id1].related_entries.append(entry_id2)
        if entry_id1 not in self.entries[entry_id2].related_entries:
            self.entries[entry_id2].related_entries.append(entry_id1)
        
        self._update_timestamp()
        return True

    def update_entry(self, entry_id: str, **kwargs) -> bool:
        """Update an entry's fields."""
        entry = self.entries.get(entry_id)
        if not entry:
            return False
        
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        entry.updated = datetime.now(timezone.utc).isoformat()
        self._update_timestamp()
        return True

    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry."""
        if entry_id in self.entries:
            # Remove links from other entries
            for entry in self.entries.values():
                if entry_id in entry.related_entries:
                    entry.related_entries.remove(entry_id)
            
            del self.entries[entry_id]
            self._update_timestamp()
            return True
        return False

    def get_relationships(self, entry_id: str) -> List[LoreEntry]:
        """Get all entries related to this one."""
        entry = self.entries.get(entry_id)
        if not entry:
            return []
        
        related = []
        for rel_id in entry.related_entries:
            if rel_id in self.entries:
                related.append(self.entries[rel_id])
        return related

    def get_summary(self) -> Dict[str, Any]:
        """Get database summary statistics."""
        type_counts = {}
        for entry in self.entries.values():
            type_counts[entry.entry_type] = type_counts.get(entry.entry_type, 0) + 1
        
        return {
            "campaign": self.campaign_name,
            "total_entries": len(self.entries),
            "by_type": type_counts,
            "secret_entries": sum(1 for e in self.entries.values() if e.is_secret),
            "created": self.created,
            "last_updated": self.last_updated
        }

    def export_to_json(self, filepath: str) -> None:
        """Export database to JSON file."""
        data = {
            "campaign_name": self.campaign_name,
            "created": self.created,
            "last_updated": self.last_updated,
            "entries": {k: v.to_dict() for k, v in self.entries.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported database to {filepath}")

    def import_from_json(self, filepath: str) -> bool:
        """Import database from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.campaign_name = data.get("campaign_name", "Imported Campaign")
            self.created = data.get("created", datetime.now(timezone.utc).isoformat())
            self.last_updated = data.get("last_updated", self.created)
            
            for entry_id, entry_data in data.get("entries", {}).items():
                entry = LoreEntry(
                    id=entry_data.get("id", entry_id),
                    title=entry_data.get("title", ""),
                    entry_type=entry_data.get("entry_type", "custom"),
                    content=entry_data.get("content", ""),
                    tags=entry_data.get("tags", []),
                    related_entries=entry_data.get("related_entries", []),
                    created=entry_data.get("created", ""),
                    updated=entry_data.get("updated", ""),
                    is_secret=entry_data.get("is_secret", False),
                    session_revealed=entry_data.get("session_revealed", 0),
                    importance=entry_data.get("importance", 3)
                )
                self.entries[entry_id] = entry
            
            logger.info(f"Imported database from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to import: {e}")
            return False

    def _update_timestamp(self):
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def display_entry(self, entry: LoreEntry, show_secrets: bool = False) -> str:
        """Display a single entry."""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"📖 {entry.title}")
        lines.append(f"{'='*60}")
        lines.append(f"Type: {entry.entry_type.upper()}")
        lines.append(f"Importance: {'⭐' * entry.importance}")
        if entry.tags:
            lines.append(f"Tags: {', '.join(entry.tags)}")
        if entry.related_entries:
            lines.append(f"Related: {', '.join(entry.related_entries)}")
        if entry.is_secret and not show_secrets:
            lines.append("\n🔒 [DM EYES ONLY - Content Hidden]")
        else:
            lines.append(f"\n{entry.content}")
        return "\n".join(lines)


def main():
    """CLI for lore database."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD Lore Database v1.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Add entry
    add_parser = subparsers.add_parser("add", help="Add new entry")
    add_parser.add_argument("title", help="Entry title")
    add_parser.add_argument("-t", "--type", required=True, 
                           choices=["npc", "location", "faction", "event", "item", "quest", "lore"])
    add_parser.add_argument("-c", "--content", required=True, help="Entry content")
    add_parser.add_argument("--tags", nargs="+", help="Tags")
    add_parser.add_argument("--secret", action="store_true", help="DM only")
    add_parser.add_argument("--importance", type=int, default=3, choices=[1,2,3,4,5])
    
    # Search
    search_parser = subparsers.add_parser("search", help="Search entries")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", help="Filter by type")
    
    # List
    list_parser = subparsers.add_parser("list", help="List entries")
    list_parser.add_argument("--type", help="Filter by type")
    
    # Show
    show_parser = subparsers.add_parser("show", help="Show entry")
    show_parser.add_argument("entry_id", help="Entry ID")
    show_parser.add_argument("--reveal", action="store_true", help="Show secrets")
    
    # Export
    export_parser = subparsers.add_parser("export", help="Export database")
    export_parser.add_argument("output", help="Output file")
    
    # Import
    import_parser = subparsers.add_parser("import", help="Import database")
    import_parser.add_argument("input", help="Input file")
    
    # Summary
    subparsers.add_parser("summary", help="Database summary")
    
    args = parser.parse_args()
    
    db = LoreDatabase()
    
    if args.command == "add":
        entry = db.add_entry(
            title=args.title,
            entry_type=args.type,
            content=args.content,
            tags=args.tags,
            is_secret=args.secret,
            importance=args.importance
        )
        print(f"Added entry: {entry.id}")
    
    elif args.command == "search":
        results = db.search(args.query, args.type)
        if results:
            print(f"\nFound {len(results)} entries:\n")
            for entry in results[:10]:
                print(f"  • {entry.id} ({entry.entry_type}) - {entry.title}")
        else:
            print("No entries found")
    
    elif args.command == "list":
        entries = db.get_by_type(args.type) if args.type else db.entries.values()
        print(f"\n{'='*50}")
        print(f"Entries ({len(list(entries))}):")
        print(f"{'='*50}")
        for entry in entries:
            secret = "🔒" if entry.is_secret else ""
            print(f"  {secret} {entry.id} ({entry.entry_type}) - {entry.title}")
    
    elif args.command == "show":
        entry = db.get_entry(args.entry_id)
        if entry:
            print(db.display_entry(entry, args.reveal))
        else:
            print(f"Entry not found: {args.entry_id}")
    
    elif args.command == "export":
        db.export_to_json(args.output)
        print(f"Exported to {args.output}")
    
    elif args.command == "import":
        if db.import_from_json(args.input):
            print(f"Imported from {args.input}")
    
    elif args.command == "summary":
        summary = db.get_summary()
        print(f"\n=== {summary['campaign']} ===")
        print(f"Total Entries: {summary['total_entries']}")
        print(f"Secret Entries: {summary['secret_entries']}")
        print(f"\nBy Type:")
        for type_name, count in summary['by_type'].items():
            print(f"  {type_name}: {count}")


if __name__ == "__main__":
    main()
