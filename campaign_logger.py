#!/usr/bin/env python3
"""
DnD Campaign Logger v1.0

Track campaign sessions, character progress, loot distribution, and story arcs.
Export campaign logs to multiple formats.

Features:
- Session notes with timestamps
- XP tracking and level-ups
- Loot distribution log
- NPC relationship tracking
- Story arc management
- Campaign timeline
- Export to JSON, Markdown, PDF-ready HTML
"""

import json
import logging
from typing import Dict, List, Optional, Any, TypedDict
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SessionType(str, Enum):
    """Types of campaign sessions."""
    MAIN = "main"
    ONE_SHOT = "one_shot"
    SIDE_QUEST = "side_quest"
    CHARACTER_BACKSTORY = "backstory"
    DM_PREP = "dm_prep"


class StoryArcStatus(str, Enum):
    """Story arc progression status."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    HIATUS = "hiatus"


@dataclass
class CharacterProgress:
    """Track a character's progress."""
    name: str
    player: str
    char_class: str
    level: int
    xp_current: int = 0
    xp_needed: int = 0
    hp_max: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionLog:
    """A single session log entry."""
    session_number: int
    title: str
    date_played: str
    duration_hours: float
    session_type: str
    summary: str
    xp_awarded: Dict[str, int] = field(default_factory=dict)
    loot_distributed: List[Dict[str, Any]] = field(default_factory=list)
    npcs_met: List[str] = field(default_factory=list)
    locations_visited: List[str] = field(default_factory=list)
    plot_developments: List[str] = field(default_factory=list)
    dm_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StoryArc:
    """A story arc in the campaign."""
    name: str
    description: str
    status: str = "planned"
    start_session: int = 0
    end_session: Optional[int] = None
    key_npcs: List[str] = field(default_factory=list)
    key_locations: List[str] = field(default_factory=list)
    resolution: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Campaign:
    """A complete campaign."""
    name: str
    dm_name: str
    start_date: str
    setting: str = ""
    tone: str = ""
    sessions: List[SessionLog] = field(default_factory=list)
    characters: List[CharacterProgress] = field(default_factory=list)
    story_arcs: List[StoryArc] = field(default_factory=list)
    campaign_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dm_name": self.dm_name,
            "start_date": self.start_date,
            "setting": self.setting,
            "tone": self.tone,
            "sessions": [s.to_dict() for s in self.sessions],
            "characters": [c.to_dict() for c in self.characters],
            "story_arcs": [a.to_dict() for a in self.story_arcs],
            "campaign_notes": self.campaign_notes
        }


