#!/usr/bin/env python3
"""
DnD Additional GM Tools Collection

Includes:
- Tavern Generator
- Background Generator  
- Magic Item Creator
- Monster Stat Creator
- Spell Creator
- Currency Converter
- Dream/Vision Generator
- Camp Encounter Generator
- Plot Hook Generator
- Treasure Map Generator
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# TAVERN GENERATOR
# =============================================================================

class TavernGenerator:
    """Generate complete taverns and inns."""

    TAVERN_NAMES = [
        "The Sleeping Dragon", "The Rusty Tankard", "The Golden Goblet",
        "The Broken Shield", "The Wandering Bard", "The Silver Unicorn",
        "The Laughing Dwarf", "The Crimson Sail", "The Old Oak",
        "The Mystic Mug", "The Firebreathing Kittens", "The Quiet Stag"
    ]

    PROPRIETORS = [
        {"name": "Old Gareth", "trait": "Gruff but kind-hearted"},
        {"name": "Mistress Elara", "trait": "Elegant former adventurer"},
        {"name": "Borin Ironfist", "trait": "Dwarven ex-mercenary"},
        {"name": "Lily Meadow", "trait": "Cheerful halfling matron"},
        {"name": "Shadow", "trait": "Mysterious tiefling with secrets"}
    ]

    ATMOSPHERES = [
        "Warm and welcoming, with a roaring fireplace",
        "Rowdy and loud, filled with merchants and sailors",
        "Quiet and refined, catering to nobility",
        "Mysterious, with shadowy corners and whispered conversations",
        "Festive, with music and dancing nightly"
    ]

    SPECIAL_FEATURES = [
        "Live entertainment every night",
        "Famous for a particular dish",
        "Has a secret basement gambling den",
        "Built around an ancient tree",
        "Haunted by friendly ghosts",
        "Has hot springs in the baths",
        "Offers exotic beverages from distant lands"
    ]

    MENU_ITEMS = {
        "food": [
            ("Roast Chicken", 5), ("Beef Stew", 4), ("Fish and Chips", 6),
            ("Venison Pie", 8), ("Vegetable Soup", 3), ("Dragon Ribs", 12)
        ],
        "drink": [
            ("Ale", 2), ("Wine", 4), ("Mead", 3), ("Whiskey", 5),
            ("Exotic Cocktail", 8), ("Dwarven Stout", 4)
        ]
    }

    PATRONS = [
        "Traveling merchant sharing news",
        "Off-duty guard looking for company",
        "Mysterious stranger in the corner",
        "Local bard seeking new material",
        "Adventurer recruiting for a quest",
        "Scholar researching local history",
        "Thief casing the place"
    ]

    def generate_tavern(self, size: str = "medium") -> Dict[str, Any]:
        """Generate a complete tavern."""
        return {
            "name": random.choice(self.TAVERN_NAMES),
            "proprietor": random.choice(self.PROPRIETORS),
            "atmosphere": random.choice(self.ATMOSPHERES),
            "size": size,
            "rooms": self._generate_rooms(size),
            "special_features": random.sample(self.SPECIAL_FEATURES, random.randint(1, 3)),
            "menu": self.MENU_ITEMS,
            "current_patrons": random.sample(self.PATRONS, random.randint(2, 5)),
            "rumors": self._generate_rumors()
        }

    def _generate_rooms(self, size: str) -> Dict[str, int]:
        """Generate room counts."""
        bases = {"small": 5, "medium": 12, "large": 25}
        base = bases.get(size, 12)
        return {
            "private_rooms": base // 3,
            "common_beds": base // 2,
            "suites": max(1, base // 10)
        }

    def _generate_rumors(self) -> List[str]:
        """Generate tavern rumors."""
        rumors = [
            "A dragon was spotted in the northern mountains",
            "The local mine has struck something strange",
            "A mysterious stranger arrived last night",
            "The lord's daughter has gone missing",
            "War is coming with the neighboring kingdom"
        ]
        return random.sample(rumors, 3)


# =============================================================================
# BACKGROUND GENERATOR
# =============================================================================

class BackgroundGenerator:
    """Generate character backstories."""

    ORIGINS = [
        "humble village", "noble estate", "street orphan", "military family",
        "merchant house", "religious order", "criminal underworld", "isolated monastery"
    ]

    INCITING_EVENTS = [
        "family was killed", "discovered a secret", "was betrayed",
        "received a mysterious letter", "witnessed a crime", "found an artifact",
        "was cursed", "fulfilled a prophecy", "lost everything"
    ]

    MOTIVATIONS = [
        "seek revenge", "find family", "gain power", "protect others",
        "discover truth", "break a curse", "restore honor", "find belonging"
    ]

    BONDS = [
        "a sibling who doesn't know the truth",
        "a mentor who believes in them",
        "a debt that must be repaid",
        "a promise made to a dying friend",
        "a family heirloom",
        "a childhood sweetheart"
    ]

    FLAWS = [
        "trusts too easily", "holds grudges forever", "addicted to danger",
        "lies compulsively", "greedy beyond reason", "cowardly when it matters",
        "arrogant about abilities", "haunted by nightmares"
    ]

    SECRETS = [
        "committed a crime they haven't paid for",
        "is the child of a notorious villain",
        "has a bounty on their head",
        "possesses forbidden knowledge",
        "is not who they claim to be"
    ]

    def generate_background(self, char_class: str = "") -> Dict[str, Any]:
        """Generate a complete character background."""
        return {
            "origin": f"Grew up in a {random.choice(self.ORIGINS)}",
            "inciting_event": f"Their life changed when {random.choice(self.INCITING_EVENTS)}",
            "motivation": f"Now they seek to {random.choice(self.MOTIVATIONS)}",
            "bond": f"They are connected to {random.choice(self.BONDS)}",
            "flaw": f"Their weakness is that they {random.choice(self.FLAWS)}",
            "secret": f"Unknown to others, {random.choice(self.SECRETS)}",
            "class_hook": self._generate_class_hook(char_class)
        }

    def _generate_class_hook(self, char_class: str) -> str:
        """Generate class-specific background element."""
        hooks = {
            "fighter": "Trained in a specific military unit or style",
            "wizard": "Apprenticed to a specific master or school",
            "rogue": "Member of a thieves' guild or criminal organization",
            "cleric": "Devoted to a specific deity or cause",
            "barbarian": "From a specific tribe with unique traditions",
            "paladin": "Sworn to a specific oath with known tenets",
        }
        return hooks.get(char_class.lower(), "Has a unique connection to their abilities")


# =============================================================================
# MAGIC ITEM CREATOR
# =============================================================================

class MagicItemCreator:
    """Create custom magic items."""

    PREFIXES = [
        "Ancient", "Cursed", "Blessed", "Enchanted", "Eternal",
        "Forgotten", "Glowing", "Hidden", "Infernal", "Mystic"
    ]

    SUFFIXES = [
        "of Power", "of Protection", "of Shadows", "of Light",
        "of the Phoenix", "of the Void", "of Ages", "of Destiny"
    ]

    ITEM_TYPES = ["weapon", "armor", "ring", "amulet", "staff", "wand", "cloak", "boots"]

    PROPERTIES = [
        "+1 bonus to attack and damage",
        "Resistance to a damage type",
        "Advantage on specific skill checks",
        "Can cast a spell once per day",
        "Glow when danger is near",
        "Telepathic communication with wielder",
        "Extra damage to specific creature type",
        "Can store spells/abilities"
    ]

    CURSES = [
        "Wielder cannot remove item without Remove Curse",
        "Item whispers dark suggestions",
        "Wielder is tracked by a specific creature",
        "Item drains hit points on critical hits",
        "Wielder cannot gain benefits from resting"
    ]

    def create_item(self, rarity: str = "uncommon", cursed: bool = False) -> Dict[str, Any]:
        """Create a custom magic item."""
        item_type = random.choice(self.ITEM_TYPES)
        name = f"{random.choice(self.PREFIXES)} {item_type.title()} {random.choice(self.SUFFIXES)}"
        
        properties = random.sample(self.PROPERTIES, random.randint(1, 3))
        
        item = {
            "name": name,
            "type": item_type,
            "rarity": rarity,
            "properties": properties,
            "attunement": random.choice([True, False]),
            "description": self._generate_description(item_type, properties)
        }
        
        if cursed:
            item["cursed"] = True
            item["curse"] = random.choice(self.CURSES)
        
        return item

    def _generate_description(self, item_type: str, properties: List[str]) -> str:
        """Generate flavor description."""
        descriptions = {
            "weapon": "This weapon hums with arcane energy.",
            "armor": "Ancient runes glow faintly along the surface.",
            "ring": "The band is inscribed with barely visible script.",
            "amulet": "A faint warmth emanates from the gemstone.",
            "staff": "Crackles of energy dance along its length.",
            "wand": "The wood feels ancient yet perfectly preserved.",
            "cloak": "The fabric seems to shift in peripheral vision.",
            "boots": "Footsteps make no sound when wearing these."
        }
        return descriptions.get(item_type, "This item radiates magical energy.")


# =============================================================================
# MONSTER STAT CREATOR
# =============================================================================

class MonsterStatCreator:
    """Create custom monster stat blocks."""

    SIZE_HP = {
        "tiny": (1, 6),
        "small": (7, 25),
        "medium": (26, 75),
        "large": (76, 150),
        "huge": (151, 300),
        "gargantuan": (301, 500)
    }

    def create_monster(
        self,
        name: str = "",
        cr: float = 1,
        size: str = "medium",
        monster_type: str = "humanoid"
    ) -> Dict[str, Any]:
        """Create a custom monster stat block."""
        if not name:
            name = self._generate_monster_name(monster_type)
        
        hp_range = self.SIZE_HP.get(size, (26, 75))
        hp = random.randint(hp_range[0], hp_range[1])
        
        ac = 10 + random.randint(0, 5) + (cr // 2)
        
        return {
            "name": name,
            "size": size,
            "type": monster_type,
            "alignment": self._generate_alignment(),
            "ac": ac,
            "hp": hp,
            "speed": self._generate_speed(size),
            "abilities": self._generate_abilities(cr),
            "traits": self._generate_traits(cr),
            "actions": self._generate_actions(cr, size),
            "cr": cr
        }

    def _generate_monster_name(self, monster_type: str) -> str:
        """Generate monster name."""
        prefixes = {"humanoid": ["Gor", "Mal", "Thar"], "undead": ["Mor", "Vex", "Zar"],
                   "dragon": ["Ign", "Cryo", "Tempest"], "beast": ["Razor", "Shadow", "Thunder"]}
        suffixes = {"humanoid": ["nak", "gar", "th"], "undead": ["ion", "us", "oth"],
                   "dragon": ["rax", "ithos", "aryx"], "beast": ["claw", "fang", "hide"]}
        
        mtype = monster_type.lower()
        prefix = random.choice(prefixes.get(mtype, ["Mon"]))
        suffix = random.choice(suffixes.get(mtype, ["ster"]))
        return f"{prefix}{suffix}"

    def _generate_alignment(self) -> str:
        return random.choice(["neutral evil", "chaotic neutral", "lawful neutral", "unaligned"])

    def _generate_speed(self, size: str) -> int:
        bases = {"tiny": 20, "small": 25, "medium": 30, "large": 30, "huge": 40, "gargantuan": 40}
        return bases.get(size, 30)

    def _generate_abilities(self, cr: float) -> Dict[str, int]:
        base = 10 + int(cr)
        return {
            "STR": base + random.randint(-2, 4),
            "DEX": base + random.randint(-2, 4),
            "CON": base + random.randint(0, 4),
            "INT": base + random.randint(-4, 2),
            "WIS": base + random.randint(-2, 2),
            "CHA": base + random.randint(-4, 2)
        }

    def _generate_traits(self, cr: float) -> List[str]:
        traits = ["Pack Tactics", "Keen Senses", "Natural Armor", "Regeneration",
                 "Magic Resistance", "Legendary Resistance", "Innate Spellcasting"]
        num_traits = min(len(traits), 1 + int(cr / 3))
        return random.sample(traits, num_traits)

    def _generate_actions(self, cr: float, size: str) -> List[Dict[str, Any]]:
        actions = []
        damage = max(1, int(cr * 2))
        
        actions.append({
            "name": "Multiattack" if cr >= 2 else "Attack",
            "description": f"Deals {damage}d6 + {max(1, cr//2)} damage"
        })
        
        if cr >= 5:
            actions.append({
                "name": "Special Attack",
                "description": "Recharge 5-6. Deals additional effects"
            })
        
        return actions


# =============================================================================
# SPELL CREATOR
# =============================================================================

class SpellCreator:
    """Create custom spells."""

    SCHOOLS = ["abjuration", "conjuration", "divination", "enchantment",
               "evocation", "illusion", "necromancy", "transmutation"]

    COMPONENTS = ["V", "S", "M"]

    def create_spell(
        self,
        level: int = 1,
        school: str = "",
        classes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a custom spell."""
        if not school:
            school = random.choice(self.SCHOOLS)
        
        name = self._generate_spell_name(school)
        
        return {
            "name": name,
            "level": level,
            "school": school,
            "casting_time": self._generate_casting_time(),
            "range": self._generate_range(),
            "components": random.sample(self.COMPONENTS, random.randint(1, 3)),
            "duration": self._generate_duration(),
            "description": self._generate_spell_description(school, level),
            "at_higher_levels": self._generate_higher_level(level),
            "classes": classes or self._assign_classes()
        }

    def _generate_spell_name(self, school: str) -> str:
        prefixes = {"evocation": ["Fire", "Lightning", "Ice"], "necromancy": ["Death", "Bone", "Soul"],
                   "illusion": ["Phantom", "Shadow", "Mirror"], "transmutation": ["Transform", "Shift", "Change"]}
        suffixes = ["Bolt", "Strike", "Ward", "Blast", "Touch", "Aura", "Shield"]
        
        prefix = random.choice(prefixes.get(school, ["Arcane"]))
        return f"{prefix} {random.choice(suffixes)}"

    def _generate_casting_time(self) -> str:
        return random.choice(["1 action", "1 bonus action", "1 reaction", "1 minute", "1 hour"])

    def _generate_range(self) -> str:
        return random.choice(["Self", "Touch", "30 feet", "60 feet", "120 feet", "300 feet"])

    def _generate_duration(self) -> str:
        return random.choice(["Instantaneous", "1 round", "1 minute", "10 minutes", "1 hour", "Concentration"])

    def _generate_spell_description(self, school: str, level: int) -> str:
        descriptions = {
            "evocation": f"Deals {level}d6 damage in an area",
            "necromancy": "Affects life force or creates undead",
            "illusion": "Creates false sensory effects",
            "transmutation": "Changes properties of target",
            "abjuration": "Provides protection or wards",
            "conjuration": "Summons creatures or objects",
            "divination": "Reveals information",
            "enchantment": "Affects minds or behavior"
        }
        return descriptions.get(school, "Produces magical effect")

    def _generate_higher_level(self, level: int) -> str:
        return f"When cast using a spell slot of {level + 1} level or higher, effect increases"

    def _assign_classes(self) -> List[str]:
        all_classes = ["wizard", "sorcerer", "cleric", "druid", "bard", "warlock", "paladin", "ranger"]
        return random.sample(all_classes, random.randint(1, 4))


