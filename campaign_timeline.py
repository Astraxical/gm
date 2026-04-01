#!/usr/bin/env python3
"""
DnD Campaign Timeline Builder v1.0

Track historical events, prophecies, and campaign chronology.
Build rich campaign histories and future plot points.

Features:
- Timeline creation with eras
- Event tracking with dates
- Prophecy system
- Past/present/future events
- Export timeline visualization
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


class EventCategory(str, Enum):
    HISTORICAL = "historical"
    CURRENT = "current"
    FUTURE = "future"
    PROPHECY = "prophecy"
    PERSONAL = "personal"


@dataclass
class TimelineEvent:
    """An event in the timeline."""
    id: str
    title: str
    description: str
    category: str
    year: int  # Relative to campaign year 0
    era: str = ""
    importance: int = 3  # 1-5
    tags: List[str] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)
    is_fulfilled: bool = False  # For prophecies
    revealed_to_players: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "year": self.year,
            "era": self.era,
            "importance": self.importance,
            "tags": self.tags,
            "related_events": self.related_events,
            "is_fulfilled": self.is_fulfilled,
            "revealed_to_players": self.revealed_to_players
        }


class CampaignTimeline:
    """Campaign timeline manager."""

    def __init__(self, campaign_name: str = "My Campaign", year_zero: str = "Campaign Start"):
        self.campaign_name = campaign_name
        self.year_zero_description = year_zero
        self.events: Dict[str, TimelineEvent] = {}
        self.eras: Dict[str, Dict[str, Any]] = {}
        self.current_year: int = 0
        self.created = datetime.now(timezone.utc).isoformat()

    def add_era(self, name: str, start_year: int, end_year: int, description: str = "") -> None:
        """Add an era to the timeline."""
        self.eras[name] = {
            "name": name,
            "start": start_year,
            "end": end_year,
            "description": description
        }
        logger.info(f"Added era: {name}")

    def add_event(
        self,
        title: str,
        description: str,
        year: int,
        category: str = "historical",
        era: str = "",
        importance: int = 3,
        tags: Optional[List[str]] = None
    ) -> TimelineEvent:
        """Add an event to the timeline."""
        event_id = f"year_{year}_{title.lower().replace(' ', '_')[:20]}"
        
        event = TimelineEvent(
            id=event_id,
            title=title,
            description=description,
            category=category,
            year=year,
            era=era,
            importance=importance,
            tags=tags or []
        )
        
        self.events[event_id] = event
        logger.info(f"Added event: {title} (Year {year})")
        return event

    def add_prophecy(
        self,
        text: str,
        fulfillment_year: int,
        source: str = "Ancient Oracle",
        clues: Optional[List[str]] = None
    ) -> TimelineEvent:
        """Add a prophecy to the timeline."""
        event = TimelineEvent(
            id=f"prophecy_{fulfillment_year}",
            title=f"Prophecy: {text[:30]}...",
            description=text,
            category="prophecy",
            year=fulfillment_year,
            importance=5,
            tags=["prophecy", source]
        )
        if clues:
            event.tags.extend([f"clue:{c}" for c in clues])
        
        self.events[event.id] = event
        return event

    def get_events_by_year(self, year: int) -> List[TimelineEvent]:
        """Get all events for a specific year."""
        return [e for e in self.events.values() if e.year == year]

    def get_events_in_range(self, start: int, end: int) -> List[TimelineEvent]:
        """Get events within a year range."""
        return [e for e in self.events.values() if start <= e.year <= end]

    def get_upcoming_events(self, from_year: Optional[int] = None) -> List[TimelineEvent]:
        """Get future events from a given year."""
        year = from_year if from_year else self.current_year
        future = [e for e in self.events.values() if e.year > year]
        future.sort(key=lambda e: e.year)
        return future

    def get_prophecies(self, fulfilled_only: bool = False) -> List[TimelineEvent]:
        """Get prophecy events."""
        prophecies = [e for e in self.events.values() if e.category == "prophecy"]
        if fulfilled_only:
            prophecies = [e for e in prophecies if e.is_fulfilled]
        return prophecies

    def fulfill_prophecy(self, event_id: str) -> bool:
        """Mark a prophecy as fulfilled."""
        if event_id in self.events:
            self.events[event_id].is_fulfilled = True
            return True
        return False

    def set_current_year(self, year: int) -> None:
        """Set the current campaign year."""
        self.current_year = year

    def get_timeline_summary(self) -> Dict[str, Any]:
        """Get timeline summary."""
        events_by_category = {}
        for event in self.events.values():
            cat = event.category
            events_by_category[cat] = events_by_category.get(cat, 0) + 1
        
        min_year = min(e.year for e in self.events.values()) if self.events else 0
        max_year = max(e.year for e in self.events.values()) if self.events else 0
        
        return {
            "campaign": self.campaign_name,
            "current_year": self.current_year,
            "total_events": len(self.events),
            "by_category": events_by_category,
            "year_range": f"{min_year} to {max_year}",
            "eras": list(self.eras.keys())
        }

    def export_to_json(self, filepath: str) -> None:
        """Export timeline to JSON."""
        data = {
            "campaign_name": self.campaign_name,
            "year_zero": self.year_zero_description,
            "current_year": self.current_year,
            "eras": self.eras,
            "events": {k: v.to_dict() for k, v in self.events.items()}
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported timeline to {filepath}")

    def display_timeline(self, show_hidden: bool = False) -> str:
        """Display timeline in readable format."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"📅 {self.campaign_name} - Timeline")
        lines.append(f"Current Year: {self.current_year}")
        lines.append("=" * 70)
        
        # Sort events by year
        sorted_events = sorted(self.events.values(), key=lambda e: e.year)
        
        current_era = None
        for event in sorted_events:
            # Show era header if applicable
            if event.era and event.era != current_era:
                era_info = self.eras.get(event.era, {})
                lines.append(f"\n📜 ERA: {event.era.upper()}")
                if era_info.get("description"):
                    lines.append(f"   {era_info['description']}")
                current_era = event.era
            
            # Show event
            year_display = f"Year {event.year}"
            category_icon = {
                "historical": "📚",
                "current": "📍",
                "future": "🔮",
                "prophecy": "✨",
                "personal": "👤"
            }.get(event.category, "•")
            
            fulfilled = "✓" if event.is_fulfilled else ""
            lines.append(f"\n{category_icon} {year_display}: {event.title} {fulfilled}")
            lines.append(f"   {event.description}")
            if event.tags:
                lines.append(f"   Tags: {', '.join(event.tags)}")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    """CLI for campaign timeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD Campaign Timeline Builder v1.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Add event
    add_parser = subparsers.add_parser("add", help="Add event")
    add_parser.add_argument("title", help="Event title")
    add_parser.add_argument("-d", "--description", required=True, help="Event description")
    add_parser.add_argument("-y", "--year", type=int, required=True, help="Year")
    add_parser.add_argument("-c", "--category", 
                           choices=["historical", "current", "future", "prophecy", "personal"],
                           default="historical")
    add_parser.add_argument("--era", help="Era name")
    
    # Add prophecy
    prophecy_parser = subparsers.add_parser("prophecy", help="Add prophecy")
    prophecy_parser.add_argument("text", help="Prophecy text")
    prophecy_parser.add_argument("-y", "--year", type=int, required=True, help="Fulfillment year")
    prophecy_parser.add_argument("--source", default="Ancient Oracle", help="Prophecy source")
    
    # List
    subparsers.add_parser("list", help="List all events")
    
    # Summary
    subparsers.add_parser("summary", help="Timeline summary")
    
    # Export
    export_parser = subparsers.add_parser("export", help="Export timeline")
    export_parser.add_argument("output", help="Output file")
    
    args = parser.parse_args()
    
    timeline = CampaignTimeline()
    
    if args.command == "add":
        event = timeline.add_event(
            title=args.title,
            description=args.description,
            year=args.year,
            category=args.category,
            era=args.era
        )
        print(f"Added event: {event.id}")
    
    elif args.command == "prophecy":
        event = timeline.add_prophecy(args.text, args.year, args.source)
        print(f"Added prophecy: {event.id}")
    
    elif args.command == "list":
        print(timeline.display_timeline())
    
    elif args.command == "summary":
        summary = timeline.get_timeline_summary()
        print(f"\n=== {summary['campaign']} ===")
        print(f"Current Year: {summary['current_year']}")
        print(f"Total Events: {summary['total_events']}")
        print(f"Year Range: {summary['year_range']}")
        print(f"\nBy Category:")
        for cat, count in summary['by_category'].items():
            print(f"  {cat}: {count}")
    
    elif args.command == "export":
        timeline.export_to_json(args.output)
        print(f"Exported to {args.output}")
    
    else:
        # Demo
        print("=== Demo Timeline ===\n")
        
        # Add eras
        timeline.add_era("Age of Myth", -1000, -500, "When gods walked the earth")
        timeline.add_era("Age of Kingdoms", -500, 0, "Rise of great nations")
        timeline.add_era("Age of Adventure", 0, 100, "Current era")
        
        # Add historical events
        timeline.add_event("The First Dragon War", "Dragons nearly destroyed civilization", -800, "historical", "Age of Myth", 5)
        timeline.add_event("Founding of the Kingdom", "King Arthur united the tribes", -450, "historical", "Age of Kingdoms", 4)
        timeline.add_event("The Great Plague", "Half the population perished", -100, "historical", "Age of Kingdoms", 3)
        
        # Add current events
        timeline.add_event("Party Arrives in Town", "The adventure begins", 0, "current", "Age of Adventure", 3)
        
        # Add prophecies
        timeline.add_prophecy(
            "When the twin moons align, the ancient evil shall rise",
            5,
            "Oracle of Delphi",
            ["twin moons", "ancient evil"]
        )
        
        # Add future events
        timeline.add_event("The Prophecy Fulfills", "The ancient evil returns", 5, "future", "Age of Adventure", 5)
        
        timeline.set_current_year(0)
        print(timeline.display_timeline())


if __name__ == "__main__":
    main()
