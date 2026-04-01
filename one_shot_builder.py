#!/usr/bin/env python3
"""
DnD One-Shot Adventure Builder v1.0

Generate complete 3-4 hour adventures with hooks, encounters, and rewards.
Perfect for convention games or filler sessions.

Features:
- Complete adventure structure
- Scaling by party level
- Multiple adventure templates
- Random encounter generation
- Treasure and rewards
- NPC generation integration
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
class Adventure:
    """Complete one-shot adventure."""
    title: str
    levels: str
    estimated_time: str
    theme: str
    hook: str
    backstory: str
    locations: List[Dict[str, Any]] = field(default_factory=list)
    npcs: List[Dict[str, Any]] = field(default_factory=list)
    encounters: List[Dict[str, Any]] = field(default_factory=list)
    treasure: List[Dict[str, Any]] = field(default_factory=list)
    conclusion: str = ""
    hooks_for_continuation: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "levels": self.levels,
            "estimated_time": self.estimated_time,
            "theme": self.theme,
            "hook": self.hook,
            "backstory": self.backstory,
            "locations": self.locations,
            "npcs": self.npcs,
            "encounters": self.encounters,
            "treasure": self.treasure,
            "conclusion": self.conclusion,
            "hooks_for_continuation": self.hooks_for_continuation
        }


class OneShotBuilder:
    """Build complete one-shot adventures."""

    ADVENTURE_TEMPLATES = {
        "rescue": {
            "title_prefix": ["The Rescue of", "Saving", "The Liberation of"],
            "locations": ["Goblin Lair", "Bandit Camp", "Cult Temple", "Tower Prison", "Underground Dungeon"],
            "enemies": ["Goblins", "Bandits", "Cultists", "Ogres", "Undead"],
            "twist": [
                "The captive doesn't want to be rescued",
                "The captive is actually a powerful mage testing the party",
                "The captors are protecting the world from the captive",
                "The captive has been replaced by a doppelganger"
            ]
        },
        "hunt": {
            "title_prefix": ["The Hunt for", "Tracking", "The Pursuit of"],
            "locations": ["Ancient Forest", "Mountain Pass", "Swamp Ruins", "Desert Oasis", "Coastal Cave"],
            "enemies": ["Monster", "Dragon Wyrmling", "Giant", "Roc", "Hydra"],
            "twist": [
                "The monster is the last of its kind",
                "The monster is protecting something valuable",
                "The monster was created by the quest giver",
                "The monster can communicate and has a valid grievance"
            ]
        },
        "retrieve": {
            "title_prefix": ["The Quest for", "Retrieving", "The Search for"],
            "locations": ["Lost Tomb", "Sunken Ship", "Dragon's Hoard", "Wizard's Tower", " Fey Crossing"],
            "enemies": ["Guardians", "Traps", "Rival Adventurers", "Undead", "Constructs"],
            "twist": [
                "The artifact is cursed",
                "The artifact is sentient",
                "The artifact is a fake - the real one is elsewhere",
                "The artifact chooses who can wield it"
            ]
        },
        "defend": {
            "title_prefix": ["Defense of", "Holding", "The Battle for"],
            "locations": ["Village", "Bridge", "Temple", "Keep", "Caravan"],
            "enemies": ["Orc Horde", "Undead Army", "Bandit Gang", "Monster Swarm", "Invading Force"],
            "twist": [
                "There's a traitor within",
                "The enemy has a siege weapon",
                "Civilians are hiding who shouldn't be",
                "Reinforcements aren't coming"
            ]
        },
        "mystery": {
            "title_prefix": ["The Mystery of", "Investigating", "The Secret of"],
            "locations": ["Manor House", "Small Town", "Academy", "Monastery", "Noble Estate"],
            "enemies": ["Killer", "Cult", "Spy Network", "Corrupt Official", "Supernatural Force"],
            "twist": [
                "The victim isn't dead",
                "The detective is the culprit",
                "Everyone is lying about something",
                "The crime was meant to hide a different crime"
            ]
        },
    }

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def build_adventure(
        self,
        theme: str = "rescue",
        party_level: int = 3,
        party_size: int = 4
    ) -> Adventure:
        """Build a complete one-shot adventure."""
        template = self.ADVENTURE_TEMPLATES.get(theme, self.ADVENTURE_TEMPLATES["rescue"])
        
        adventure = Adventure(
            title=f"{random.choice(template['title_prefix'])} {self._generate_specific_element(theme)}",
            levels=f"{party_level}-{party_level + 2}",
            estimated_time="3-4 hours",
            theme=theme,
            hook=self._generate_hook(theme),
            backstory=self._generate_backstory(theme),
            locations=self._generate_locations(template, party_level),
            npcs=self._generate_npcs(theme),
            encounters=self._generate_encounters(party_level, party_size),
            treasure=self._generate_treasure(party_level),
            conclusion=self._generate_conclusion(theme),
            hooks_for_continuation=self._generate_continuation_hooks(theme)
        )
        
        logger.info(f"Built adventure: {adventure.title}")
        return adventure

    def _generate_specific_element(self, theme: str) -> str:
        """Generate specific element based on theme."""
        elements = {
            "rescue": ["the Missing Noble", "the Captured Merchant", "the Kidnapped Children", "the Stolen Heirloom"],
            "hunt": ["the Shadow Beast", "the Man-Eater", "the Thunder Bird", "the Cave Drake"],
            "retrieve": ["the Crystal of Power", "the Lost Tome", "the Ancestral Sword", "the Sacred Relic"],
            "defend": ["Millbrook Village", "the Stone Bridge", "the Temple of Light", "the Winter Keep"],
            "mystery": ["the Locked Room", "the Vanishing", "the Poisoned Chalice", "the Midnight Murders"],
        }
        return random.choice(elements.get(theme, ["the Unknown"]))

    def _generate_hook(self, theme: str) -> str:
        """Generate adventure hook."""
        hooks = {
            "rescue": [
                "A desperate NPC begs the party to save their loved one",
                "A ransom note arrives demanding payment",
                "Screams are heard from a nearby location",
                "The local lord offers a reward for safe return"
            ],
            "hunt": [
                "Livestock and travelers have been disappearing",
                "A bounty is posted for a dangerous creature",
                "A hunter hires the party to track a legendary beast",
                "The creature threatens a settlement's survival"
            ],
            "retrieve": [
                "A scholar needs an ancient text from a dangerous location",
                "A family heirloom was stolen by monsters",
                "A magical item is needed to break a curse",
                "A collector offers payment for a rare artifact"
            ],
            "defend": [
                "Refugees arrive warning of an approaching threat",
                "A small community begs for protection",
                "A strategic location must be held at all costs",
                "The party is escorting something valuable"
            ],
            "mystery": [
                "A prominent figure is found dead under strange circumstances",
                "People are disappearing without a trace",
                "Strange events plague a peaceful location",
                "An anonymous letter hints at dark secrets"
            ],
        }
        return random.choice(hooks.get(theme, ["Adventure awaits!"]))

    def _generate_backstory(self, theme: str) -> str:
        """Generate adventure backstory."""
        backstories = {
            "rescue": "The captive was taken by {enemy} who demand {demand}. But there's more to the story than first appears.",
            "hunt": "The {monster} has terrorized the region for {time}. Local legends say it was {origin}.",
            "retrieve": "The {artifact} was lost when {event}. Now {faction} seeks to claim its power.",
            "defend": "The {location} stands between {threat} and innocent lives. Time is running out.",
            "mystery": "What began as {initial} has revealed deeper conspiracies. Someone will kill to keep secrets hidden.",
        }
        
        fills = {
            "enemy": random.choice(["goblins", "a necromancer", "a dragon", "bandits"]),
            "demand": random.choice(["gold", "political concessions", "a magical item", "surrender"]),
            "monster": random.choice(["beast", "creature", "predator"]),
            "time": random.choice(["months", "years", "generations"]),
            "origin": random.choice(["created by a wizard", "cursed", "the last of its kind", "summoned"]),
            "artifact": random.choice(["artifact", "weapon", "tome"]),
            "event": random.choice(["a battle", "a betrayal", "an earthquake", "a theft"]),
            "faction": random.choice(["a cult", "a rival kingdom", "a thieves guild"]),
            "location": random.choice(["village", "keep", "bridge"]),
            "threat": random.choice(["an army", "a horde", "dark forces"]),
            "initial": random.choice(["a simple disappearance", "a strange death"]),
        }
        
        story = backstories.get(theme, backstories["rescue"])
        for key, value in fills.items():
            story = story.replace("{" + key + "}", value)
        return story

    def _generate_locations(self, template: Dict, level: int) -> List[Dict[str, Any]]:
        """Generate adventure locations."""
        locations = []
        main_location = random.choice(template["locations"])
        
        # Entrance
        locations.append({
            "name": f"Entrance to {main_location}",
            "type": "entrance",
            "description": "The party arrives at the location.",
            "encounters": 0,
            "features": ["Signs of recent activity", "Possible guards or wards"]
        })
        
        # Middle areas
        for i in range(2):
            locations.append({
                "name": f"{main_location} - Area {i + 1}",
                "type": "interior",
                "description": f"Deeper within the {main_location}.",
                "encounters": 1,
                "features": self._generate_features(level)
            })
        
        # Climax location
        locations.append({
            "name": f"{main_location} - Heart",
            "type": "climax",
            "description": "The final confrontation awaits here.",
            "encounters": 1,
            "features": ["Boss enemy", "Objective location", "Escape route"]
        })
        
        return locations

    def _generate_features(self, level: int) -> List[str]:
        """Generate location features."""
        features = [
            "Difficult terrain", "Cover opportunities", "Environmental hazard",
            "Hidden compartment", "Ancient writings", "Trapped area",
            "Magical anomaly", "Multiple levels", "Limited visibility"
        ]
        return random.sample(features, min(3, len(features)))

    def _generate_npcs(self, theme: str) -> List[Dict[str, Any]]:
        """Generate NPCs for the adventure."""
        npcs = []
        
        # Quest giver
        npcs.append({
            "role": "Quest Giver",
            "description": self._generate_npc_description(),
            "motivation": "Needs the party's help",
            "reward": "Gold and gratitude"
        })
        
        # Ally/Contact
        npcs.append({
            "role": "Local Contact",
            "description": self._generate_npc_description(),
            "motivation": "Has information to share",
            "reward": "Protection or favor"
        })
        
        # Villain
        npcs.append({
            "role": "Antagonist",
            "description": self._generate_npc_description(),
            "motivation": self._generate_villain_motivation(theme),
            "reward": "Defeat brings resolution"
        })
        
        return npcs

    def _generate_npc_description(self) -> str:
        """Generate NPC description."""
        appearances = ["weathered", "well-dressed", "nervous", "confident", "mysterious"]
        ages = ["elderly", "middle-aged", "young"]
        features = ["scarred", "kind-eyed", "sharp-featured", "gentle", "intense"]
        
        return f"A {random.choice(appearances)} {random.choice(ages)} person with {random.choice(features)} features"

    def _generate_villain_motivation(self, theme: str) -> str:
        """Generate villain motivation."""
        motivations = [
            "Power and control", "Revenge", "Desperation", "Misguided belief",
            "Following orders", "Personal gain", "Protecting something"
        ]
        return random.choice(motivations)

    def _generate_encounters(self, level: int, size: int) -> List[Dict[str, Any]]:
        """Generate encounters scaled to party."""
        encounters = []
        
        # Easy encounter
        encounters.append({
            "name": "Opening Encounter",
            "difficulty": "easy",
            "description": "Tests party resources",
            "enemies": f"2-4 enemies (CR {max(0, level - 2)}-{level - 1})",
            "xp": self._calculate_xp(level, size, "easy")
        })
        
        # Medium encounter
        encounters.append({
            "name": "Mid-Adventure Challenge",
            "difficulty": "medium",
            "description": "Requires tactics",
            "enemies": f"3-5 enemies (CR {level - 1}-{level})",
            "xp": self._calculate_xp(level, size, "medium")
        })
        
        # Hard encounter
        encounters.append({
            "name": "Pre-Boss Challenge",
            "difficulty": "hard",
            "description": "Drains party resources",
            "enemies": f"Elite enemy + minions (CR {level + 1})",
            "xp": self._calculate_xp(level, size, "hard")
        })
        
        # Boss encounter
        encounters.append({
            "name": "Final Confrontation",
            "difficulty": "deadly",
            "description": "Climactic battle",
            "enemies": f"Boss (CR {level + 2}) + lair actions",
            "xp": self._calculate_xp(level, size, "deadly")
        })
        
        return encounters

    def _calculate_xp(self, level: int, size: int, difficulty: str) -> int:
        """Calculate XP for encounter."""
        base_xp = {
            "easy": 50,
            "medium": 100,
            "hard": 200,
            "deadly": 400
        }
        return base_xp.get(difficulty, 100) * level * size

    def _generate_treasure(self, level: int) -> List[Dict[str, Any]]:
        """Generate treasure rewards."""
        return [
            {
                "type": "Gold",
                "amount": f"{level * 50}-{level * 100} gp",
                "description": "Found in villain's hoard"
            },
            {
                "type": "Magic Item",
                "amount": "1 item",
                "description": f"Uncommon rarity (appropriate for level {level})"
            },
            {
                "type": "Story Reward",
                "amount": "Reputation, contacts, future hooks",
                "description": "Relationships and plot development"
            }
        ]

    def _generate_conclusion(self, theme: str) -> str:
        """Generate adventure conclusion."""
        conclusions = {
            "rescue": "The captive is freed and returns home. The party's heroism spreads through the region.",
            "hunt": "The creature is dealt with, and the land is safe once more. Hunters sing the party's praises.",
            "retrieve": "The artifact is secured. What the party does with it may shape the future.",
            "defend": "The location stands, thanks to the party's bravery. Survivors owe them their lives.",
            "mystery": "The truth is revealed, justice is served. But some questions may remain unanswered."
        }
        return conclusions.get(theme, "The adventure concludes, but the legend begins.")

    def _generate_continuation_hooks(self, theme: str) -> List[str]:
        """Generate hooks for campaign continuation."""
        hooks = [
            "The villain worked for a larger organization",
            "A clue points to a greater threat",
            "The rescued/captured item has unexpected properties",
            "An NPC from the adventure seeks the party later",
            "The location holds secrets yet to be discovered"
        ]
        return random.sample(hooks, 3)

    def export_to_json(self, adventure: Adventure, filepath: str) -> None:
        """Export adventure to JSON."""
        with open(filepath, 'w') as f:
            json.dump(adventure.to_dict(), f, indent=2)
        logger.info(f"Exported adventure to {filepath}")

    def display_adventure(self, adventure: Adventure) -> str:
        """Display adventure in readable format."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"📖 {adventure.title}")
        lines.append("=" * 70)
        lines.append(f"Levels: {adventure.levels} | Time: {adventure.estimated_time}")
        lines.append(f"Theme: {adventure.theme}")
        
        lines.append(f"\n🎣 Hook:")
        lines.append(f"   {adventure.hook}")
        
        lines.append(f"\n📜 Backstory:")
        lines.append(f"   {adventure.backstory}")
        
        lines.append(f"\n📍 Locations:")
        for loc in adventure.locations:
            lines.append(f"   • {loc['name']} ({loc['type']})")
        
        lines.append(f"\n👥 NPCs:")
        for npc in adventure.npcs:
            lines.append(f"   • {npc['role']}: {npc['description']}")
        
        lines.append(f"\n⚔️ Encounters:")
        for enc in adventure.encounters:
            lines.append(f"   • {enc['name']} ({enc['difficulty']})")
            lines.append(f"     {enc['enemies']}")
        
        lines.append(f"\n💰 Treasure:")
        for t in adventure.treasure:
            lines.append(f"   • {t['type']}: {t['amount']}")
        
        lines.append(f"\n🏁 Conclusion:")
        lines.append(f"   {adventure.conclusion}")
        
        lines.append(f"\n🔗 Continuation Hooks:")
        for hook in adventure.hooks_for_continuation:
            lines.append(f"   • {hook}")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    """CLI for one-shot builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD One-Shot Adventure Builder v1.0")
    parser.add_argument("-t", "--theme",
                       choices=["rescue", "hunt", "retrieve", "defend", "mystery"],
                       default="rescue")
    parser.add_argument("-l", "--level", type=int, default=3, help="Party level")
    parser.add_argument("-s", "--size", type=int, default=4, help="Party size")
    parser.add_argument("-o", "--output", help="Export to JSON file")
    
    args = parser.parse_args()
    
    builder = OneShotBuilder()
    adventure = builder.build_adventure(args.theme, args.level, args.size)
    
    print(builder.display_adventure(adventure))
    
    if args.output:
        builder.export_to_json(adventure, args.output)
        print(f"\nExported to {args.output}")


if __name__ == "__main__":
    main()