class CampaignLogger:
    """Log and track DnD campaign progress."""

    # XP thresholds by level (DnD 5e)
    XP_THRESHOLDS = {
        1: 0,
        2: 300,
        3: 900,
        4: 2700,
        5: 6500,
        6: 14000,
        7: 23000,
        8: 34000,
        9: 48000,
        10: 64000,
        11: 85000,
        12: 100000,
        13: 120000,
        14: 140000,
        15: 165000,
        16: 195000,
        17: 225000,
        18: 265000,
        19: 305000,
        20: 355000
    }

    def __init__(self, campaign_name: str = "", dm_name: str = ""):
        """
        Initialize the campaign logger.
        
        Args:
            campaign_name: Name of the campaign
            dm_name: Dungeon Master's name
        """
        self.campaigns: Dict[str, Campaign] = {}
        self.current_campaign: Optional[str] = None
        
        if campaign_name:
            self.create_campaign(campaign_name, dm_name)

    def create_campaign(
        self,
        name: str,
        dm_name: str,
        setting: str = "",
        tone: str = ""
    ) -> Campaign:
        """
        Create a new campaign.
        
        Args:
            name: Campaign name
            dm_name: DM name
            setting: Campaign setting
            tone: Campaign tone (serious, comedic, horror, etc.)
            
        Returns:
            Created Campaign object
        """
        campaign = Campaign(
            name=name,
            dm_name=dm_name,
            start_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            setting=setting,
            tone=tone
        )
        self.campaigns[name] = campaign
        self.current_campaign = name
        logger.info(f"Created campaign: {name}")
        return campaign

    def load_campaign(self, filepath: str) -> Campaign:
        """
        Load a campaign from JSON file.
        
        Args:
            filepath: Path to campaign JSON file
            
        Returns:
            Loaded Campaign object
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        campaign = Campaign(
            name=data.get("name", "Unknown"),
            dm_name=data.get("dm_name", ""),
            start_date=data.get("start_date", ""),
            setting=data.get("setting", ""),
            tone=data.get("tone", ""),
            campaign_notes=data.get("campaign_notes", "")
        )
        
        # Load sessions
        for s in data.get("sessions", []):
            session = SessionLog(
                session_number=s.get("session_number", 0),
                title=s.get("title", ""),
                date_played=s.get("date_played", ""),
                duration_hours=s.get("duration_hours", 0),
                session_type=s.get("session_type", "main"),
                summary=s.get("summary", ""),
                xp_awarded=s.get("xp_awarded", {}),
                loot_distributed=s.get("loot_distributed", []),
                npcs_met=s.get("npcs_met", []),
                locations_visited=s.get("locations_visited", []),
                plot_developments=s.get("plot_developments", []),
                dm_notes=s.get("dm_notes", "")
            )
            campaign.sessions.append(session)
        
        # Load characters
        for c in data.get("characters", []):
            char = CharacterProgress(
                name=c.get("name", ""),
                player=c.get("player", ""),
                char_class=c.get("char_class", ""),
                level=c.get("level", 1),
                xp_current=c.get("xp_current", 0),
                xp_needed=c.get("xp_needed", 0),
                hp_max=c.get("hp_max", 0),
                notes=c.get("notes", "")
            )
            campaign.characters.append(char)
        
        # Load story arcs
        for a in data.get("story_arcs", []):
            arc = StoryArc(
                name=a.get("name", ""),
                description=a.get("description", ""),
                status=a.get("status", "planned"),
                start_session=a.get("start_session", 0),
                end_session=a.get("end_session"),
                key_npcs=a.get("key_npcs", []),
                key_locations=a.get("key_locations", []),
                resolution=a.get("resolution", "")
            )
            campaign.story_arcs.append(arc)
        
        self.campaigns[name] = campaign
        self.current_campaign = name
        logger.info(f"Loaded campaign: {name} from {filepath}")
        return campaign

    def add_character(
        self,
        name: str,
        player: str,
        char_class: str,
        level: int = 1,
        hp_max: int = 0
    ) -> CharacterProgress:
        """
        Add a character to the campaign.
        
        Args:
            name: Character name
            player: Player name
            char_class: Character class
            level: Starting level
            hp_max: Maximum hit points
            
        Returns:
            Created CharacterProgress object
        """
        if not self.current_campaign:
            raise ValueError("No active campaign")
        
        campaign = self.campaigns[self.current_campaign]
        
        # Calculate XP needed for next level
        xp_needed = self.XP_THRESHOLDS.get(level + 1, 0) - self.XP_THRESHOLDS.get(level, 0)
        
        char = CharacterProgress(
            name=name,
            player=player,
            char_class=char_class,
            level=level,
            xp_current=self.XP_THRESHOLDS.get(level, 0),
            xp_needed=xp_needed,
            hp_max=hp_max
        )
        
        campaign.characters.append(char)
        logger.info(f"Added character: {name} (Level {level} {char_class})")
        return char

    def log_session(
        self,
        title: str,
        summary: str,
        date_played: Optional[str] = None,
        duration_hours: float = 4.0,
        session_type: str = "main",
        xp_awarded: Optional[Dict[str, int]] = None,
        loot_distributed: Optional[List[Dict[str, Any]]] = None,
        npcs_met: Optional[List[str]] = None,
        locations_visited: Optional[List[str]] = None,
        plot_developments: Optional[List[str]] = None,
        dm_notes: str = ""
    ) -> SessionLog:
        """
        Log a campaign session.
        
        Args:
            title: Session title
            summary: Session summary
            date_played: Date of session (default: today)
            duration_hours: Session duration in hours
            session_type: Type of session
            xp_awarded: XP awarded to each character
            loot_distributed: List of loot distributed
            npcs_met: NPCs encountered
            locations_visited: Locations visited
            plot_developments: Major plot developments
            dm_notes: Private DM notes
            
        Returns:
            Created SessionLog object
        """
        if not self.current_campaign:
            raise ValueError("No active campaign")
        
        campaign = self.campaigns[self.current_campaign]
        
        session_number = len(campaign.sessions) + 1
        
        session = SessionLog(
            session_number=session_number,
            title=title,
            date_played=date_played or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            duration_hours=duration_hours,
            session_type=session_type,
            summary=summary,
            xp_awarded=xp_awarded or {},
            loot_distributed=loot_distributed or [],
            npcs_met=npcs_met or [],
            locations_visited=locations_visited or [],
            plot_developments=plot_developments or [],
            dm_notes=dm_notes
        )
        
        campaign.sessions.append(session)
        
        # Update character XP
        for char_name, xp in xp_awarded.items():
            self._add_xp(char_name, xp)
        
        logger.info(f"Logged session {session_number}: {title}")
        return session

    def _add_xp(self, character_name: str, xp: int) -> None:
        """Add XP to a character and check for level-ups."""
        if not self.current_campaign:
            return
        
        campaign = self.campaigns[self.current_campaign]
        
        for char in campaign.characters:
            if char.name.lower() == character_name.lower():
                old_level = char.level
                char.xp_current += xp
                
                # Check for level-ups
                for level, threshold in sorted(self.XP_THRESHOLDS.items()):
                    if char.xp_current >= threshold and level > char.level:
                        char.level = level
                        logger.info(f"🎉 {char.name} leveled up to {level}!")
                
                # Update XP needed
                char.xp_needed = self.XP_THRESHOLDS.get(char.level + 1, 0) - char.xp_current
                break

    def add_story_arc(
        self,
        name: str,
        description: str,
        key_npcs: Optional[List[str]] = None,
        key_locations: Optional[List[str]] = None
    ) -> StoryArc:
        """
        Add a story arc to the campaign.
        
        Args:
            name: Arc name
            description: Arc description
            key_npcs: Important NPCs in this arc
            key_locations: Important locations in this arc
            
        Returns:
            Created StoryArc object
        """
        if not self.current_campaign:
            raise ValueError("No active campaign")
        
        campaign = self.campaigns[self.current_campaign]
        
        arc = StoryArc(
            name=name,
            description=description,
            start_session=len(campaign.sessions) + 1,
            key_npcs=key_npcs or [],
            key_locations=key_locations or []
        )
        
        campaign.story_arcs.append(arc)
        logger.info(f"Added story arc: {name}")
        return arc

    def update_story_arc_status(self, arc_name: str, status: str) -> bool:
        """Update the status of a story arc."""
        if not self.current_campaign:
            return False
        
        campaign = self.campaigns[self.current_campaign]
        
        for arc in campaign.story_arcs:
            if arc.name.lower() == arc_name.lower():
                arc.status = status
                if status == "completed":
                    arc.end_session = len(campaign.sessions)
                logger.info(f"Updated story arc '{arc_name}' status to {status}")
                return True
        return False

    def get_campaign_summary(self) -> Dict[str, Any]:
        """Get a summary of the current campaign."""
        if not self.current_campaign:
            return {"error": "No active campaign"}
        
        campaign = self.campaigns[self.current_campaign]
        
        total_play_time = sum(s.duration_hours for s in campaign.sessions)
        
        return {
            "name": campaign.name,
            "dm": campaign.dm_name,
            "setting": campaign.setting,
            "tone": campaign.tone,
            "start_date": campaign.start_date,
            "sessions_played": len(campaign.sessions),
            "total_play_time_hours": total_play_time,
            "characters": len(campaign.characters),
            "story_arcs": len(campaign.story_arcs),
            "active_arcs": sum(1 for a in campaign.story_arcs if a.status == "active")
        }

    def export_to_json(self, filepath: str) -> None:
        """Export campaign to JSON file."""
        if not self.current_campaign:
            raise ValueError("No active campaign")
        
        campaign = self.campaigns[self.current_campaign]
        with open(filepath, 'w') as f:
            json.dump(campaign.to_dict(), f, indent=2)
        logger.info(f"Campaign exported to {filepath}")

    def export_to_markdown(self, filepath: str) -> None:
        """Export campaign to Markdown file."""
        if not self.current_campaign:
            raise ValueError("No active campaign")
        
        campaign = self.campaigns[self.current_campaign]
        
        md = f"# {campaign.name}\n\n"
        md += f"**DM:** {campaign.dm_name}  \n"
        md += f"**Setting:** {campaign.setting}  \n"
        md += f"**Tone:** {campaign.tone}  \n"
        md += f"**Started:** {campaign.start_date}  \n\n"
        
        # Campaign summary
        summary = self.get_campaign_summary()
        md += "## Campaign Summary\n\n"
        md += f"- Sessions Played: {summary['sessions_played']}\n"
        md += f"- Total Play Time: {summary['total_play_time_hours']} hours\n"
        md += f"- Characters: {summary['characters']}\n"
        md += f"- Story Arcs: {summary['story_arcs']} ({summary['active_arcs']} active)\n\n"
        
        # Characters
        md += "## Characters\n\n"
        for char in campaign.characters:
            md += f"### {char.name}\n"
            md += f"- **Player:** {char.player}\n"
            md += f"- **Class:** {char.char_class}\n"
            md += f"- **Level:** {char.level}\n"
            md += f"- **XP:** {char.xp_current:,} / {char.xp_current + char.xp_needed:,}\n\n"
        
        # Story Arcs
        md += "## Story Arcs\n\n"
        for arc in campaign.story_arcs:
            status_icon = {"planned": "📋", "active": "▶️", "completed": "✅", "hiatus": "⏸️"}.get(arc.status, "")
            md += f"### {status_icon} {arc.name}\n"
            md += f"{arc.description}\n\n"
            if arc.key_npcs:
                md += f"**Key NPCs:** {', '.join(arc.key_npcs)}\n"
            if arc.key_locations:
                md += f"**Key Locations:** {', '.join(arc.key_locations)}\n"
            if arc.resolution:
                md += f"**Resolution:** {arc.resolution}\n"
            md += "\n"
        
        # Sessions
        md += "## Session Logs\n\n"
        for session in campaign.sessions:
            md += f"### Session {session.session_number}: {session.title}\n"
            md += f"*{session.date_played} ({session.duration_hours} hours)*\n\n"
            md += f"{session.summary}\n\n"
            
            if session.xp_awarded:
                md += "**XP Awarded:**\n"
                for name, xp in session.xp_awarded.items():
                    md += f"- {name}: {xp} XP\n"
                md += "\n"
            
            if session.loot_distributed:
                md += "**Loot Distributed:**\n"
                for item in session.loot_distributed:
                    if isinstance(item, dict):
                        md += f"- {item.get('item', 'Unknown')} → {item.get('recipient', 'Unknown')}\n"
                    else:
                        md += f"- {item}\n"
                md += "\n"
            
            if session.plot_developments:
                md += "**Plot Developments:**\n"
                for dev in session.plot_developments:
                    md += f"- {dev}\n"
                md += "\n"
            
            md += "---\n\n"
        
        with open(filepath, 'w') as f:
            f.write(md)
        logger.info(f"Campaign exported to {filepath}")

    def get_character_sheet(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a character."""
        if not self.current_campaign:
            return None
        
        campaign = self.campaigns[self.current_campaign]
        
        for char in campaign.characters:
            if char.name.lower() == character_name.lower():
                return char.to_dict()
        return None


