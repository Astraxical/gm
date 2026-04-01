#!/usr/bin/env python3
"""
DnD GM Utilities - Collection of Quick Tools

Includes:
- Trap Generator
- Puzzle/Riddle Generator  
- Rumor Generator
- Villain Builder
- Social Encounter Tracker
- Chase Scene Tracker
- Handout Generator
- Session Timer
"""

import json
import random
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# TRAP GENERATOR
# =============================================================================

class TrapGenerator:
    """Generate random traps."""

    TRAP_TYPES = {
        "pit": {"name": "Pit Trap", "dc": 15, "damage": "1d6 per 10ft", "type": "falling"},
        "poison_dart": {"name": "Poison Dart", "dc": 15, "damage": "1d4 + poison", "type": "ranged"},
        "swinging_blade": {"name": "Swinging Blade", "dc": 16, "damage": "2d8 slashing", "type": "melee"},
        "fire_jet": {"name": "Fire Jet", "dc": 15, "damage": "2d6 fire", "type": "elemental"},
        "poison_gas": {"name": "Poison Gas", "dc": 15, "damage": "2d6 poison", "type": "cloud"},
        "collapsing_ceiling": {"name": "Collapsing Ceiling", "dc": 16, "damage": "3d6 bludgeoning", "type": "environment"},
        "scything_blade": {"name": "Scything Blade", "dc": 17, "damage": "2d10 slashing", "type": "melee"},
        "lightning_bolt": {"name": "Lightning Arc", "dc": 16, "damage": "3d6 lightning", "type": "elemental"},
        "freezing_blast": {"name": "Freezing Blast", "dc": 15, "damage": "2d6 cold + slowed", "type": "elemental"},
        "crushing_walls": {"name": "Crushing Walls", "dc": 18, "damage": "4d10 bludgeoning", "type": "environment"},
    }

    TRAP_LOCATIONS = [
        "in the floor", "in the ceiling", "in the walls", "on the door",
        "on the treasure chest", "on the stairs", "in the corridor",
        "at the entrance", "near the altar", "by the throne"
    ]

    TRAP_TRIGGERS = [
        "stepping on a pressure plate", "opening the door", "touching the treasure",
        "crossing the threshold", "pulling the lever", "speaking above a whisper",
        "carrying metal", "breaking a light beam", "after a time delay"
    ]

    def generate_trap(self, level: int = 1, location: str = "") -> Dict[str, Any]:
        """Generate a random trap."""
        trap_key = random.choice(list(self.TRAP_TYPES.keys()))
        trap = self.TRAP_TYPES[trap_key].copy()
        
        # Scale damage with level
        trap["perception_dc"] = trap["dc"] - 2 + (level // 3)
        trap["disable_dc"] = trap["dc"] + (level // 3)
        trap["attack_bonus"] = 5 + level
        trap["save_dc"] = trap["dc"] + level
        trap["location"] = location or random.choice(self.TRAP_LOCATIONS)
        trap["trigger"] = random.choice(self.TRAP_TRIGGERS)
        trap["hint"] = self._generate_hint(trap["type"])
        
        return trap

    def _generate_hint(self, trap_type: str) -> str:
        """Generate a clue that the trap exists."""
        hints = {
            "falling": "Scuff marks around the edges of the floor",
            "ranged": "Small holes visible in the walls",
            "melee": "Worn grooves in the floor",
            "elemental": "Burn marks or frost on nearby surfaces",
            "cloud": "Faint smell of almonds or sulfur",
            "environment": "Cracks in the walls and ceiling"
        }
        return hints.get(trap_type, "Something seems off about this area")


# =============================================================================
# PUZZLE/RIDDLE GENERATOR
# =============================================================================

class PuzzleGenerator:
    """Generate puzzles and riddles."""

    RIDDLES = [
        {
            "riddle": "I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?",
            "answer": "An echo",
            "difficulty": "easy"
        },
        {
            "riddle": "The more you take, the more you leave behind. What am I?",
            "answer": "Footsteps",
            "difficulty": "easy"
        },
        {
            "riddle": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?",
            "answer": "A map",
            "difficulty": "medium"
        },
        {
            "riddle": "What can you catch but not throw?",
            "answer": "A cold",
            "difficulty": "easy"
        },
        {
            "riddle": "I am always hungry, I must always be fed. The finger I touch will soon turn red. What am I?",
            "answer": "Fire",
            "difficulty": "medium"
        },
        {
            "riddle": "What has keys but no locks, space but no room, and you can enter but not go inside?",
            "answer": "A keyboard",
            "difficulty": "medium"
        },
        {
            "riddle": "I am not alive, but I grow. I don't have lungs, but I need air. I don't have a mouth, but water kills me. What am I?",
            "answer": "Fire",
            "difficulty": "medium"
        },
        {
            "riddle": "What can travel around the world while staying in a corner?",
            "answer": "A stamp",
            "difficulty": "hard"
        },
        {
            "riddle": "The person who makes it has no need of it. The person who buys it has no use for it. The person who uses it can neither see nor feel it. What is it?",
            "answer": "A coffin",
            "difficulty": "hard"
        },
        {
            "riddle": "What comes once in a minute, twice in a moment, but never in a thousand years?",
            "answer": "The letter M",
            "difficulty": "hard"
        },
    ]

    PUZZLE_TYPES = [
        {
            "name": "Symbol Alignment",
            "description": "Rotate rings or tiles to match a symbol pattern",
            "dc": 15,
            "hint": "Look for clues in the surrounding artwork"
        },
        {
            "name": "Weight Puzzle",
            "description": "Place correct weights on a scale",
            "dc": 14,
            "hint": "The inscription mentions sacred numbers"
        },
        {
            "name": "Light Reflection",
            "description": "Angle mirrors to direct light to a target",
            "dc": 16,
            "hint": "The light must touch the holy symbol"
        },
        {
            "name": "Sequence Puzzle",
            "description": "Press plates in the correct order",
            "dc": 15,
            "hint": "The murals show the sequence"
        },
        {
            "name": "Elemental Balance",
            "description": "Balance opposing elements on pedestals",
            "dc": 17,
            "hint": "Fire opposes water, earth opposes air"
        },
    ]

    def generate_riddle(self, difficulty: str = "") -> Dict[str, str]:
        """Generate a random riddle."""
        riddles = self.RIDDLES
        if difficulty:
            riddles = [r for r in riddles if r["difficulty"] == difficulty]
        return random.choice(riddles) if riddles else random.choice(self.RIDDLES)

    def generate_puzzle(self) -> Dict[str, Any]:
        """Generate a mechanical puzzle."""
        puzzle = random.choice(self.PUZZLE_TYPES).copy()
        puzzle["attempts"] = 3
        puzzle["consequence"] = random.choice([
            "Trap activates", "Alarm sounds", "Door locks permanently",
            "Poison gas releases", "Room begins to flood"
        ])
        return puzzle


# =============================================================================
# RUMOR GENERATOR
# =============================================================================

class RumorGenerator:
    """Generate tavern rumors and gossip."""

    RUMOR_TEMPLATES = [
        "They say {subject} was seen {action} near {location}",
        "Have you heard about {subject}? Apparently they {action}",
        "My cousin's friend knows someone who saw {subject} {action}",
        "The {location} has been {action} lately, mark my words",
        "I heard {subject} is looking for {object}",
        "They're saying {subject} found a {object} in the {location}",
        "Between you and me, {subject} has been {action}",
        "The {object} that was stolen from {location}? I hear {subject} has it",
    ]

    SUBJECTS = [
        "the mayor", "a wizard", "the blacksmith", "a dragon",
        "the king's advisor", "a bandit lord", "the high priest",
        "a mysterious stranger", "the local guildmaster", "an adventurer"
    ]

    ACTIONS = [
        "meeting with cultists", "hiding treasure", "planning a heist",
        "searching for an artifact", "fleeing from assassins",
        "training an army", "making a deal with devils",
        "discovering a secret passage", "being cursed", "coming into power"
    ]

    LOCATIONS = [
        "the old mill", "the abandoned mine", "the forest",
        "the castle ruins", "the tavern cellar", "the temple",
        "the wizard's tower", "the graveyard", "the caves"
    ]

    OBJECTS = [
        "ancient artifact", "dragon's hoard", "cursed item",
        "magical sword", "royal crown", "forbidden tome",
        "philosopher's stone", "map to treasure"
    ]

    def generate_rumor(self) -> str:
        """Generate a random rumor."""
        template = random.choice(self.RUMOR_TEMPLATES)
        
        return template.format(
            subject=random.choice(self.SUBJECTS),
            action=random.choice(self.ACTIONS),
            location=random.choice(self.LOCATIONS),
            object=random.choice(self.OBJECTS)
        )

    def generate_rumors(self, count: int = 5, truth_ratio: float = 0.6) -> List[Dict[str, Any]]:
        """
        Generate multiple rumors with some being true.
        
        Args:
            count: Number of rumors
            truth_ratio: Ratio of true rumors (0-1)
            
        Returns:
            List of rumor dicts with truth value
        """
        rumors = []
        for _ in range(count):
            is_true = random.random() < truth_ratio
            rumors.append({
                "text": self.generate_rumor(),
                "is_true": is_true,
                "hook": "Quest hook" if is_true else "Red herring"
            })
        return rumors


# =============================================================================
# VILLAIN BUILDER
# =============================================================================

class VillainBuilder:
    """Build complete villains with schemes and lairs."""

    VILLAIN_ARCHETYPES = [
        "The Conqueror", "The Cult Leader", "The Crime Lord",
        "The Fallen Hero", "The Mad Scientist", "The Necromancer",
        "The Corrupt Noble", "The Dragon", "The Demon Lord",
        "The Manipulator", "The Revenge Seeker", "The Zealot"
    ]

    MOTIVATIONS = [
        "Power and domination", "Revenge for past wrongs", "Religious fanaticism",
        "Protecting loved ones", "Immortality", "Wealth beyond measure",
        "Destroying civilization", "Creating a utopia", "Personal glory"
    ]

    LAIR_TYPES = [
        "Dark fortress", "Underground complex", "Floating castle",
        "Volcanic lair", "Sunken temple", "Mobile stronghold",
        "Dimensional pocket", "Ancient ruins", "Living organism"
    ]

    MINIONS = [
        "Goblin horde", "Undead army", "Cult fanatics",
        "Mercenary company", "Constructs", "Summoned demons",
        "Corrupted animals", "Brainwashed villagers", "Elite guards"
    ]

    def generate_villain(self, cr: int = 5, archetype: str = "") -> Dict[str, Any]:
        """Generate a complete villain."""
        villain = {
            "name": self._generate_villain_name(),
            "archetype": archetype or random.choice(self.VILLAIN_ARCHETYPES),
            "cr": cr,
            "motivation": random.choice(self.MOTIVATIONS),
            "goal": self._generate_goal(),
            "lair": {
                "type": random.choice(self.LAIR_TYPES),
                "defenses": self._generate_lair_defenses(),
                "traps": random.randint(2, 5)
            },
            "minions": {
                "type": random.choice(self.MINIONS),
                "count": random.randint(10, 100)
            },
            "scheme": self._generate_scheme(),
            "weakness": self._generate_weakness(),
            "quotes": self._generate_quotes()
        }
        return villain

    def _generate_villain_name(self) -> str:
        """Generate a villainous name."""
        prefixes = ["Mal", "Mor", "Dar", "Vex", "Zar", "Kor", "Thal", "Mor"]
        suffixes = ["ak", "us", "ion", "ar", "oth", "ax", "grim", "thane"]
        titles = ["the Dark", "the Cruel", "the Mad", "the Undying", "the Betrayer"]
        
        name = random.choice(prefixes) + random.choice(suffixes)
        if random.random() < 0.5:
            name += " " + random.choice(titles)
        return name

    def _generate_goal(self) -> str:
        """Generate villain goal."""
        goals = [
            "Obtain the {artifact} to gain ultimate power",
            "Resurrect their dead {relation}",
            "Destroy the {organization}",
            "Conquer the {location}",
            "Open a portal to the {plane}",
            "Collect the {number} {items}"
        ]
        goal = random.choice(goals)
        return goal.format(
            artifact=random.choice(["Orb", "Crown", "Staff", "Tome"]),
            relation=random.choice(["spouse", "child", "parent", "sibling"]),
            organization=random.choice(["Kingdom", "Church", "Guild"]),
            location=random.choice(["Capital", "Continent", "World"]),
            plane=random.choice(["Nine Hells", "Abyss", "Elemental Chaos"]),
            number=random.randint(3, 7),
            items=random.choice(["Crystals", "Keys", "Artifacts", "Souls"])
        )

    def _generate_lair_defenses(self) -> List[str]:
        """Generate lair defenses."""
        defenses = [
            "Magical wards alert to intruders",
            "Guard beasts patrol the perimeter",
            "Hidden entrances and exits",
            "Traps in key locations",
            "Loyal guards stationed throughout",
            "Magical barriers block access"
        ]
        return random.sample(defenses, random.randint(2, 4))

    def _generate_scheme(self) -> str:
        """Generate villain's current scheme."""
        schemes = [
            "Infiltrating the local government",
            "Collecting components for a ritual",
            "Building an army of {minions}",
            "Sabotaging the kingdom's defenses",
            "Searching for an ancient {artifact}",
            "Corrupting the local {location}"
        ]
        return random.choice(schemes).format(
            minions=random.choice(["undead", "demons", "mercenaries"]),
            artifact=random.choice(["weapon", "relic", "tome"]),
            location=random.choice(["temple", "castle", "forest"])
        )

    def _generate_weakness(self) -> str:
        """Generate villain weakness."""
        return random.choice([
            "Overconfidence in their plans",
            "Attachment to a specific {object}",
            "Fear of {thing}",
            "Vulnerable when performing {action}",
            "Their {relation} is their weakness"
        ]).format(
            object=random.choice(["phylactery", "familiar", "weapon"]),
            thing=random.choice(["holy symbols", "a specific material", "their past"]),
            action=random.choice(["the ritual", "transforming", "casting"]),
            relation=random.choice(["child", "spouse", "former mentor"])
        )

    def _generate_quotes(self) -> List[str]:
        """Generate villain quotes."""
        return [
            f"You think you can stop {self._generate_goal()[:30]}...?",
            "Foolish heroes, you've played right into my hands!",
            "Join me, and together we can rule!",
            "This is not the end... it is only the beginning!"
        ]


# =============================================================================
# MAIN CLI
# =============================================================================

def main():
    """CLI for GM utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD GM Utilities")
    
    subparsers = parser.add_subparsers(dest="tool", help="Tool to use")
    
    # Trap generator
    trap_parser = subparsers.add_parser("trap", help="Generate a trap")
    trap_parser.add_argument("-l", "--level", type=int, default=1)
    
    # Riddle generator
    riddle_parser = subparsers.add_parser("riddle", help="Generate a riddle")
    riddle_parser.add_argument("-d", "--difficulty", choices=["easy", "medium", "hard"])
    
    # Puzzle generator
    subparsers.add_parser("puzzle", help="Generate a puzzle")
    
    # Rumor generator
    rumor_parser = subparsers.add_parser("rumor", help="Generate rumors")
    rumor_parser.add_argument("-n", "--count", type=int, default=5)
    
    # Villain generator
    villain_parser = subparsers.add_parser("villain", help="Generate a villain")
    villain_parser.add_argument("--cr", type=int, default=5)
    
    args = parser.parse_args()
    
    if args.tool == "trap":
        gen = TrapGenerator()
        trap = gen.generate_trap(level=args.level)
        print(f"\n=== {trap['name']} ===")
        print(f"Location: {trap['location']}")
        print(f"Trigger: {trap['trigger']}")
        print(f"Perception DC: {trap['perception_dc']}")
        print(f"Disable DC: {trap['disable_dc']}")
        print(f"Damage: {trap['damage']}")
        print(f"Hint: {trap['hint']}")
    
    elif args.tool == "riddle":
        gen = PuzzleGenerator()
        riddle = gen.generate_riddle(args.difficulty)
        print(f"\nRiddle ({riddle['difficulty']}):")
        print(f"  {riddle['riddle']}")
        print(f"\nAnswer: {riddle['answer']}")
    
    elif args.tool == "puzzle":
        gen = PuzzleGenerator()
        puzzle = gen.generate_puzzle()
        print(f"\n=== {puzzle['name']} ===")
        print(f"Description: {puzzle['description']}")
        print(f"DC: {puzzle['dc']}")
        print(f"Hint: {puzzle['hint']}")
        print(f"Consequence: {puzzle['consequence']}")
    
    elif args.tool == "rumor":
        gen = RumorGenerator()
        rumors = gen.generate_rumors(args.count)
        print(f"\n=== Tavern Rumors ({args.count}) ===\n")
        for i, rumor in enumerate(rumors, 1):
            truth = "TRUE" if rumor["is_true"] else "FALSE"
            print(f"{i}. {rumor['text']}")
            print(f"   [DM: {truth} - {rumor['hook']}]\n")
    
    elif args.tool == "villain":
        gen = VillainBuilder()
        villain = gen.generate_villain(cr=args.cr)
        print(f"\n=== {villain['name']} ===")
        print(f"Archetype: {villain['archetype']}")
        print(f"CR: {villain['cr']}")
        print(f"Motivation: {villain['motivation']}")
        print(f"Goal: {villain['goal']}")
        print(f"\nLair: {villain['lair']['type']}")
        for defense in villain['lair']['defenses']:
            print(f"  • {defense}")
        print(f"\nMinions: {villain['minions']['count']} {villain['minions']['type']}")
        print(f"\nCurrent Scheme: {villain['scheme']}")
        print(f"Weakness: {villain['weakness']}")
        print(f"\nQuotes:")
        for quote in villain['quotes'][:2]:
            print(f'  "{quote}"')
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
