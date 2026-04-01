#!/usr/bin/env python3
"""
DnD Random Event Generator v1.0

Generate story events, twists, complications, and plot hooks.
Keep your sessions unpredictable and engaging.

Features:
- Story event tables
- Plot twists
- Complications generator
- Encounter modifiers
- Social events
- Environmental events
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class StoryEvent:
    """A story event."""
    name: str
    category: str
    description: str
    hooks: List[str] = field(default_factory=list)
    complications: List[str] = field(default_factory=list)
    dc: int = 15
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "hooks": self.hooks,
            "complications": self.complications,
            "dc": self.dc
        }


class EventGenerator:
    """Generate random story events."""

    # Story event categories
    EVENT_TABLES = {
        "combat": [
            {"name": "Reinforcements Arrive", "description": "Enemy allies appear", "dc": 15},
            {"name": "Environmental Hazard", "description": "Terrain becomes dangerous", "dc": 14},
            {"name": "Morale Break", "description": "Enemies flee or surrender", "dc": 12},
            {"name": "Desperate Gambit", "description": "Enemy uses powerful ability", "dc": 16},
            {"name": "Third Party Joins", "description": "New faction enters combat", "dc": 15},
            {"name": "Weapon Breaks", "description": "Important equipment damaged", "dc": 13},
            {"name": "Magical Interference", "description": "Magic behaves strangely", "dc": 15},
            {"name": "Terrain Shift", "description": "Battlefield changes", "dc": 14},
        ],
        "social": [
            {"name": "Unexpected Ally", "description": "Stranger offers help", "dc": 12},
            {"name": "Hidden Agenda Revealed", "description": "True motives exposed", "dc": 16},
            {"name": "Mistaken Identity", "description": "Confused for someone else", "dc": 10},
            {"name": "Rival Appears", "description": "Competitor interferes", "dc": 14},
            {"name": "Opportunity Arises", "description": "Chance for advancement", "dc": 12},
            {"name": "Scandal Erupts", "description": "Embarrassing secret exposed", "dc": 15},
            {"name": "Diplomatic Incident", "description": "International tension", "dc": 17},
            {"name": "Plea for Help", "description": "Desperate NPC intervenes", "dc": 10},
        ],
        "exploration": [
            {"name": "Hidden Passage", "description": "Secret route discovered", "dc": 14},
            {"name": "Natural Disaster", "description": "Earthquake, flood, etc.", "dc": 16},
            {"name": "Ancient Ruins", "description": "Discovery of old structure", "dc": 12},
            {"name": "Dangerous Wildlife", "description": "Creatures block path", "dc": 13},
            {"name": "Magical Anomaly", "description": "Strange magical effect", "dc": 15},
            {"name": "Lost Traveler", "description": "Confused NPC found", "dc": 10},
            {"name": "Treasure Cache", "description": "Hidden valuables found", "dc": 12},
            {"name": "Blocked Path", "description": "Route impassable", "dc": 11},
        ],
        "mystery": [
            {"name": "Cryptic Message", "description": "Mysterious communication received", "dc": 14},
            {"name": "Evidence Found", "description": "Clue discovered", "dc": 12},
            {"name": "Witness Appears", "description": "Someone saw something", "dc": 11},
            {"name": "Red Herring", "description": "Misleading information", "dc": 13},
            {"name": "Pattern Emerges", "description": "Connection becomes clear", "dc": 15},
            {"name": "Time Pressure", "description": "Deadline revealed", "dc": 12},
            {"name": "Missing Piece", "description": "Something doesn't fit", "dc": 14},
            {"name": "Breakthrough", "description": "Major discovery made", "dc": 16},
        ],
        "downtime": [
            {"name": "Unexpected Visitor", "description": "Someone seeks the party", "dc": 10},
            {"name": "Business Opportunity", "description": "Investment chance arises", "dc": 12},
            {"name": "Festival/Event", "description": "Local celebration", "dc": 8},
            {"name": "Rumors Spread", "description": "News about the party", "dc": 11},
            {"name": "Training Available", "description": "New skill can be learned", "dc": 12},
            {"name": "Equipment Issue", "description": "Item needs repair/replacement", "dc": 10},
            {"name": "Personal Quest", "description": "Character-specific hook", "dc": 13},
            {"name": "Rest Interrupted", "description": "Peace disturbed", "dc": 12},
        ],
    }

    # Plot twist templates
    PLOT_TWISTS = [
        "The {ally} has been working with the {villain} all along",
        "The {artifact} is actually a {twist_object}",
        "The {location} is not what it seems - it's actually a {twist_location}",
        "The party member's {backstory_element} is a lie",
        "The {villain} is trying to prevent something worse than themselves",
        "The {quest_giver} created the problem they hired the party to solve",
        "The {prophecy} has been mistranslated - it means the opposite",
        "Time travel/alternate timeline is involved",
        "The {npc} is actually {true_identity} in disguise",
        "The party has been {twist_state} the entire time",
        "The {macguffin} is sentient and has its own agenda",
        "The {faction} the party works for is the real enemy",
        "The {villain}'s goal would actually save the world",
        "There is a mole within the party's allies",
        "The {location} is a living creature",
    ]

    TWIST_COMPONENTS = {
        "ally": ["mentor", "friend", "patron", "guide", "family member", "old hero"],
        "villain": ["main antagonist", "rival", "monster", "organization", "force of nature"],
        "artifact": ["sword", "orb", "tome", "crown", "amulet", "key"],
        "twist_object": ["prison for an ancient evil", "living creature", "fake", "cursed item", "key to something else"],
        "location": ["castle", "dungeon", "temple", "city", "forest", "tower"],
        "twist_location": ["living organism", "pocket dimension", "illusion", "time loop", "dream"],
        "backstory_element": ["trauma", "identity", "mission", "curse", "blessing", "quest"],
        "quest_giver": ["king", "priest", "merchant", "wizard", "noble", "commoner"],
        "prophecy": ["ancient prophecy", "divine message", "oracle's words", "written prediction"],
        "npc": ["guide", "merchant", "innkeeper", "guard", "scholar", "peasant"],
        "true_identity": ["the villain", "a celestial being", "a fiend", "an ancient dragon", "a god", "the hero's parent"],
        "twist_state": ["dead", "in a coma", "trapped in illusion", "in the past", "in someone else's dream"],
        "macguffin": ["artifact", "weapon", "tome", "creature", "person"],
        "faction": ["guild", "church", "kingdom", "order", "alliance"],
    }

    # Complication tables
    COMPLICATIONS = {
        "general": [
            "Time is running out faster than expected",
            "An important NPC is unavailable",
            "Required equipment is missing/broken",
            "Weather/environment works against the party",
            "Communication fails at critical moment",
            "Resources are depleted",
            "An unexpected witness complicates things",
            "The stakes are higher than realized",
        ],
        "combat": [
            "Hostages present",
            "Collateral damage risk",
            "Enemy has reinforcements coming",
            "Terrain favors the enemy",
            "Party member separated from group",
            "Magic/item malfunction",
            "Enemy knows party's tactics",
            "Morale is breaking",
        ],
        "social": [
            "Cultural misunderstanding",
            "Conflicting loyalties",
            "Past grudge resurfaces",
            "Someone is lying",
            "Information is incomplete",
            "Multiple parties want different things",
            "Public opinion matters",
            "Legal complications",
        ],
        "exploration": [
            "Map is wrong/incomplete",
            "Supplies running low",
            "Environmental hazard blocks path",
            "Creatures lair nearby",
            "Magical interference with navigation",
            "Party member afflicted with ailment",
            "Equipment failure",
            "Wrong path chosen",
        ],
    }

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_event(self, category: str = "general") -> StoryEvent:
        """Generate a random story event."""
        if category == "general":
            category = random.choice(list(self.EVENT_TABLES.keys()))
        
        table = self.EVENT_TABLES.get(category, self.EVENT_TABLES["exploration"])
        event_data = random.choice(table)
        
        return StoryEvent(
            name=event_data["name"],
            category=category,
            description=event_data["description"],
            dc=event_data.get("dc", 15),
            hooks=self._generate_hooks(category),
            complications=self._generate_complications(category)
        )

    def generate_plot_twist(self) -> str:
        """Generate a random plot twist."""
        template = random.choice(self.PLOT_TWISTS)
        
        # Fill in template
        result = template
        for key, options in self.TWIST_COMPONENTS.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, random.choice(options))
        
        return result

    def generate_complication(self, category: str = "general") -> str:
        """Generate a complication."""
        table = self.COMPLICATIONS.get(category, self.COMPLICATIONS["general"])
        return random.choice(table)

    def generate_multiple_events(self, count: int = 3, category: str = "general") -> List[StoryEvent]:
        """Generate multiple events."""
        return [self.generate_event(category) for _ in range(count)]

    def _generate_hooks(self, category: str) -> List[str]:
        """Generate adventure hooks for an event."""
        hooks = {
            "combat": [
                "What do the enemies want?",
                "Who sent them?",
                "What are they protecting?"
            ],
            "social": [
                "What does the NPC really want?",
                "What happens if the party refuses?",
                "Who else is involved?"
            ],
            "exploration": [
                "What lies beyond?",
                "Who created this?",
                "Why was this hidden?"
            ],
            "mystery": [
                "What does this clue mean?",
                "Who left this here?",
                "What is being concealed?"
            ],
            "downtime": [
                "What opportunity does this present?",
                "Who benefits?",
                "What strings are attached?"
            ],
        }
        return random.sample(hooks.get(category, hooks["exploration"]), 2)

    def _generate_complications(self, category: str) -> List[str]:
        """Generate complications for an event."""
        return [self.generate_complication(category) for _ in range(2)]

    def generate_session_events(self, session_type: str = "mixed") -> Dict[str, Any]:
        """Generate a set of events for a session."""
        events = {
            "opening": self.generate_event(random.choice(["exploration", "social"])),
            "complication": self.generate_event(random.choice(list(self.EVENT_TABLES.keys()))),
            "climax": self.generate_event("combat"),
            "twist": self.generate_plot_twist(),
            "hook_for_next": self.generate_event("mystery")
        }
        return events


def main():
    """CLI for event generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD Random Event Generator v1.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Command type")
    
    # Single event
    event_parser = subparsers.add_parser("event", help="Generate single event")
    event_parser.add_argument("-c", "--category", 
                             choices=["combat", "social", "exploration", "mystery", "downtime", "general"],
                             default="general")
    
    # Plot twist
    subparsers.add_parser("twist", help="Generate plot twist")
    
    # Complication
    comp_parser = subparsers.add_parser("complication", help="Generate complication")
    comp_parser.add_argument("-c", "--category", 
                            choices=["general", "combat", "social", "exploration"],
                            default="general")
    
    # Session events
    subparsers.add_parser("session", help="Generate session events")
    
    args = parser.parse_args()
    
    generator = EventGenerator()
    
    if args.command == "event" or not args.command:
        event = generator.generate_event(args.category)
        print(f"\n=== {event.name} ===")
        print(f"Category: {event.category}")
        print(f"Description: {event.description}")
        print(f"DC: {event.dc}")
        print(f"\nHooks:")
        for hook in event.hooks:
            print(f"  • {hook}")
        print(f"\nComplications:")
        for comp in event.complications:
            print(f"  • {comp}")
    
    elif args.command == "twist":
        twist = generator.generate_plot_twist()
        print(f"\n=== Plot Twist ===\n")
        print(f"  {twist}\n")
    
    elif args.command == "complication":
        comp = generator.generate_complication(args.category)
        print(f"\n=== Complication ({args.category}) ===\n")
        print(f"  {comp}\n")
    
    elif args.command == "session":
        events = generator.generate_session_events()
        print("\n=== Session Events ===\n")
        print(f"📖 Opening: {events['opening'].name}")
        print(f"   {events['opening'].description}")
        print(f"\n⚠️ Complication: {events['complication'].name}")
        print(f"   {events['complication'].description}")
        print(f"\n⚔️ Climax: {events['climax'].name}")
        print(f"   {events['climax'].description}")
        print(f"\n🔄 Twist: {events['twist']}")
        print(f"\n🎣 Hook for Next: {events['hook_for_next'].name}")
        print(f"   {events['hook_for_next'].description}")


if __name__ == "__main__":
    main()
