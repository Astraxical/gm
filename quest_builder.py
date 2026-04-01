#!/usr/bin/env python3
"""
DnD Quest Builder v1.0

Generate complete quest templates with hooks, objectives, complications, and rewards.
Uses template-based generation with customizable parameters.

Features:
- 8 quest hook templates with 20+ value variations each
- Quest complexity levels (simple, moderate, complex, epic)
- Automatic NPC generation integration
- Complication and twist generation
- Reward scaling by party level
- Export to JSON for VTT integration
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any, TypedDict
from pathlib import Path
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    from npc_gen import NPCGenerator
    from sentence_forge import SentenceGenerator
except ImportError:
    NPCGenerator = None
    SentenceGenerator = None


class QuestHook(TypedDict):
    """Type definition for quest hook template."""
    template: str
    values: Dict[str, List[str]]


class QuestComplication(TypedDict):
    """Type definition for quest complication."""
    name: str
    description: str
    dc: int
    consequence: str


class QuestReward(TypedDict):
    """Type definition for quest reward."""
    type: str
    amount: int
    description: str


class QuestBuilder:
    """Generate complete DnD quests with hooks, complications, and rewards."""

    # Quest complexity levels with recommended party levels
    COMPLEXITY_LEVELS = {
        "simple": {"level_range": (1, 4), "xp": 500, "difficulty": "easy"},
        "moderate": {"level_range": (3, 8), "xp": 1500, "difficulty": "medium"},
        "complex": {"level_range": (7, 12), "xp": 5000, "difficulty": "hard"},
        "epic": {"level_range": (11, 20), "xp": 15000, "difficulty": "deadly"}
    }

    # Quest types with associated mechanics
    QUEST_TYPES = {
        "rescue": {
            "objectives": ["rescue the prisoners", "save the kidnapped noble", "free the captured villagers"],
            "enemies": ["goblin raiders", "bandits", "cultists", "slavers"],
            "skill_checks": ["Stealth", "Investigation", "Persuasion"]
        },
        "hunt": {
            "objectives": ["hunt the monster", "track the beast", "eliminate the threat"],
            "enemies": ["dragon", "manticore", "chimera", "ogre", "troll"],
            "skill_checks": ["Survival", "Animal Handling", "Athletics"]
        },
        "retrieve": {
            "objectives": ["retrieve the artifact", "recover the relic", "find the lost item"],
            "enemies": ["undead", "traps", "rival adventurers", "guardians"],
            "skill_checks": ["Investigation", "Arcana", "Perception"]
        },
        "escort": {
            "objectives": ["escort the caravan", "protect the diplomat", "guide the refugees"],
            "enemies": ["ambushers", "bandits", "monsters", "weather"],
            "skill_checks": ["Perception", "Survival", "Persuasion"]
        },
        "investigate": {
            "objectives": ["investigate the disturbance", "solve the mystery", "uncover the plot"],
            "enemies": ["spies", "cultists", "corrupt officials", "secret society"],
            "skill_checks": ["Investigation", "Insight", "History"]
        },
        "defend": {
            "objectives": ["defend the village", "protect the ritual", "hold the bridge"],
            "enemies": ["invading army", "undead horde", "monster swarm", "raiders"],
            "skill_checks": ["Athletics", "Intimidation", "Medicine"]
        },
        "assassinate": {
            "objectives": ["eliminate the target", "remove the threat", "silent takedown"],
            "enemies": ["tyrant", "crime lord", "corrupt noble", "enemy commander"],
            "skill_checks": ["Stealth", "Deception", "Sleight of Hand"]
        },
        "diplomacy": {
            "objectives": ["negotiate peace", "forge alliance", "resolve dispute"],
            "enemies": ["political rivals", "warmongers", "saboteurs", "misunderstandings"],
            "skill_checks": ["Persuasion", "Insight", "History"]
        }
    }

    # Complications that can arise during quests
    COMPLICATIONS: List[QuestComplication] = [
        {
            "name": "Unexpected Ally",
            "description": "A former enemy offers assistance, but their motives are unclear.",
            "dc": 14,
            "consequence": "If trusted, they provide valuable aid. If betrayed, they become a future enemy."
        },
        {
            "name": "Time Pressure",
            "description": "The quest must be completed before a deadline.",
            "dc": 12,
            "consequence": "Failure means the objective is lost or the situation worsens significantly."
        },
        {
            "name": "Moral Dilemma",
            "description": "The party must choose between two equally important outcomes.",
            "dc": 15,
            "consequence": "Either choice has significant consequences for the campaign."
        },
        {
            "name": "Hidden Traitor",
            "description": "Someone working with the party is secretly undermining them.",
            "dc": 16,
            "consequence": "Discovery leads to confrontation; failure means sabotage at a critical moment."
        },
        {
            "name": "Environmental Hazard",
            "description": "Weather, terrain, or magical effects complicate the journey.",
            "dc": 13,
            "consequence": "Party takes damage or loses resources before reaching the objective."
        },
        {
            "name": "Rival Party",
            "description": "Another group is pursuing the same goal.",
            "dc": 14,
            "consequence": "Race against time; losers face consequences from the winners' success."
        },
        {
            "name": "Magical Interference",
            "description": "Magic behaves strangely in the area.",
            "dc": 15,
            "consequence": "Spellcasters must make concentration checks or spells fail."
        },
        {
            "name": "Insufficient Resources",
            "description": "The party lacks key equipment or information.",
            "dc": 12,
            "consequence": "Must find alternative solutions or acquire missing resources first."
        },
        {
            "name": "Civilian Casualties",
            "description": "Innocents are in the crossfire.",
            "dc": 14,
            "consequence": "Failure to protect them results in reputation loss and guilt."
        },
        {
            "name": "The True Enemy",
            "description": "The apparent villain is working for someone worse.",
            "dc": 18,
            "consequence": "Defeating the boss reveals a greater threat lurking behind the scenes."
        }
    ]

    # Twist templates for quest revelations
    TWISTS = [
        "The {QUEST_GIVER} was manipulating the party all along.",
        "The {THREAT} was actually trying to prevent something worse.",
        "The {OBJECTIVE} has unintended consequences when completed.",
        "A party member has a hidden connection to the quest.",
        "The {LOCATION} holds a secret that changes everything.",
        "The real villain has been pulling strings from the shadows.",
        "Completing the quest triggers an ancient prophecy.",
        "The {NPC} is actually {TRUE_IDENTITY} in disguise."
    ]

    TRUE_IDENTITIES = [
        "a celestial being", "a fiend in disguise", "an ancient dragon",
        "a time traveler", "a clone of a PC", "a legendary hero",
        "the BBEG's puppet", "a deity in mortal form"
    ]

    def __init__(self, data_dir: Optional[str] = None, seed: Optional[int] = None):
        """
        Initialize the quest builder.

        Args:
            data_dir: Directory containing quest data files
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"
        self.quest_hooks: Optional[QuestHook] = None
        self._load_quest_hooks()

        # Initialize generators if available
        self.npc_generator = NPCGenerator(seed=seed) if NPCGenerator else None
        self._load_quest_hooks()

    def _load_quest_hooks(self):
        """Load quest hook templates from data file."""
        hooks_file = self.data_dir / "quest_hooks.json"
        if hooks_file.exists():
            with open(hooks_file, 'r') as f:
                self.quest_hooks = json.load(f)
            logger.debug(f"Loaded {len(self.quest_hooks.get('templates', []))} quest hook templates")
        else:
            logger.warning(f"Quest hooks file not found at {hooks_file}")
            self.quest_hooks = {
                "templates": ["{QUEST_GIVER} needs help with {OBJECTIVE} in {LOCATION}."],
                "values": {
                    "QUEST_GIVER": ["the mayor", "a merchant", "the temple"],
                    "OBJECTIVE": ["defeat the monster", "retrieve the artifact"],
                    "LOCATION": ["the forest", "the ruins", "the dungeon"]
                }
            }

    def _generate_npc_quest_giver(self, culture: str = "human") -> Dict[str, Any]:
        """Generate an NPC to serve as quest giver."""
        if self.npc_generator:
            npc = self.npc_generator.generate_npc(
                race=culture,
                class_name=random.choice(["commoner", "noble", "acolyte", "sage"]),
                level=random.randint(1, 5)
            )
            return npc
        return {
            "name": f"{random.choice(['Old', 'Young', 'Wise', 'Grizzled'])} {random.choice(['Thomas', 'Maria', 'Gareth', 'Elena'])}",
            "race": culture,
            "occupation": random.choice(["merchant", "noble", "priest", "wizard"])
        }

    def _calculate_reward(self, party_level: int, complexity: str) -> QuestReward:
        """Calculate appropriate reward based on party level and complexity."""
        complexity_data = self.COMPLEXITY_LEVELS.get(complexity, self.COMPLEXITY_LEVELS["moderate"])
        base_xp = complexity_data["xp"]

        # Scale reward by party level
        level_multiplier = 1 + (party_level - 1) * 0.2
        total_xp = int(base_xp * level_multiplier)

        # Gold reward (DMG guidelines: ~50gp per level for moderate quest)
        gold_per_level = {"simple": 25, "moderate": 50, "complex": 100, "epic": 250}
        base_gold = gold_per_level.get(complexity, 50)
        total_gold = int(base_gold * party_level * level_multiplier)

        reward_types = [
            {"type": "gold", "amount": total_gold, "description": f"{total_gold} gold pieces"},
            {"type": "magic_item", "amount": 1, "description": f"A magic item appropriate for level {party_level}"},
            {"type": "land", "amount": 1, "description": "A small parcel of land with a cottage"},
            {"type": "title", "amount": 1, "description": "A noble title and associated privileges"},
            {"type": "boon", "amount": 1, "description": "A powerful boon from a deity or patron"},
            {"type": "information", "amount": 1, "description": "Critical information about the main campaign plot"}
        ]

        # Higher complexity = chance for better rewards
        if complexity in ["complex", "epic"] and random.random() > 0.5:
            reward = random.choice(reward_types[1:])
            reward["amount"] = total_gold // 2  # Half gold if special reward
            return reward

        return reward_types[0]  # Default to gold

    def generate_quest(
        self,
        quest_type: Optional[str] = None,
        complexity: str = "moderate",
        party_level: int = 3,
        party_size: int = 4,
        include_npcs: bool = True,
        include_complications: bool = True,
        num_complications: int = 2,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete quest.

        Args:
            quest_type: Type of quest (rescue, hunt, retrieve, etc.)
            complexity: Quest complexity (simple, moderate, complex, epic)
            party_level: Average party level
            party_size: Number of party members
            include_npcs: Whether to generate NPC details
            include_complications: Whether to add complications
            num_complications: Number of complications to add
            seed: Optional random seed

        Returns:
            Complete quest dict with hooks, objectives, rewards, and complications
        """
        if seed is not None:
            random.seed(seed)

        # Select quest type
        if quest_type is None or quest_type not in self.QUEST_TYPES:
            quest_type = random.choice(list(self.QUEST_TYPES.keys()))

        quest_data = self.QUEST_TYPES[quest_type]
        complexity_info = self.COMPLEXITY_LEVELS.get(complexity, self.COMPLEXITY_LEVELS["moderate"])

        # Generate quest hook using SentenceGenerator if available
        hook_text = self._generate_quest_hook(quest_type)

        # Generate quest giver NPC
        quest_giver = None
        if include_npcs and self.npc_generator:
            quest_giver = self._generate_npc_quest_giver()

        # Calculate rewards
        reward = self._calculate_reward(party_level, complexity)

        # Select complications
        complications = []
        if include_complications:
            num_comp = min(num_complications, len(self.COMPLICATIONS))
            complications = random.sample(self.COMPLICATIONS, num_comp)

        # Generate twist
        twist = self._generate_twist()

        # Build quest structure
        quest = {
            "_meta": {
                "schemaVersion": "1.0.0",
                "createdAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "generator": "quest_builder v1.0"
            },
            "identity": {
                "name": self._generate_quest_name(quest_type),
                "type": quest_type,
                "complexity": complexity,
                "recommended_level": party_level,
                "recommended_party_size": party_size
            },
            "hook": {
                "text": hook_text,
                "quest_giver": quest_giver,
                "location": random.choice(self.quest_hooks.get("values", {}).get("LOCATION", ["the unknown location"]))
            },
            "objectives": {
                "primary": random.choice(quest_data["objectives"]),
                "secondary": self._generate_secondary_objectives(quest_type),
                "skill_checks": self._generate_skill_checks(quest_data["skill_checks"], party_level)
            },
            "enemies": {
                "types": quest_data["enemies"],
                "encounter_difficulty": complexity_info["difficulty"],
                "estimated_xp": complexity_info["xp"]
            },
            "rewards": {
                "primary": reward,
                "experience": complexity_info["xp"] // party_size,
                "reputation": self._generate_reputation_reward(quest_type)
            },
            "complications": complications,
            "twist": twist,
            "dm_notes": self._generate_dm_notes(quest_type, complexity)
        }

        return quest

    def _generate_quest_hook(self, quest_type: str) -> str:
        """Generate quest hook text using templates."""
        if not self.quest_hooks:
            return f"A {quest_type} quest awaits the brave adventurers."

        if SentenceGenerator and self.quest_hooks:
            # Use SentenceGenerator for template expansion
            template = random.choice(self.quest_hooks["templates"])
            gen = SentenceGenerator(template)

            # Set values from quest_hooks data - only for placeholders that exist
            values = self.quest_hooks.get("values", {})
            for key, options in values.items():
                if options and gen.has_placeholder(key):
                    gen.set_values(key, options)

            try:
                return gen.generate()
            except ValueError as e:
                logger.debug(f"Quest hook generation error: {e}")
                # Fallback if template has issues
                pass

        # Fallback: simple template
        quest_data = self.QUEST_TYPES.get(quest_type, {})
        objective = random.choice(quest_data.get("objectives", ["complete the quest"]))
        location = random.choice(["the ancient ruins", "the dark forest", "the distant mountains"])
        return f"A mysterious stranger speaks of {objective} in {location}. Will you answer the call?"

    def _generate_quest_name(self, quest_type: str) -> str:
        """Generate a flavorful quest name."""
        name_templates = {
            "rescue": [
                "The {adjective} Rescue", "Escape from {location}", "Saving the {target}"
            ],
            "hunt": [
                "The {adjective} Hunt", "Tracking the {beast}", "The {location} Stalker"
            ],
            "retrieve": [
                "The {artifact} Quest", "Recovery at {location}", "The Lost {item}"
            ],
            "escort": [
                "Journey to {location}", "The {cargo} Escort", "Through {terrain}"
            ],
            "investigate": [
                "Mystery of {location}", "The {adjective} Conspiracy", "Shadows over {place}"
            ],
            "defend": [
                "Defense of {location}", "The {adjective} Siege", "Last Stand at {place}"
            ],
            "assassinate": [
                "The {adjective} Contract", "Silent Shadow", "Death of {target}"
            ],
            "diplomacy": [
                "The {adjective} Accord", "Peace at {location}", "The {event} Negotiations"
            ]
        }

        templates = name_templates.get(quest_type, ["The {adjective} Quest"])
        template = random.choice(templates)

        replacements = {
            "adjective": random.choice(["Forgotten", "Hidden", "Cursed", "Ancient", "Mysterious", "Dark"]),
            "location": random.choice(["Shadowdale", "the Deepwood", "Ironhold", "the Wastes"]),
            "target": random.choice(["Captives", "Prisoners", "Lost Souls", "Kidnapped Noble"]),
            "beast": random.choice(["Beast", "Monster", "Menace", "Predator"]),
            "artifact": random.choice(["Artifact", "Relic", "Tome", "Orb"]),
            "item": random.choice(["Heirloom", "Weapon", "Crown", "Amulet"]),
            "cargo": random.choice(["Merchant", "Diplomat", "Refugees"]),
            "terrain": random.choice(["Darkness", "Storms", "Wilderness"]),
            "place": random.choice(["the City", "the Valley", "the Keep"]),
            "event": random.choice(["Harvest", "Midwinter", "Coronation"]),
            "target": random.choice(["the Tyrant", "the Crime Lord", "the Traitor"])
        }

        name = template
        for key, value in replacements.items():
            name = name.replace(f"{{{key}}}", value)

        return name

    def _generate_secondary_objectives(self, quest_type: str) -> List[str]:
        """Generate optional secondary objectives."""
        secondary_options = {
            "rescue": [
                "Gather intelligence on enemy plans",
                "Recover stolen goods from the captors",
                "Eliminate the enemy leader"
            ],
            "hunt": [
                "Collect proof of the kill",
                "Gather rare components from the beast",
                "Ensure no trace of the monster remains"
            ],
            "retrieve": [
                "Document any traps or guardians",
                "Recover any additional artifacts found",
                "Map the location for future expeditions"
            ],
            "escort": [
                "Keep the cargo's true nature secret",
                "Arrive before the deadline",
                "Avoid any combat that might endanger the escort"
            ],
            "investigate": [
                "Identify all conspirators",
                "Gather physical evidence",
                "Protect key witnesses"
            ],
            "defend": [
                "Minimize civilian casualties",
                "Preserve key structures",
                "Capture enemy leaders for interrogation"
            ],
            "assassinate": [
                "Make it look like an accident",
                "Retrieve incriminating documents from the target",
                "Frame a rival for the deed"
            ],
            "diplomacy": [
                "Secure favorable trade terms",
                "Arrange a marriage alliance",
                "Gain military support for future conflicts"
            ]
        }

        options = secondary_options.get(quest_type, ["Complete the mission successfully"])
        num_secondary = random.randint(1, 2)
        return random.sample(options, min(num_secondary, len(options)))

    def _generate_skill_checks(
        self,
        primary_skills: List[str],
        party_level: int
    ) -> List[Dict[str, Any]]:
        """Generate skill check DCs based on party level."""
        # Base DC by party level (DMG guidelines)
        level_dc = {
            1: 10, 2: 11, 3: 12, 4: 13, 5: 14,
            6: 15, 7: 16, 8: 17, 9: 18, 10: 19,
            11: 20, 12: 21, 13: 22, 14: 23, 15: 24,
            16: 25, 17: 26, 18: 27, 19: 28, 20: 29
        }

        base_dc = level_dc.get(min(party_level, 20), 15)

        checks = []
        for skill in primary_skills[:3]:  # Max 3 skill checks
            checks.append({
                "skill": skill,
                "dc": base_dc + random.randint(-2, 2),
                "consequence": f"Failure means {random.choice(['delay', 'additional encounter', 'resource loss'])}"
            })

        return checks

    def _generate_reputation_reward(self, quest_type: str) -> str:
        """Generate reputation-based reward description."""
        reputation_rewards = {
            "rescue": "Gratitude of the rescued and their allies",
            "hunt": "Renown as a monster slayer",
            "retrieve": "Trust of scholars and collectors",
            "escort": "Reputation as reliable protectors",
            "investigate": "Known as solvers of mysteries",
            "defend": "Heroes of the defended location",
            "assassinate": "Feared reputation in certain circles",
            "diplomacy": "Respected as skilled negotiators"
        }
        return reputation_rewards.get(quest_type, "Respect among adventurers")

    def _generate_twist(self) -> str:
        """Generate a plot twist for the quest."""
        template = random.choice(self.TWISTS)
        replacements = {
            "QUEST_GIVER": random.choice(["quest giver", "patron", "employer"]),
            "THREAT": random.choice(["apparent threat", "monster", "villain"]),
            "OBJECTIVE": random.choice(["quest objective", "artifact", "goal"]),
            "LOCATION": random.choice(["quest location", "dungeon", "ruins"]),
            "NPC": random.choice(["key NPC", "ally", "guide"]),
            "TRUE_IDENTITY": random.choice(self.TRUE_IDENTITIES)
        }

        twist = template
        for key, value in replacements.items():
            twist = twist.replace(f"{{{key}}}", value)

        return twist

    def _generate_dm_notes(self, quest_type: str, complexity: str) -> str:
        """Generate DM guidance notes."""
        notes = [
            f"This {complexity} {quest_type} quest is designed for a party of 4-5 adventurers.",
            "Adjust enemy numbers based on actual party size and resources.",
            "Consider the party's backstory when revealing the twist.",
            "Have backup encounters ready if the party finishes early."
        ]
        return "\n".join(notes)

    def generate_quest_chain(
        self,
        num_quests: int = 3,
        starting_complexity: str = "simple",
        party_level: int = 1,
        seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a chain of connected quests that scale in difficulty.

        Args:
            num_quests: Number of quests in the chain
            starting_complexity: Starting quest complexity
            party_level: Starting party level
            seed: Optional random seed

        Returns:
            List of quest dicts forming a connected chain
        """
        if seed is not None:
            random.seed(seed)

        complexity_order = ["simple", "moderate", "complex", "epic"]
        start_idx = complexity_order.index(starting_complexity)

        quest_chain = []
        connecting_thread = self._generate_campaign_thread()

        for i in range(num_quests):
            # Scale complexity
            complexity_idx = min(start_idx + i, len(complexity_order) - 1)
            complexity = complexity_order[complexity_idx]

            # Scale party level (assume ~1 level per quest)
            current_level = party_level + i

            quest = self.generate_quest(
                complexity=complexity,
                party_level=current_level,
                include_complications=(i > 0)  # No complications in first quest
            )

            # Add campaign thread connection
            if i > 0:
                quest["connection_to_previous"] = connecting_thread[i - 1] if i - 1 < len(connecting_thread) else "Continuation of the previous quest"

            quest_chain.append(quest)

        return quest_chain

    def _generate_campaign_thread(self) -> List[str]:
        """Generate connecting threads for a quest chain."""
        threads = [
            "Clues from this quest point to a larger conspiracy.",
            "The defeated enemy was working for a greater power.",
            "A mysterious figure observes the party's progress.",
            "Ancient prophecies begin to align with recent events.",
            "The true mastermind reveals themselves."
        ]
        return threads

    def export_to_json(self, quest: Dict[str, Any], filepath: str) -> None:
        """
        Export quest to JSON file.

        Args:
            quest: Quest dict to export
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump(quest, f, indent=2)
        logger.info(f"Quest exported to {filepath}")

    def export_quest_chain_to_json(self, quest_chain: List[Dict[str, Any]], filepath: str) -> None:
        """
        Export quest chain to JSON file.

        Args:
            quest_chain: List of quest dicts
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump({"quest_chain": quest_chain, "total_quests": len(quest_chain)}, f, indent=2)
        logger.info(f"Quest chain exported to {filepath}")


def main():
    """CLI for the quest builder."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DnD Quest Builder v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quest_builder.py -t rescue -c moderate -l 5
  python quest_builder.py --type hunt --complexity complex --party-level 8
  python quest_builder.py --chain 3 --starting simple -l 3
  python quest_builder.py -t retrieve -o quest.json --no-npcs
        """
    )

    parser.add_argument("-t", "--type", dest="quest_type",
                        choices=["rescue", "hunt", "retrieve", "escort", "investigate",
                                 "defend", "assassinate", "diplomacy", "random"],
                        help="Type of quest to generate")
    parser.add_argument("-c", "--complexity", default="moderate",
                        choices=["simple", "moderate", "complex", "epic"],
                        help="Quest complexity level")
    parser.add_argument("-l", "--party-level", type=int, default=3,
                        help="Average party level")
    parser.add_argument("-s", "--party-size", type=int, default=4,
                        help="Number of party members")
    parser.add_argument("--chain", type=int, metavar="NUM",
                        help="Generate a chain of NUM connected quests")
    parser.add_argument("--starting", default="simple",
                        choices=["simple", "moderate", "complex", "epic"],
                        help="Starting complexity for quest chains")
    parser.add_argument("-o", "--output", help="Output file path (JSON)")
    parser.add_argument("--no-npcs", action="store_true",
                        help="Don't generate detailed NPCs")
    parser.add_argument("--no-complications", action="store_true",
                        help="Don't add quest complications")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output with all details")

    args = parser.parse_args()

    # Determine quest type
    quest_type = None if args.quest_type == "random" else args.quest_type

    builder = QuestBuilder(seed=args.seed)

    if args.chain:
        # Generate quest chain
        chain = builder.generate_quest_chain(
            num_quests=args.chain,
            starting_complexity=args.starting,
            party_level=args.party_level
        )

        if args.output:
            builder.export_quest_chain_to_json(chain, args.output)
        else:
            print(f"=== Quest Chain ({len(chain)} quests) ===\n")
            for i, quest in enumerate(chain, 1):
                print(f"\n{'='*50}")
                print(f"Quest {i}: {quest['identity']['name']}")
                print(f"{'='*50}")
                print(f"Type: {quest['identity']['type']} | Complexity: {quest['identity']['complexity']}")
                print(f"Recommended Level: {quest['identity']['recommended_level']}")
                print(f"\nHook: {quest['hook']['text']}")
                print(f"\nPrimary Objective: {quest['objectives']['primary']}")
                if quest['objectives'].get('secondary'):
                    print(f"Secondary: {', '.join(quest['objectives']['secondary'])}")
                print(f"\nReward: {quest['rewards']['primary']['description']}")
                if quest.get('complications'):
                    print(f"Complications: {[c['name'] for c in quest['complications']]}")
                if i < len(chain) and quest.get('connection_to_previous'):
                    print(f"\n📜 Connection: {quest['connection_to_previous']}")
    else:
        # Generate single quest
        quest = builder.generate_quest(
            quest_type=quest_type,
            complexity=args.complexity,
            party_level=args.party_level,
            party_size=args.party_size,
            include_npcs=not args.no_npcs,
            include_complications=not args.no_complications
        )

        if args.output:
            builder.export_to_json(quest, args.output)
        else:
            print(f"=== {quest['identity']['name']} ===")
            print(f"Type: {quest['identity']['type'].capitalize()} | Complexity: {quest['identity']['complexity']}")
            print(f"Recommended: Level {quest['identity']['recommended_level']}, Party of {quest['identity']['recommended_party_size']}")

            print(f"\n📜 Quest Hook:")
            print(f"   {quest['hook']['text']}")

            if quest['hook'].get('quest_giver'):
                qg = quest['hook']['quest_giver']
                print(f"\n👤 Quest Giver: {qg.get('identity', {}).get('name', 'Unknown')}")
                if args.verbose:
                    print(f"   Race: {qg['identity'].get('race', 'Unknown')}")
                    print(f"   Class: {qg['identity'].get('class', 'Commoner')}")

            print(f"\n🎯 Objectives:")
            print(f"   Primary: {quest['objectives']['primary']}")
            if quest['objectives'].get('secondary'):
                for sec in quest['objectives']['secondary']:
                    print(f"   • {sec}")

            print(f"\n⚔️ Enemies:")
            print(f"   Types: {', '.join(quest['enemies']['types'][:3])}")
            print(f"   Difficulty: {quest['enemies']['encounter_difficulty']}")
            print(f"   Estimated XP: {quest['enemies']['estimated_xp']}")

            print(f"\n💰 Rewards:")
            print(f"   {quest['rewards']['primary']['description']}")
            print(f"   XP per character: {quest['rewards']['experience']}")
            print(f"   Reputation: {quest['rewards']['reputation']}")

            if quest.get('complications'):
                print(f"\n⚠️ Complications:")
                for comp in quest['complications']:
                    print(f"   • {comp['name']} (DC {comp['dc']}): {comp['description']}")

            print(f"\n🔄 Plot Twist:")
            print(f"   {quest['twist']}")

            if args.verbose:
                print(f"\n📝 DM Notes:")
                print(f"   {quest['dm_notes']}")
                print(f"\n🎲 Skill Checks:")
                for check in quest['objectives'].get('skill_checks', []):
                    print(f"   • {check['skill']} DC {check['dc']}: {check['consequence']}")


if __name__ == "__main__":
    main()