def main():
    """CLI for campaign logger."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DnD Campaign Logger v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python campaign_logger.py new "Rise of Tiamat" --dm "John"
  python campaign_logger.py session "The Goblin Cave" --summary "Party explores..."
  python campaign_logger.py add-char "Thorin" --player "Alice" --class Fighter
  python campaign_logger.py export campaign.md --format markdown
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # New campaign
    new_parser = subparsers.add_parser("new", help="Create new campaign")
    new_parser.add_argument("name", help="Campaign name")
    new_parser.add_argument("--dm", required=True, help="DM name")
    new_parser.add_argument("--setting", help="Campaign setting")
    new_parser.add_argument("--tone", help="Campaign tone")
    
    # Log session
    session_parser = subparsers.add_parser("session", help="Log a session")
    session_parser.add_argument("title", help="Session title")
    session_parser.add_argument("--summary", required=True, help="Session summary")
    session_parser.add_argument("--date", help="Session date (YYYY-MM-DD)")
    session_parser.add_argument("--duration", type=float, default=4.0, help="Duration in hours")
    session_parser.add_argument("--xp", nargs="+", metavar="CHAR:XP", help="XP awards (CHAR:XP format)")
    session_parser.add_argument("--dm-notes", help="Private DM notes")
    
    # Add character
    char_parser = subparsers.add_parser("add-char", help="Add a character")
    char_parser.add_argument("name", help="Character name")
    char_parser.add_argument("--player", required=True, help="Player name")
    char_parser.add_argument("--class", dest="char_class", required=True, help="Character class")
    char_parser.add_argument("--level", type=int, default=1, help="Starting level")
    char_parser.add_argument("--hp", type=int, default=0, help="Max HP")
    
    # Export
    export_parser = subparsers.add_parser("export", help="Export campaign")
    export_parser.add_argument("output", help="Output file path")
    export_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    
    # Summary
    subparsers.add_parser("summary", help="Show campaign summary")
    
    # Load
    load_parser = subparsers.add_parser("load", help="Load campaign from file")
    load_parser.add_argument("file", help="Campaign JSON file")
    
    args = parser.parse_args()
    
    logger_instance = CampaignLogger()
    
    if args.command == "new":
        logger_instance.create_campaign(
            name=args.name,
            dm_name=args.dm,
            setting=args.setting or "",
            tone=args.tone or ""
        )
        print(f"Created campaign: {args.name}")
        print(f"DM: {args.dm}")
    
    elif args.command == "session":
        # Parse XP awards
        xp_awarded = {}
        if args.xp:
            for award in args.xp:
                if ":" in award:
                    name, xp = award.split(":", 1)
                    xp_awarded[name.strip()] = int(xp.strip())
        
        logger_instance.log_session(
            title=args.title,
            summary=args.summary,
            date_played=args.date,
            duration_hours=args.duration,
            xp_awarded=xp_awarded,
            dm_notes=args.dm_notes or ""
        )
        print(f"Logged session: {args.title}")
    
    elif args.command == "add-char":
        logger_instance.add_character(
            name=args.name,
            player=args.player,
            char_class=args.char_class,
            level=args.level,
            hp_max=args.hp
        )
        print(f"Added character: {args.name}")
    
    elif args.command == "export":
        if args.format == "markdown":
            logger_instance.export_to_markdown(args.output)
        else:
            logger_instance.export_to_json(args.output)
        print(f"Exported to {args.output}")
    
    elif args.command == "summary":
        summary = logger_instance.get_campaign_summary()
        if "error" in summary:
            print(summary["error"])
        else:
            print(f"=== {summary['name']} ===")
            print(f"DM: {summary['dm']}")
            print(f"Setting: {summary['setting']}")
            print(f"Sessions: {summary['sessions_played']}")
            print(f"Total Play Time: {summary['total_play_time_hours']} hours")
            print(f"Characters: {summary['characters']}")
            print(f"Story Arcs: {summary['story_arcs']} ({summary['active_arcs']} active)")
    
    elif args.command == "load":
        logger_instance.load_campaign(args.file)
        print(f"Loaded campaign from {args.file}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
