#!/usr/bin/env python3
"""
DnD Loot Generator v2.1

Generate random treasure with rarity-weighted selection.
Supports cursed items, sentient items, item sets, and expanded loot tables.

Features:
- LRU caching for data loading
- Logging support
- Regional treasure tables
"""

import json
import random
import logging
from functools import lru_cache
from typing import List, Dict, Optional, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class LootGenerator:
    """Generate DnD loot with rarity weighting."""

    # Rarity weights (higher = more common)
    RARITY_WEIGHTS = {
        "common": 100,
        "uncommon": 50,
        "rare": 20,
        "very rare": 5,
        "legendary": 1,
        "artifact": 0.1
    }

    # Gold value ranges by rarity
    GOLD_RANGES = {
        "common": (1, 50),
        "uncommon": (50, 250),
        "rare": (250, 1000),
        "very rare": (1000, 5000),
        "legendary": (5000, 25000),
        "artifact": (25000, 100000)
    }

    # Sentient item personalities
    SENTIENT_PERSONALITIES = [
        {"alignment": "lawful good", "purpose": "Protect the innocent", "communication": "Telepathy", "special": "Detect evil"},
        {"alignment": "chaotic evil", "purpose": "Spread chaos", "communication": "Speech", "special": "Dominate wielder"},
        {"alignment": "neutral", "purpose": "Preserve knowledge", "communication": "Empathy", "special": "Know history of objects"},
        {"alignment": "lawful neutral", "purpose": "Maintain order", "communication": "Telepathy", "special": "Detect lies"},
        {"alignment": "chaotic good", "purpose": "Fight tyranny", "communication": "Speech", "special": "Inspire allies"},
    ]

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the loot generator.

        Args:
            data_dir: Directory containing SRD data files
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.items: List[Dict[str, Any]] = []
        self.cursed_items: List[Dict[str, Any]] = []
        self.sentient_items: List[Dict[str, Any]] = []
        self.item_sets: List[Dict[str, Any]] = []
        self.regional_treasure: Dict[str, Any] = {}
        self._load_items()

    @staticmethod
    @lru_cache(maxsize=4)
    def _load_json_data(data_dir: Path, filename: str) -> Dict[str, Any]:
        """
        Load JSON data with LRU caching.
        
        Args:
            data_dir: Directory containing data files
            filename: Name of the JSON file
            
        Returns:
            Dict with loaded data
        """
        filepath = data_dir / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}

    def _load_items(self):
        """Load item data from SRD file."""
        items_data = self._load_json_data(self.data_dir, "srd_items.json")
        regional_data = self._load_json_data(self.data_dir, "regional_treasure.json")
        
        if items_data:
            self.items = items_data.get("items", [])
            self.cursed_items = items_data.get("cursed_items", [])
            self.sentient_items = items_data.get("sentient_items", [])
            self.item_sets = items_data.get("item_sets", [])
            logger.debug(f"Loaded {len(self.items)} items from cache")
        else:
            # Fallback minimal data
            self.items = [
                {"name": "Longsword +1", "type": "weapon", "rarity": "uncommon", "property": "+1 to attack and damage"},
                {"name": "Shield +1", "type": "armor", "rarity": "uncommon", "property": "+1 to AC"},
                {"name": "Potion of Healing", "type": "potion", "rarity": "common", "property": "Restore 2d4+2 HP"},
                {"name": "Ring of Protection", "type": "ring", "rarity": "rare", "property": "+1 to AC and saving throws"},
            ]
            self.cursed_items = []
            self.sentient_items = []
            self.item_sets = []
            logger.warning("Using fallback item data")
        
        if regional_data:
            self.regional_treasure = regional_data.get("regions", {})
            logger.debug(f"Loaded {len(self.regional_treasure)} regional treasure tables")

    def _weighted_choice(self, items: List[Dict[str, Any]], rarity_weights: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
        """Select an item based on rarity weights."""
        if not items:
            return None

        weights = rarity_weights or self.RARITY_WEIGHTS
        weighted_items = []

        for item in items:
            rarity = item.get("rarity", "common").lower()
            weight = weights.get(rarity, 1)
            # Add item multiple times based on weight
            weighted_items.extend([item] * int(weight * 10))

        if not weighted_items:
            return random.choice(items)

        return random.choice(weighted_items)

    def filter_items(self, rarity: Optional[str] = None,
                     item_type: Optional[str] = None,
                     exclude_cursed: bool = True) -> List[Dict[str, Any]]:
        """
        Filter items by criteria.

        Args:
            rarity: Filter by rarity
            item_type: Filter by type (weapon, armor, ring, etc.)
            exclude_cursed: Whether to exclude cursed items

        Returns:
            List of matching items
        """
        filtered = self.items

        if rarity:
            filtered = [i for i in filtered if i.get("rarity", "").lower() == rarity.lower()]

        if item_type:
            filtered = [i for i in filtered if i.get("type", "").lower() == item_type.lower()]

        return filtered

    def generate_magic_item(self, rarity: Optional[str] = None,
                            item_type: Optional[str] = None,
                            allow_cursed: bool = False,
                            allow_sentient: bool = False,
                            seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a single magic item.

        Args:
            rarity: Specific rarity (or random if None)
            item_type: Specific type (or random if None)
            allow_cursed: Whether to allow cursed items
            allow_sentient: Whether to allow sentient items
            seed: Optional random seed

        Returns:
            Item dict with details
        """
        if seed is not None:
            random.seed(seed)

        # Check for sentient item
        if allow_sentient and self.sentient_items and random.random() < 0.05:
            item = random.choice(self.sentient_items)
            return self._create_sentient_item(item)

        # Check for cursed item
        if allow_cursed and self.cursed_items and random.random() < 0.1:
            item = random.choice(self.cursed_items)
            return self._create_cursed_item(item)

        filtered = self.filter_items(rarity=rarity, item_type=item_type)

        if not filtered:
            return self._generate_fallback_item(rarity)

        item = self._weighted_choice(filtered)

        # Calculate gold value
        item_rarity = item.get("rarity", "common").lower()
        gold_range = self.GOLD_RANGES.get(item_rarity, (10, 100))
        gold_value = random.randint(gold_range[0], gold_range[1])

        return {
            "name": item.get("name", "Unknown Item"),
            "type": item.get("type", "wondrous"),
            "rarity": item_rarity,
            "property": item.get("property", "Unknown property"),
            "gold_value": gold_value,
            "description": self._generate_description(item),
            "cursed": False,
            "sentient": False
        }

    def _create_cursed_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create a cursed item entry."""
        item_rarity = item.get("rarity", "rare").lower()
        gold_range = self.GOLD_RANGES.get(item_rarity, (100, 1000))

        return {
            "name": item.get("name", "Cursed Item"),
            "type": item.get("type", "wondrous"),
            "rarity": item_rarity,
            "property": item.get("property", "Unknown cursed property"),
            "gold_value": random.randint(gold_range[0], gold_range[1]),
            "description": f"A sinister aura surrounds this {item_rarity} item.",
            "cursed": True,
            "sentient": False,
            "curse_effect": item.get("property", "Unknown curse")
        }

    def _create_sentient_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sentient item entry."""
        personality = random.choice(self.SENTIENT_PERSONALITIES)
        item_rarity = item.get("rarity", "legendary").lower()
        gold_range = self.GOLD_RANGES.get(item_rarity, (5000, 25000))

        return {
            "name": item.get("name", "Sentient Item"),
            "type": item.get("type", "weapon"),
            "rarity": item_rarity,
            "property": item.get("property", "Sentient"),
            "gold_value": random.randint(gold_range[0], gold_range[1]),
            "description": f"This ancient item pulses with intelligence.",
            "cursed": False,
            "sentient": True,
            "sentience": {
                "intelligence": random.randint(10, 17),
                "wisdom": random.randint(8, 16),
                "charisma": random.randint(10, 18),
                "alignment": personality["alignment"],
                "purpose": personality["purpose"],
                "communication": personality["communication"],
                "special_ability": personality["special"],
                "senses": {
                    "hearing": random.randint(30, 120),
                    "vision": random.randint(30, 120)
                },
                "ego": random.randint(8, 16)
            }
        }

    def _generate_fallback_item(self, rarity: Optional[str] = None) -> Dict[str, Any]:
        """Generate a fallback item if no data available."""
        rarity = rarity or random.choice(list(self.RARITY_WEIGHTS.keys()))
        gold_range = self.GOLD_RANGES.get(rarity, (10, 100))

        return {
            "name": f"Magic Item of {rarity.capitalize()}",
            "type": "wondrous",
            "rarity": rarity,
            "property": "DM's discretion",
            "gold_value": random.randint(gold_range[0], gold_range[1]),
            "description": f"A mysterious item radiating {rarity} magic.",
            "cursed": False,
            "sentient": False
        }

    def _generate_description(self, item: Dict[str, Any]) -> str:
        """Generate a flavor description for an item."""
        descriptions = {
            "weapon": [
                "This weapon hums with arcane energy.",
                "Ancient runes glow faintly along the blade.",
                "The weapon feels lighter than it appears.",
                "A faint aura surrounds this masterwork weapon."
            ],
            "armor": [
                "This armor bears the marks of countless battles.",
                "The metal shimmers with an otherworldly light.",
                "Enchanted protections are woven into the material.",
                "This armor has protected heroes of old."
            ],
            "ring": [
                "The band is inscribed with barely visible script.",
                "A faint warmth emanates from the ring.",
                "The gemstone seems to shift colors in the light.",
                "This ring has passed through many hands."
            ],
            "wand": [
                "Crackles of energy dance along the wand's length.",
                "The wood feels ancient yet perfectly preserved.",
                "The wand resonates with magical potential.",
                "Runes spiral down the length of this artifact."
            ],
            "potion": [
                "The liquid inside glows with inner light.",
                "Bubbles rise against gravity within the vial.",
                "A sweet aroma wafts from the container.",
                "The potion changes color as you watch."
            ],
            "wondrous": [
                "This item defies mundane explanation.",
                "Ancient magic pulses through the object.",
                "The item bears symbols of a forgotten age.",
                "A sense of destiny surrounds this artifact."
            ]
        }

        item_type = item.get("type", "wondrous")
        options = descriptions.get(item_type, descriptions["wondrous"])
        return random.choice(options)

    def check_item_set(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check if collected items form a set.

        Args:
            items: List of item names

        Returns:
            List of matching set bonuses
        """
        item_names = [i.get("name", "") if isinstance(i, dict) else i for i in items]
        matched_sets = []

        for item_set in self.item_sets:
            pieces = item_set.get("pieces", [])
            if all(any(piece.lower() in name.lower() for name in item_names) for piece in pieces):
                matched_sets.append({
                    "set_name": item_set["name"],
                    "bonus": item_set.get("bonus", "Unknown bonus"),
                    "pieces_collected": len(pieces),
                    "pieces_total": len(pieces)
                })

        return matched_sets

    def generate_hoard(self, party_size: int = 4,
                       party_level: int = 5,
                       include_magic_items: int = 2,
                       allow_cursed: bool = False,
                       allow_sentient: bool = False) -> Dict[str, Any]:
        """
        Generate a treasure hoard.

        Args:
            party_size: Number of party members
            party_level: Average party level
            include_magic_items: Number of magic items to include
            allow_cursed: Whether to include cursed items
            allow_sentient: Whether to include sentient items

        Returns:
            Hoard dict with coins, gems, and magic items
        """
        # Calculate base treasure by party level
        base_gold = party_level * party_size * random.randint(50, 100)

        # Add gems and art objects
        gem_count = random.randint(2, 6)
        gem_value = random.randint(10, 100) * party_level
        art_count = random.randint(1, 3)
        art_value = random.randint(50, 250) * party_level

        # Generate magic items with appropriate rarity
        magic_items = []
        for i in range(include_magic_items):
            # Higher level = chance for rarer items
            rarity_roll = random.random()
            if party_level >= 10 and rarity_roll > 0.8:
                rarity = random.choice(["rare", "very rare"])
            elif party_level >= 5 and rarity_roll > 0.6:
                rarity = random.choice(["uncommon", "rare"])
            else:
                rarity = random.choice(["common", "uncommon", "common"])

            item = self.generate_magic_item(
                rarity=rarity,
                allow_cursed=allow_cursed,
                allow_sentient=allow_sentient
            )
            magic_items.append(item)

        # Check for item sets
        set_bonuses = self.check_item_set(magic_items)

        return {
            "gold_pieces": base_gold,
            "gems": {"count": gem_count, "value_each": gem_value, "total_value": gem_count * gem_value},
            "art_objects": {"count": art_count, "value_each": art_value, "total_value": art_count * art_value},
            "magic_items": magic_items,
            "set_bonuses": set_bonuses,
            "total_value": base_gold + (gem_count * gem_value) + (art_count * art_value) + sum(i.get("gold_value", 0) for i in magic_items)
        }

    def generate_treasure_bundle(self, count: int = 5,
                                 rarity: Optional[str] = None,
                                 allow_cursed: bool = False) -> List[Dict[str, Any]]:
        """
        Generate multiple treasure items.

        Args:
            count: Number of items to generate
            rarity: Specific rarity for all items
            allow_cursed: Whether to include cursed items

        Returns:
            List of treasure items
        """
        return [
            self.generate_magic_item(rarity=rarity, allow_cursed=allow_cursed)
            for _ in range(count)
        ]

    def roll_on_table(self, table_type: str = "d100",
                      allow_cursed: bool = False,
                      allow_sentient: bool = False,
                      seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Roll on a standard treasure table.

        Args:
            table_type: Table type (d100, minor, major)
            allow_cursed: Whether to include cursed items
            allow_sentient: Whether to include sentient items
            seed: Optional random seed

        Returns:
            Treasure result
        """
        if seed is not None:
            random.seed(seed)

        if table_type == "d100":
            roll = random.randint(1, 100)
            if roll <= 50:
                return {"type": "currency", "amount": random.randint(10, 100), "currency": "gp"}
            elif roll <= 75:
                return self.generate_magic_item(rarity="common", allow_cursed=allow_cursed, allow_sentient=allow_sentient)
            elif roll <= 90:
                return self.generate_magic_item(rarity="uncommon", allow_cursed=allow_cursed, allow_sentient=allow_sentient)
            elif roll <= 97:
                return self.generate_magic_item(rarity="rare", allow_cursed=allow_cursed, allow_sentient=allow_sentient)
            elif roll <= 99:
                return self.generate_magic_item(rarity="very rare", allow_cursed=allow_cursed, allow_sentient=allow_sentient)
            else:
                return self.generate_magic_item(rarity="legendary", allow_cursed=allow_cursed, allow_sentient=allow_sentient)
        elif table_type == "minor":
            return self.generate_magic_item(
                rarity=random.choice(["common", "uncommon"]),
                allow_cursed=allow_cursed,
                allow_sentient=allow_sentient
            )
        elif table_type == "major":
            return self.generate_magic_item(
                rarity=random.choice(["rare", "very rare", "legendary"]),
                allow_cursed=allow_cursed,
                allow_sentient=allow_sentient
            )
        else:
            return self.generate_magic_item(allow_cursed=allow_cursed, allow_sentient=allow_sentient)

    def identify_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify an item, revealing if it's cursed or sentient.

        Args:
            item: Item dict to identify

        Returns:
            Identified item dict
        """
        identified = item.copy()
        identified["identified"] = True

        if item.get("cursed"):
            identified["curse_revealed"] = True
            identified["identification_check"] = "Arcana DC 15"

        if item.get("sentient"):
            identified["sentience_revealed"] = True
            identified["communication_established"] = True

        return identified


def main():
    """CLI for the loot generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DnD Loot Generator v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python loot_gen.py -r rare
  python loot_gen.py --hoard --party-level 7 --party-size 5
  python loot_gen.py -t weapon -n 3
  python loot_gen.py --roll major --cursed --sentient
  python loot_gen.py --check-set --items "Holy Avenger" "Plate Armor +2"
        """
    )

    parser.add_argument("-r", "--rarity",
                        choices=["common", "uncommon", "rare", "very rare", "legendary", "artifact"],
                        help="Specific rarity")
    parser.add_argument("-t", "--type", dest="item_type",
                        choices=["weapon", "armor", "ring", "wand", "staff", "wondrous", "potion"],
                        help="Specific item type")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Number of items to generate")
    parser.add_argument("--hoard", action="store_true",
                        help="Generate a full treasure hoard")
    parser.add_argument("--party-size", type=int, default=4,
                        help="Party size for hoard calculation")
    parser.add_argument("--party-level", type=int, default=5,
                        help="Average party level for hoard calculation")
    parser.add_argument("--roll", choices=["d100", "minor", "major"],
                        help="Roll on a treasure table")
    parser.add_argument("--cursed", action="store_true",
                        help="Allow cursed items")
    parser.add_argument("--sentient", action="store_true",
                        help="Allow sentient items")
    parser.add_argument("--check-set", action="store_true",
                        help="Check if items form a set")
    parser.add_argument("--items", nargs="+", help="Items to check for set bonus")
    parser.add_argument("--seed", type=int, help="Random seed")

    args = parser.parse_args()

    generator = LootGenerator()

    if args.check_set and args.items:
        sets = generator.check_item_set(args.items)
        if sets:
            print("=== Item Set Bonuses ===")
            for s in sets:
                print(f"  {s['set_name']}: {s['bonus']}")
        else:
            print("No set bonuses found for these items.")
        return

    if args.hoard:
        hoard = generator.generate_hoard(
            party_size=args.party_size,
            party_level=args.party_level,
            include_magic_items=args.count,
            allow_cursed=args.cursed,
            allow_sentient=args.sentient
        )
        print("=== Treasure Hoard ===")
        print(f"Gold Pieces: {hoard['gold_pieces']}")
        print(f"Gems: {hoard['gems']['count']} worth {hoard['gems']['value_each']} gp each ({hoard['gems']['total_value']} gp)")
        print(f"Art Objects: {hoard['art_objects']['count']} worth {hoard['art_objects']['value_each']} gp each ({hoard['art_objects']['total_value']} gp)")
        print(f"\nMagic Items ({len(hoard['magic_items'])}):")
        for item in hoard['magic_items']:
            curse_sentient = ""
            if item.get('cursed'):
                curse_sentient = " ⚠️ CURSED"
            elif item.get('sentient'):
                curse_sentient = " 🧠 SENTIENT"
            print(f"  {item['name']} ({item['rarity']}) - {item['property']}{curse_sentient}")
        if hoard.get('set_bonuses'):
            print(f"\nSet Bonuses:")
            for s in hoard['set_bonuses']:
                print(f"  {s['set_name']}: {s['bonus']}")
        print(f"\nTotal Value: {hoard['total_value']} gp")

    elif args.roll:
        result = generator.roll_on_table(
            args.roll,
            allow_cursed=args.cursed,
            allow_sentient=args.sentient,
            seed=args.seed
        )
        print(f"=== Treasure Roll ({args.roll}) ===")
        if result.get("type") == "currency":
            print(f"Currency: {result['amount']} {result['currency']}")
        else:
            curse_sentient = ""
            if result.get('cursed'):
                curse_sentient = " ⚠️ CURSED"
            elif result.get('sentient'):
                curse_sentient = " 🧠 SENTIENT"
            print(f"Item: {result['name']}{curse_sentient}")
            print(f"Rarity: {result['rarity']}")
            print(f"Type: {result['type']}")
            print(f"Property: {result['property']}")
            if result.get('sentience'):
                print(f"Sentience: INT {result['sentience']['intelligence']}, {result['sentience']['alignment']}")
                print(f"Communication: {result['sentience']['communication']}")
                print(f"Special: {result['sentience']['special_ability']}")

    else:
        print(f"=== Magic Items ({args.count}) ===")
        for i in range(args.count):
            item = generator.generate_magic_item(
                rarity=args.rarity,
                item_type=args.item_type,
                allow_cursed=args.cursed,
                allow_sentient=args.sentient,
                seed=args.seed + i if args.seed else None
            )
            curse_sentient = ""
            if item.get('cursed'):
                curse_sentient = " ⚠️ CURSED"
            elif item.get('sentient'):
                curse_sentient = " 🧠 SENTIENT"
            print(f"\n{item['name']}{curse_sentient}")
            print(f"  Rarity: {item['rarity']}")
            print(f"  Type: {item['type']}")
            print(f"  Property: {item['property']}")
            print(f"  Value: {item['gold_value']} gp")
            print(f"  Description: {item['description']}")
            if item.get('sentience'):
                print(f"  Sentience: INT {item['sentience']['intelligence']}, {item['sentience']['alignment']}")
                print(f"  Communication: {item['sentience']['communication']}")
                print(f"  Special Ability: {item['sentience']['special_ability']}")


if __name__ == "__main__":
    main()