# =============================================================================
# CURRENCY CONVERTER
# =============================================================================

class CurrencyConverter:
    """Convert between currencies and track wealth."""

    # Standard DnD exchange rates (relative to gp)
    RATES = {
        "pp": 10,  # Platinum
        "gp": 1,   # Gold
        "ep": 0.5, # Electrum
        "sp": 0.1, # Silver
        "cp": 0.01 # Copper
    }

    def __init__(self, base_currency: str = "gp"):
        self.base_currency = base_currency

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies."""
        gp_value = amount * self.RATES.get(from_currency, 1)
        return gp_value / self.RATES.get(to_currency, 1)

    def to_standard(self, coins: Dict[str, int]) -> Dict[str, Any]:
        """Convert mixed coins to standard format."""
        total_gp = sum(amount * self.RATES.get(coin, 0) for coin, amount in coins.items())
        
        # Break down into standard denominations
        remaining = total_gp
        result = {}
        
        for coin in ["pp", "gp", "sp", "cp"]:
            rate = self.RATES[coin]
            count = int(remaining // rate)
            if count > 0:
                result[coin] = count
                remaining -= count * rate
        
        return {
            "breakdown": result,
            "total_gp": total_gp
        }

    def lifestyle_cost(self, lifestyle: str) -> Dict[str, Any]:
        """Get lifestyle expenses."""
        lifestyles = {
            "wretched": {"cost": 0, "period": "day"},
            "squalid": {"cost": 1, "period": "day", "currency": "sp"},
            "poor": {"cost": 2, "period": "day", "currency": "sp"},
            "modest": {"cost": 1, "period": "day", "currency": "gp"},
            "comfortable": {"cost": 2, "period": "day", "currency": "gp"},
            "wealthy": {"cost": 4, "period": "day", "currency": "gp"},
            "aristocratic": {"cost": 10, "period": "day", "currency": "gp"}
        }
        return lifestyles.get(lifestyle, lifestyles["modest"])


# =============================================================================
# DREAM/VISION GENERATOR
# =============================================================================

class DreamVisionGenerator:
    """Generate prophetic dreams and visions."""

    SYMBOLS = {
        "water": "Emotions, change, the unconscious",
        "fire": "Passion, destruction, transformation",
        "snake": "Betrayal, healing, hidden knowledge",
        "bird": "Freedom, messages, spiritual matters",
        "death": "Endings, transformation, not literal death",
        "falling": "Loss of control, insecurity",
        "teeth": "Anxiety, powerlessness",
        "chase": "Avoiding something important",
        "door": "Opportunities, transitions",
        "mirror": "Self-reflection, hidden aspects"
    }

    SETTINGS = [
        "familiar location twisted",
        "completely alien landscape",
        "childhood memory",
        "future event",
        "another person's perspective"
    ]

    OUTCOMES = [
        "reveals a hidden truth",
        "warns of coming danger",
        "shows a possible future",
        "connects to a past trauma",
        "provides a cryptic clue"
    ]

    def generate_vision(self, purpose: str = "prophecy") -> Dict[str, Any]:
        """Generate a dream or vision."""
        symbols = random.sample(list(self.SYMBOLS.keys()), random.randint(2, 4))
        
        return {
            "setting": random.choice(self.SETTINGS),
            "symbols": {s: self.SYMBOLS[s] for s in symbols},
            "narrative": self._generate_narrative(symbols),
            "purpose": purpose,
            "outcome": random.choice(self.OUTCOMES),
            "clarity": random.choice(["crystal clear", "hazy", "fragmented", "symbolic"])
        }

    def _generate_narrative(self, symbols: List[str]) -> str:
        templates = [
            f"The dreamer sees {{0}} and {{1}}, then awakens.",
            f"In the vision, {{0}} transforms into {{1}}.",
            f"The dreamer is pursued by {{0}} through {{1}}.",
            f"A voice speaks of {{0}} while {{1}} looms."
        ]
        template = random.choice(templates)
        return template.format(*symbols[:2])


# =============================================================================
# CAMP ENCOUNTER GENERATOR
# =============================================================================

class CampEncounterGenerator:
    """Generate camp events and encounters."""

    QUIET_EVENTS = [
        "Peaceful night, full rest",
        "Beautiful starry sky",
        "Distant howling",
        "Someone keeps watch dutifully",
        "Dreams are vivid"
    ]

    MINOR_EVENTS = [
        "Watch notices movement in darkness",
        "Campfire sputters strangely",
        "Animal approaches camp curiously",
        "Weather turns unpleasant",
        "Equipment needs minor repair"
    ]

    MAJOR_EVENTS = [
        "Ambush by nocturnal predators",
        "Mysterious traveler seeks shelter",
        "Magical phenomenon occurs",
        "Camp is discovered by enemies",
        "Supplies are stolen"
    ]

    def generate_camp(self, danger_level: str = "normal") -> Dict[str, Any]:
        """Generate camp encounter."""
        if danger_level == "safe":
            event = random.choice(self.QUIET_EVENTS)
            threat = False
        elif danger_level == "dangerous":
            event = random.choice(self.MAJOR_EVENTS)
            threat = True
        else:
            roll = random.randint(1, 100)
            if roll <= 50:
                event = random.choice(self.QUIET_EVENTS)
                threat = False
            elif roll <= 80:
                event = random.choice(self.MINOR_EVENTS)
                threat = False
            else:
                event = random.choice(self.MAJOR_EVENTS)
                threat = True
        
        return {
            "event": event,
            "threat": threat,
            "rest_quality": "full" if not threat else "interrupted",
            "watch_dc": 10 if not threat else 15
        }


# =============================================================================
# PLOT HOOK GENERATOR
# =============================================================================

class PlotHookGenerator:
    """Generate adventure plot hooks."""

    HOOKS_BY_TYPE = {
        "combat": [
            "A monster terrorizes the countryside",
            "Bandits have been ambushing travelers",
            "A dungeon has been discovered",
            "Mercenaries are recruiting"
        ],
        "social": [
            "A noble seeks discreet investigators",
            "A festival brings unusual visitors",
            "Political tensions are rising",
            "A wedding needs protection"
        ],
        "exploration": [
            "A map to lost treasure surfaces",
            "Unusual phenomena reported",
            "A new route is discovered",
            "Ancient ruins emerge from the earth"
        ],
        "mystery": [
            "People are disappearing",
            "Murders with no explanation",
            "Objects vanish and reappear",
            "Someone is impersonating nobles"
        ]
    }

    def generate_hook(self, hook_type: str = "any") -> Dict[str, Any]:
        """Generate a plot hook."""
        if hook_type == "any":
            hook_type = random.choice(list(self.HOOKS_BY_TYPE.keys()))
        
        hooks = self.HOOKS_BY_TYPE.get(hook_type, self.HOOKS_BY_TYPE["combat"])
        
        return {
            "type": hook_type,
            "hook": random.choice(hooks),
            "quest_giver": self._generate_quest_giver(),
            "reward": self._generate_reward(hook_type)
        }

    def _generate_quest_giver(self) -> str:
        givers = ["noble", "merchant", "priest", "commoner", "official", "child"]
        return f"A desperate {random.choice(givers)}"

    def _generate_reward(self, hook_type: str) -> str:
        rewards = {
            "combat": "Gold and glory",
            "social": "Favor and connections",
            "exploration": "Treasure and discovery",
            "mystery": "Truth and justice"
        }
        return rewards.get(hook_type, "Appropriate reward")


# =============================================================================
# TREASURE MAP GENERATOR
# =============================================================================

class TreasureMapGenerator:
    """Generate treasure maps with clues."""

    LANDMARKS = [
        "the old oak tree", "the standing stones", "the ruined tower",
        "the waterfall", "the cave entrance", "the crossroads",
        "the graveyard", "the bridge", "the mill", "the temple"
    ]

    DIRECTIONS = [
        "Go north until you see",
        "From there, head east toward",
        "Walk until you reach",
        "Journey to",
        "Seek out"
    ]

    CLUES = [
        "Where the shadow falls at noon",
        "Beneath the stone that weeps",
        "In the mouth of the beast",
        "Where two paths become one",
        "Under the watchful eye"
    ]

    def generate_map(self, difficulty: str = "medium") -> Dict[str, Any]:
        """Generate a treasure map."""
        num_clues = {"easy": 2, "medium": 4, "hard": 6}.get(difficulty, 4)
        
        directions = []
        for i in range(num_clues):
            directions.append(f"{random.choice(self.DIRECTIONS)} {random.choice(self.LANDMARKS)}")
        
        final_clue = random.choice(self.CLUES)
        
        return {
            "directions": directions,
            "final_clue": final_clue,
            "treasure_type": self._generate_treasure(),
            "complications": self._generate_complications(difficulty)
        }

    def _generate_treasure(self) -> str:
        treasures = [
            "Gold and gems",
            "Magic item",
            "Ancient artifact",
            "Family heirloom",
            "Forbidden knowledge"
        ]
        return random.choice(treasures)

    def _generate_complications(self, difficulty: str) -> List[str]:
        complications = [
            "The location is guarded",
            "The map is incomplete",
            "Others seek the treasure",
            "The treasure is cursed",
            "The landscape has changed"
        ]
        num_comp = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 1)
        return random.sample(complications, num_comp)


# =============================================================================
# MAIN CLI
# =============================================================================

def main():
    """CLI for additional GM tools."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD Additional GM Tools")
    
    subparsers = parser.add_subparsers(dest="tool", help="Tool to use")
    
    # Tavern
    subparsers.add_parser("tavern", help="Generate a tavern")
    
    # Background
    bg_parser = subparsers.add_parser("background", help="Generate character background")
    bg_parser.add_argument("--class", dest="char_class", help="Character class")
    
    # Magic Item
    item_parser = subparsers.add_parser("magic-item", help="Create magic item")
    item_parser.add_argument("-r", "--rarity", default="uncommon")
    item_parser.add_argument("--cursed", action="store_true")
    
    # Monster
    monster_parser = subparsers.add_parser("monster", help="Create monster")
    monster_parser.add_argument("--cr", type=float, default=1)
    monster_parser.add_argument("--size", default="medium")
    
    # Spell
    spell_parser = subparsers.add_parser("spell", help="Create spell")
    spell_parser.add_argument("-l", "--level", type=int, default=1)
    
    # Dream/Vision
    subparsers.add_parser("dream", help="Generate dream/vision")
    
    # Camp
    camp_parser = subparsers.add_parser("camp", help="Generate camp encounter")
    camp_parser.add_argument("-d", "--danger", default="normal")
    
    # Plot Hook
    hook_parser = subparsers.add_parser("hook", help="Generate plot hook")
    hook_parser.add_argument("-t", "--type", default="any")
    
    # Treasure Map
    map_parser = subparsers.add_parser("map", help="Generate treasure map")
    map_parser.add_argument("-d", "--difficulty", default="medium")
    
    args = parser.parse_args()
    
    if args.tool == "tavern" or not args.tool:
        gen = TavernGenerator()
        tavern = gen.generate_tavern()
        print(f"\n=== {tavern['name']} ===")
        print(f"Proprietor: {tavern['proprietor']['name']} ({tavern['proprietor']['trait']})")
        print(f"Atmosphere: {tavern['atmosphere']}")
        print(f"Features: {', '.join(tavern['special_features'])}")
        print(f"Patrons: {', '.join(tavern['current_patrons'])}")
        print(f"Rumors:")
        for rumor in tavern['rumors']:
            print(f"  • {rumor}")
    
    elif args.tool == "background":
        gen = BackgroundGenerator()
        bg = gen.generate_background(args.char_class or "")
        print(f"\n=== Character Background ===")
        for key, value in bg.items():
            print(f"{key.title()}: {value}")
    
    elif args.tool == "magic-item":
        gen = MagicItemCreator()
        item = gen.create_item(args.rarity, args.cursed)
        print(f"\n=== {item['name']} ===")
        print(f"Type: {item['type']} | Rarity: {item['rarity']}")
        print(f"Attunement: {'Required' if item['attunement'] else 'Not required'}")
        print(f"Properties: {', '.join(item['properties'])}")
        print(f"Description: {item['description']}")
        if item.get('cursed'):
            print(f"⚠️ CURSED: {item['curse']}")
    
    elif args.tool == "monster":
        gen = MonsterStatCreator()
        monster = gen.create_monster(cr=args.cr, size=args.size)
        print(f"\n=== {monster['name']} ===")
        print(f"Size: {monster['size']} | Type: {monster['type']}")
        print(f"AC: {monster['ac']} | HP: {monster['hp']} | CR: {monster['cr']}")
        print(f"Traits: {', '.join(monster['traits'])}")
    
    elif args.tool == "spell":
        gen = SpellCreator()
        spell = gen.create_spell(level=args.level)
        print(f"\n=== {spell['name']} ===")
        print(f"Level: {spell['level']} | School: {spell['school']}")
        print(f"Casting Time: {spell['casting_time']}")
        print(f"Range: {spell['range']} | Duration: {spell['duration']}")
        print(f"Description: {spell['description']}")
    
    elif args.tool == "dream":
        gen = DreamVisionGenerator()
        vision = gen.generate_vision()
        print(f"\n=== Vision/Dream ===")
        print(f"Setting: {vision['setting']}")
        print(f"Symbols:")
        for symbol, meaning in vision['symbols'].items():
            print(f"  • {symbol}: {meaning}")
        print(f"Narrative: {vision['narrative']}")
        print(f"Outcome: {vision['outcome']}")
    
    elif args.tool == "camp":
        gen = CampEncounterGenerator()
        camp = gen.generate_camp(args.danger)
        print(f"\n=== Camp Encounter ===")
        print(f"Event: {camp['event']}")
        print(f"Threat: {'Yes' if camp['threat'] else 'No'}")
        print(f"Rest Quality: {camp['rest_quality']}")
    
    elif args.tool == "hook":
        gen = PlotHookGenerator()
        hook = gen.generate_hook(args.type)
        print(f"\n=== Plot Hook ({hook['type']}) ===")
        print(f"Hook: {hook['hook']}")
        print(f"Quest Giver: {hook['quest_giver']}")
        print(f"Reward: {hook['reward']}")
    
    elif args.tool == "map":
        gen = TreasureMapGenerator()
        map_data = gen.generate_map(args.difficulty)
        print(f"\n=== Treasure Map ({args.difficulty}) ===")
        print("Directions:")
        for direction in map_data['directions']:
            print(f"  • {direction}")
        print(f"\nFinal Clue: {map_data['final_clue']}")
        print(f"Treasure: {map_data['treasure_type']}")
        if map_data['complications']:
            print(f"Complications: {', '.join(map_data['complications'])}")


if __name__ == "__main__":
    main()
