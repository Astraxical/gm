#!/usr/bin/env python3
"""
DnD Faction Tracker v1.0

Track faction relationships, reputation, and influence.
Perfect for political campaigns and world-building.

Features:
- Multiple factions with relationships
- Reputation tracking per faction
- Influence points
- Faction quests and goals
- Relationship web visualization
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    ALLIED = "allied"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    UNFRIENDLY = "unfriendly"
    HOSTILE = "hostile"
    ENEMY = "enemy"


@dataclass
class Faction:
    """A faction or organization."""
    name: str
    description: str = ""
    alignment: str = "neutral"
    power_level: int = 3  # 1-5
    leader: str = ""
    headquarters: str = ""
    goals: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)
    key_members: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "alignment": self.alignment,
            "power_level": self.power_level,
            "leader": self.leader,
            "headquarters": self.headquarters,
            "goals": self.goals,
            "secrets": self.secrets,
            "key_members": self.key_members
        }


@dataclass
class Reputation:
    """Player reputation with a faction."""
    faction_name: str
    score: int = 0  # -100 to 100
    rank: str = "Unknown"
    quests_completed: int = 0
    favors_owed: int = 0
    favors_owned: int = 0
    
    @property
    def relationship(self) -> str:
        if self.score >= 80:
            return "allied"
        elif self.score >= 40:
            return "friendly"
        elif self.score >= -20:
            return "neutral"
        elif self.score >= -60:
            return "unfriendly"
        else:
            return "hostile"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "faction_name": self.faction_name,
            "score": self.score,
            "rank": self.rank,
            "relationship": self.relationship,
            "quests_completed": self.quests_completed,
            "favors_owed": self.favors_owed,
            "favors_owned": self.favors_owned
        }


class FactionTracker:
    """Track factions and relationships."""

    PREBUILT_FACTIONS = {
        "harpers": {
            "name": "Harpers",
            "description": "Secretive organization promoting justice and knowledge",
            "alignment": "neutral good",
            "power_level": 4,
            "goals": ["Defeat the Zhentarim", "Preserve ancient knowledge", "Protect the innocent"],
            "secrets": ["Have agents in every major city", "Possess artifacts of great power"]
        },
        "zhentarim": {
            "name": "Zhentarim",
            "description": "Mercantile organization seeking power through trade",
            "alignment": "neutral evil",
            "power_level": 4,
            "goals": ["Control trade routes", "Amass wealth", "Undermine rivals"],
            "secrets": ["Infiltrated merchant guilds", "Employ assassins"]
        },
        "lords_alliance": {
            "name": "Lords' Alliance",
            "description": "Political alliance of city-states",
            "alignment": "lawful neutral",
            "power_level": 5,
            "goals": ["Maintain order", "Defend civilization", "Expand influence"],
            "secrets": ["Secret treaties", "Political prisoners"]
        },
        "order_gauntlet": {
            "name": "Order of the Gauntlet",
            "description": "Holy warriors fighting evil",
            "alignment": "lawful good",
            "power_level": 3,
            "goals": ["Destroy undead", "Defeat fiends", "Uphold justice"],
            "secrets": ["Have a mole in the church", "Hunt a specific artifact"]
        },
        "emerald_enclave": {
            "name": "Emerald Enclave",
            "description": "Druids protecting nature",
            "alignment": "neutral",
            "power_level": 3,
            "goals": ["Preserve nature", "Stop industrial expansion", "Balance ecosystems"],
            "secrets": ["Control ancient circles", "Have awakened allies"]
        }
    }

    def __init__(self):
        self.factions: Dict[str, Faction] = {}
        self.reputations: Dict[str, Reputation] = {}
        self.relationships: Dict[str, Dict[str, str]] = {}
        self._load_prebuilt_factions()

    def _load_prebuilt_factions(self):
        """Load pre-built factions."""
        for key, data in self.PREBUILT_FACTIONS.items():
            faction = Faction(
                name=data["name"],
                description=data["description"],
                alignment=data["alignment"],
                power_level=data["power_level"],
                goals=data["goals"],
                secrets=data["secrets"]
            )
            self.factions[key] = faction
        
        # Set default relationships
        self._set_default_relationships()
        logger.debug(f"Loaded {len(self.PREBUILT_FACTIONS)} factions")

    def _set_default_relationships(self):
        """Set default faction relationships."""
        # Harpers vs Zhentarim: enemies
        self.set_relationship("harpers", "zhentarim", "enemy")
        # Lords Alliance friendly with Order
        self.set_relationship("lords_alliance", "order_gauntlet", "allied")
        # Emerald Enclave neutral with most
        self.set_relationship("emerald_enclave", "lords_alliance", "neutral")

    def add_faction(self, name: str, description: str = "", alignment: str = "neutral") -> Faction:
        """Add a new faction."""
        key = name.lower().replace(" ", "_")
        faction = Faction(name=name, description=description, alignment=alignment)
        self.factions[key] = faction
        return faction

    def set_relationship(self, faction1: str, faction2: str, relationship: str) -> None:
        """Set relationship between two factions."""
        if faction1 not in self.relationships:
            self.relationships[faction1] = {}
        self.relationships[faction1][faction2] = relationship
        # Symmetric
        if faction2 not in self.relationships:
            self.relationships[faction2] = {}
        self.relationships[faction2][faction1] = relationship

    def modify_reputation(self, faction_name: str, change: int, reason: str = "") -> int:
        """
        Modify reputation with a faction.
        
        Returns:
            New reputation score
        """
        key = faction_name.lower().replace(" ", "_")
        
        if key not in self.reputations:
            self.reputations[key] = Reputation(faction_name=faction_name)
        
        old_score = self.reputations[key].score
        self.reputations[key].score = max(-100, min(100, old_score + change))
        
        # Update rank
        score = self.reputations[key].score
        if score >= 80:
            self.reputations[key].rank = "Champion"
        elif score >= 60:
            self.reputations[key].rank = "Ally"
        elif score >= 40:
            self.reputations[key].rank = "Friend"
        elif score >= 20:
            self.reputations[key].rank = "Associate"
        elif score >= -20:
            self.reputations[key].rank = "Neutral"
        elif score >= -40:
            self.reputations[key].rank = "Rival"
        else:
            self.reputations[key].rank = "Enemy"
        
        logger.info(f"Reputation with {faction_name}: {old_score} → {self.reputations[key].score} ({reason})")
        return self.reputations[key].score

    def get_reputation(self, faction_name: str) -> Optional[Reputation]:
        """Get reputation with a faction."""
        key = faction_name.lower().replace(" ", "_")
        return self.reputations.get(key)

    def complete_quest(self, faction_name: str, reward: int = 10) -> Dict[str, Any]:
        """Complete a quest for a faction."""
        key = faction_name.lower().replace(" ", "_")
        if key not in self.reputations:
            self.reputations[key] = Reputation(faction_name=faction_name)
        
        self.reputations[key].quests_completed += 1
        new_score = self.modify_reputation(faction_name, reward, "Quest completed")
        
        return {
            "faction": faction_name,
            "new_reputation": new_score,
            "relationship": self.reputations[key].relationship,
            "quests_completed": self.reputations[key].quests_completed
        }

    def get_relationship_web(self) -> Dict[str, Dict[str, str]]:
        """Get the full relationship web."""
        return self.relationships

    def export_to_json(self, filepath: str) -> None:
        """Export faction data to JSON."""
        data = {
            "factions": {k: v.to_dict() for k, v in self.factions.items()},
            "reputations": {k: v.to_dict() for k, v in self.reputations.items()},
            "relationships": self.relationships
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported faction data to {filepath}")


def main():
    """CLI for faction tracker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD Faction Tracker v1.0")
    parser.add_argument("--list", action="store_true", help="List factions")
    parser.add_argument("--reputation", type=str, help="Check reputation with faction")
    parser.add_argument("--modify", type=str, help="Modify reputation (faction:change)")
    parser.add_argument("--quest", type=str, help="Complete quest for faction")
    parser.add_argument("--export", type=str, help="Export to JSON")
    
    args = parser.parse_args()
    
    tracker = FactionTracker()
    
    if args.list:
        print("=== Factions ===\n")
        for key, faction in tracker.factions.items():
            rep = tracker.get_reputation(faction.name)
            rep_str = f" | Rep: {rep.score} ({rep.relationship})" if rep else ""
            print(f"• {faction.name} ({faction.alignment}){rep_str}")
            print(f"  {faction.description}")
            if faction.goals:
                print(f"  Goals: {', '.join(faction.goals[:2])}")
            print()
    
    if args.reputation:
        rep = tracker.get_reputation(args.reputation)
        if rep:
            print(f"\nReputation with {rep.faction_name}:")
            print(f"  Score: {rep.score}")
            print(f"  Relationship: {rep.relationship}")
            print(f"  Rank: {rep.rank}")
            print(f"  Quests: {rep.quests_completed}")
        else:
            print(f"No reputation tracked with {args.reputation}")
    
    if args.modify:
        parts = args.modify.split(":")
        if len(parts) >= 2:
            faction = parts[0]
            change = int(parts[1])
            new_score = tracker.modify_reputation(faction, change)
            print(f"Reputation with {faction}: {new_score}")
    
    if args.quest:
        result = tracker.complete_quest(args.quest)
        print(f"\nQuest completed for {result['faction']}!")
        print(f"New reputation: {result['new_reputation']}")
        print(f"Relationship: {result['relationship']}")
    
    if args.export:
        tracker.export_to_json(args.export)
        print(f"Exported to {args.export}")


if __name__ == "__main__":
    main()
