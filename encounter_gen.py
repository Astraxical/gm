#!/usr/bin/env python3
"""
DnD Encounter Generator v2.0

Generate random encounters filtered by CR and terrain.
Supports lair actions, legendary actions, and environmental hazards.
Uses expanded SRD monster data for balanced encounters.
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


class EncounterGenerator:
    """Generate DnD encounters based on CR and terrain."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the encounter generator.

        Args:
            data_dir: Directory containing SRD data files
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)
        self.monsters: List[Dict[str, Any]] = []
        self.lair_actions: Dict[str, List[str]] = {}
        self.legendary_actions: Dict[str, List[str]] = {}
        self.environmental_hazards: Dict[str, List[str]] = {}
        self.cr_ranges: Dict[str, Dict[str, int]] = {}
        self.terrain_types: List[str] = []
        self._load_monsters()

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_monster_data(data_dir: Path) -> Dict[str, Any]:
        """
        Load monster data with LRU caching.
        
        Args:
            data_dir: Directory containing data files
            
        Returns:
            Dict with all monster data
        """
        monsters_file = data_dir / "srd_monsters.json"
        if monsters_file.exists():
            with open(monsters_file, 'r') as f:
                return json.load(f)
        return {}

    def _load_monsters(self):
        """Load monster data from SRD file."""
        data = self._load_monster_data(self.data_dir)
        
        if data:
            self.monsters = data.get("monsters", [])
            self.cr_ranges = data.get("cr_ranges", {})
            self.terrain_types = data.get("terrain_types", [])
            self.lair_actions = data.get("lair_actions", {})
            self.legendary_actions = data.get("legendary_actions", {})
            self.environmental_hazards = data.get("environmental_hazards", {})
            logger.debug(f"Loaded {len(self.monsters)} monsters from cache")
        else:
            # Fallback minimal data
            self.monsters = [
                {"name": "Goblin", "type": "humanoid", "cr": "0.25", "ac": 15, "hp": 7, "terrain": ["dungeon", "forest"]},
                {"name": "Orc", "type": "humanoid", "cr": "0.5", "ac": 13, "hp": 15, "terrain": ["plains", "mountain"]},
                {"name": "Ogre", "type": "giant", "cr": "2", "ac": 11, "hp": 59, "terrain": ["mountain", "forest"]},
                {"name": "Troll", "type": "giant", "cr": "5", "ac": 15, "hp": 84, "terrain": ["forest", "swamp"]},
                {"name": "Adult Red Dragon", "type": "dragon", "cr": "17", "ac": 19, "hp": 256, "terrain": ["mountain"]},
            ]
            self.cr_ranges = {
                "easy": {"min": 0, "max": 1},
                "medium": {"min": 1, "max": 4},
                "hard": {"min": 4, "max": 10},
                "deadly": {"min": 10, "max": 21}
            }
            self.terrain_types = ["dungeon", "forest", "mountain", "plains", "swamp", "ruins"]
            self.lair_actions = {}
            self.legendary_actions = {}
            self.environmental_hazards = {}
            logger.warning("Using fallback monster data")

    def _parse_cr(self, cr: str) -> float:
        """Parse CR string to float."""
        if "/" in cr:
            parts = cr.split("/")
            return int(parts[0]) / int(parts[1])
        return float(cr)

    def _get_monster_type_key(self, monster_type: str) -> str:
        """Get the key for lair/legendary actions based on monster type."""
        type_mapping = {
            "dragon": "dragon",
            "undead": "lich",
            "aberration": "beholder",
            "fiend": "demon",
            "monstrosity": "tarrasque"
        }
        return type_mapping.get(monster_type.lower(), "")

    def filter_monsters(self, terrain: Optional[str] = None,
                        min_cr: Optional[float] = None,
                        max_cr: Optional[float] = None,
                        monster_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter monsters by criteria.

        Args:
            terrain: Filter by terrain type
            min_cr: Minimum challenge rating
            max_cr: Maximum challenge rating
            monster_type: Filter by monster type (humanoid, undead, etc.)

        Returns:
            List of matching monsters
        """
        filtered = self.monsters

        if terrain:
            filtered = [m for m in filtered if terrain.lower() in [t.lower() for t in m.get("terrain", [])] or "any" in [t.lower() for t in m.get("terrain", [])]]

        if min_cr is not None:
            filtered = [m for m in filtered if self._parse_cr(m.get("cr", "0")) >= min_cr]

        if max_cr is not None:
            filtered = [m for m in filtered if self._parse_cr(m.get("cr", "0")) <= max_cr]

        if monster_type:
            filtered = [m for m in filtered if m.get("type", "").lower() == monster_type.lower()]

        return filtered

    def generate_encounter(self, difficulty: str = "medium",
                           terrain: Optional[str] = None,
                           party_size: int = 4,
                           party_level: int = 5,
                           max_monsters: int = 6,
                           include_lair_actions: bool = False,
                           include_hazards: bool = False) -> Dict[str, Any]:
        """
        Generate a balanced encounter.

        Args:
            difficulty: Encounter difficulty (easy, medium, hard, deadly, boss, epic)
            terrain: Terrain type for filtering
            party_size: Number of party members
            party_level: Average party level
            max_monsters: Maximum number of monsters
            include_lair_actions: Whether to include lair actions for legendary creatures
            include_hazards: Whether to include environmental hazards

        Returns:
            Encounter dict with monsters, XP, and optional features
        """
        # Get CR range for difficulty
        cr_range = self.cr_ranges.get(difficulty.lower(), self.cr_ranges.get("medium"))
        min_cr = cr_range.get("min", 0)
        max_cr = cr_range.get("max", 4)

        # Adjust CR based on party level
        max_cr = min(max_cr, party_level + 2)

        # Filter available monsters
        available = self.filter_monsters(terrain=terrain, max_cr=max_cr)

        if not available:
            available = self.monsters  # Fallback to all monsters

        # Calculate target XP budget
        xp_budget = self._calculate_xp_budget(party_size, party_level, difficulty)

        # Select monsters
        encounter_monsters = []
        total_xp = 0
        attempts = 0

        while total_xp < xp_budget and len(encounter_monsters) < max_monsters and attempts < 100:
            monster = random.choice(available)
            monster_xp = self._cr_to_xp(self._parse_cr(monster.get("cr", "0.25")))

            if total_xp + monster_xp <= xp_budget * 1.2:  # Allow up to 20% over budget
                monster_entry = {
                    "name": monster["name"],
                    "type": monster.get("type", "unknown"),
                    "cr": monster.get("cr", "0.25"),
                    "ac": monster.get("ac", 10),
                    "hp": monster.get("hp", 10),
                    "count": 1,
                    "traits": monster.get("traits", [])
                }

                # Add lair actions for legendary creatures
                if include_lair_actions and self._parse_cr(monster.get("cr", "0")) >= 10:
                    type_key = self._get_monster_type_key(monster.get("type", ""))
                    if type_key and type_key in self.lair_actions:
                        monster_entry["lair_actions"] = random.sample(
                            self.lair_actions[type_key],
                            min(3, len(self.lair_actions[type_key]))
                        )

                # Add legendary actions for legendary creatures
                if include_lair_actions and self._parse_cr(monster.get("cr", "0")) >= 10:
                    type_key = self._get_monster_type_key(monster.get("type", ""))
                    if type_key and type_key in self.legendary_actions:
                        monster_entry["legendary_actions"] = self.legendary_actions[type_key]
                        monster_entry["legendary_resistance"] = 3

                encounter_monsters.append(monster_entry)
                total_xp += monster_xp
            attempts += 1

        # Calculate adjusted XP for multiple monsters
        adjusted_xp = self._calculate_adjusted_xp(total_xp, len(encounter_monsters))

        encounter = {
            "difficulty": difficulty,
            "terrain": terrain,
            "monsters": encounter_monsters,
            "total_xp": total_xp,
            "adjusted_xp": adjusted_xp,
            "xp_budget": xp_budget,
            "monster_count": len(encounter_monsters)
        }

        # Add environmental hazards
        if include_hazards and terrain and terrain in self.environmental_hazards:
            hazards = self.environmental_hazards[terrain]
            encounter["environmental_hazards"] = random.sample(hazards, min(2, len(hazards)))

        return encounter

    def _calculate_xp_budget(self, party_size: int, party_level: int, difficulty: str) -> int:
        """Calculate XP budget based on party size, level, and difficulty."""
        # DMG XP thresholds by level (simplified)
        thresholds = {
            1: {"easy": 25, "medium": 50, "hard": 75, "deadly": 100},
            2: {"easy": 50, "medium": 100, "hard": 150, "deadly": 200},
            3: {"easy": 75, "medium": 150, "hard": 225, "deadly": 400},
            4: {"easy": 125, "medium": 250, "hard": 375, "deadly": 500},
            5: {"easy": 250, "medium": 500, "hard": 750, "deadly": 1100},
            6: {"easy": 300, "medium": 600, "hard": 900, "deadly": 1400},
            7: {"easy": 350, "medium": 750, "hard": 1100, "deadly": 1700},
            8: {"easy": 400, "medium": 850, "hard": 1250, "deadly": 1900},
            9: {"easy": 450, "medium": 900, "hard": 1400, "deadly": 2100},
            10: {"easy": 500, "medium": 1000, "hard": 1500, "deadly": 2300},
            11: {"easy": 550, "medium": 1100, "hard": 1600, "deadly": 2400},
            12: {"easy": 600, "medium": 1200, "hard": 1700, "deadly": 2500},
            13: {"easy": 650, "medium": 1300, "hard": 1800, "deadly": 2600},
            14: {"easy": 700, "medium": 1400, "hard": 1900, "deadly": 2700},
            15: {"easy": 750, "medium": 1500, "hard": 2000, "deadly": 2800},
            16: {"easy": 800, "medium": 1600, "hard": 2100, "deadly": 2900},
            17: {"easy": 850, "medium": 1700, "hard": 2200, "deadly": 3000},
            18: {"easy": 900, "medium": 1800, "hard": 2300, "deadly": 3100},
            19: {"easy": 950, "medium": 1900, "hard": 2400, "deadly": 3200},
            20: {"easy": 1000, "medium": 2000, "hard": 2500, "deadly": 3300},
        }

        base = thresholds.get(min(party_level, 20), thresholds[20])
        difficulty_xp = base.get(difficulty.lower(), base["medium"])

        # Multiplier for party size
        size_multipliers = {1: 1, 2: 1.5, 3: 2, 4: 2.5, 5: 3, 6: 3.5}
        multiplier = size_multipliers.get(min(party_size, 6), 3.5)

        return int(difficulty_xp * multiplier)

    def _cr_to_xp(self, cr: float) -> int:
        """Convert CR to XP value."""
        xp_table = {
            0: 0, 0.125: 10, 0.25: 50, 0.5: 100, 1: 200, 2: 450,
            3: 700, 4: 1100, 5: 1800, 6: 2300, 7: 2900, 8: 3900,
            9: 5000, 10: 5900, 11: 7200, 12: 8400, 13: 10000,
            14: 11500, 15: 13000, 16: 15000, 17: 18000, 18: 20000,
            19: 22000, 20: 25000, 21: 28000, 22: 31000, 23: 34000,
            24: 37000, 25: 40000, 26: 43000, 27: 46000, 28: 49000,
            29: 52000, 30: 55000
        }
        return xp_table.get(int(cr) if cr >= 1 else cr, 100)

    def _calculate_adjusted_xp(self, base_xp: int, monster_count: int) -> int:
        """Calculate adjusted XP for encounter difficulty."""
        multipliers = {1: 1, 2: 1.5, 3: 2, 4: 2.5, 5: 3, 6: 3.5, 7: 4, 8: 4.5}
        multiplier = multipliers.get(min(monster_count, 8), 4.5)
        return int(base_xp * multiplier)

    def generate_boss_encounter(self, boss_cr: int = 15,
                                party_size: int = 4,
                                party_level: int = 10,
                                terrain: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a boss encounter with minions.

        Args:
            boss_cr: Challenge rating of the boss
            party_size: Number of party members
            party_level: Average party level
            terrain: Terrain type for filtering

        Returns:
            Boss encounter dict
        """
        # Find a boss monster
        bosses = [m for m in self.monsters 
                  if self._parse_cr(m.get("cr", "0")) >= boss_cr - 2 
                  and self._parse_cr(m.get("cr", "0")) <= boss_cr + 2]
        
        if terrain:
            bosses = [m for m in bosses 
                     if terrain.lower() in [t.lower() for t in m.get("terrain", [])]]

        if not bosses:
            bosses = [m for m in self.monsters if self._parse_cr(m.get("cr", "0")) >= boss_cr]

        if not bosses:
            bosses = self.monsters

        boss = random.choice(bosses)

        # Add minions (CR 1-4)
        minions = self.filter_monsters(terrain=terrain, min_cr=0.25, max_cr=4)
        minion_count = random.randint(2, 6)
        minion_selection = random.sample(minions, min(minion_count, len(minions)))

        encounter_monsters = [{
            "name": boss["name"],
            "type": boss.get("type", "unknown"),
            "cr": boss.get("cr", "15"),
            "ac": boss.get("ac", 18),
            "hp": boss.get("hp", 200),
            "count": 1,
            "is_boss": True,
            "traits": boss.get("traits", []),
            "lair_actions": [],
            "legendary_actions": [],
            "legendary_resistance": 3
        }]

        # Add boss features
        type_key = self._get_monster_type_key(boss.get("type", ""))
        if type_key:
            if type_key in self.lair_actions:
                encounter_monsters[0]["lair_actions"] = random.sample(
                    self.lair_actions[type_key],
                    min(3, len(self.lair_actions[type_key]))
                )
            if type_key in self.legendary_actions:
                encounter_monsters[0]["legendary_actions"] = self.legendary_actions[type_key]

        for minion in minion_selection:
            encounter_monsters.append({
                "name": minion["name"],
                "type": minion.get("type", "unknown"),
                "cr": minion.get("cr", "1"),
                "ac": minion.get("ac", 12),
                "hp": minion.get("hp", 20),
                "count": 1,
                "is_minion": True,
                "traits": minion.get("traits", [])
            })

        total_xp = sum(self._cr_to_xp(self._parse_cr(m["cr"])) for m in encounter_monsters)

        return {
            "difficulty": "boss",
            "terrain": terrain,
            "monsters": encounter_monsters,
            "total_xp": total_xp,
            "adjusted_xp": total_xp,  # Boss encounters use raw XP
            "boss": boss["name"],
            "minion_count": len(minion_selection)
        }

    def generate_random_encounter(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Generate a completely random encounter."""
        if seed is not None:
            random.seed(seed)

        terrain = random.choice(self.terrain_types)
        difficulty = random.choice(["easy", "medium", "hard", "deadly"])

        return self.generate_encounter(difficulty=difficulty, terrain=terrain)

    def list_terrains(self) -> List[str]:
        """Return list of available terrain types."""
        return self.terrain_types

    def list_monster_types(self) -> List[str]:
        """Return list of unique monster types."""
        types = set(m.get("type", "unknown") for m in self.monsters)
        return sorted(list(types))

    def get_monster_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a monster by name."""
        for monster in self.monsters:
            if monster["name"].lower() == name.lower():
                return monster
        return None

    def get_monsters_by_cr(self, min_cr: float, max_cr: float) -> List[Dict[str, Any]]:
        """Get all monsters within a CR range."""
        return [m for m in self.monsters 
                if min_cr <= self._parse_cr(m.get("cr", "0")) <= max_cr]


def main():
    """CLI for the encounter generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DnD Encounter Generator v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python encounter_gen.py -t forest -d medium
  python encounter_gen.py -t dungeon --party-level 3 --party-size 5
  python encounter_gen.py --random
  python encounter_gen.py --boss --boss-cr 17 -t mountain
  python encounter_gen.py --list-terrains
  python encounter_gen.py --list-types
        """
    )

    parser.add_argument("-t", "--terrain", help="Terrain type (forest, dungeon, etc.)")
    parser.add_argument("-d", "--difficulty", default="medium",
                        choices=["easy", "medium", "hard", "deadly", "boss", "epic"],
                        help="Encounter difficulty")
    parser.add_argument("--party-size", type=int, default=4,
                        help="Number of party members")
    parser.add_argument("--party-level", type=int, default=5,
                        help="Average party level")
    parser.add_argument("--boss", action="store_true",
                        help="Generate boss encounter with minions")
    parser.add_argument("--boss-cr", type=int, default=15,
                        help="Boss CR for boss encounters")
    parser.add_argument("--lair-actions", action="store_true",
                        help="Include lair/legendary actions")
    parser.add_argument("--hazards", action="store_true",
                        help="Include environmental hazards")
    parser.add_argument("--random", action="store_true",
                        help="Generate completely random encounter")
    parser.add_argument("--list-terrains", action="store_true",
                        help="List available terrain types")
    parser.add_argument("--list-types", action="store_true",
                        help="List available monster types")
    parser.add_argument("--monster", help="Get info on specific monster")
    parser.add_argument("--seed", type=int, help="Random seed")

    args = parser.parse_args()

    generator = EncounterGenerator()

    if args.list_terrains:
        print("Available terrains:", ", ".join(generator.list_terrains()))
        return

    if args.list_types:
        print("Available monster types:", ", ".join(generator.list_monster_types()))
        print(f"\nTotal monsters: {len(generator.monsters)}")
        return

    if args.monster:
        monster = generator.get_monster_by_name(args.monster)
        if monster:
            print(f"=== {monster['name']} ===")
            print(f"Type: {monster.get('type', 'unknown')}")
            print(f"CR: {monster.get('cr', '0')}")
            print(f"AC: {monster.get('ac', 10)}")
            print(f"HP: {monster.get('hp', 10)}")
            print(f"Terrain: {', '.join(monster.get('terrain', []))}")
            if monster.get('traits'):
                print(f"Traits: {', '.join(monster['traits'])}")
        else:
            print(f"Monster '{args.monster}' not found")
        return

    if args.boss:
        encounter = generator.generate_boss_encounter(
            boss_cr=args.boss_cr,
            party_size=args.party_size,
            party_level=args.party_level,
            terrain=args.terrain
        )
    elif args.random:
        encounter = generator.generate_random_encounter(seed=args.seed)
    else:
        encounter = generator.generate_encounter(
            difficulty=args.difficulty,
            terrain=args.terrain,
            party_size=args.party_size,
            party_level=args.party_level,
            include_lair_actions=args.lair_actions,
            include_hazards=args.hazards
        )

    print(f"=== {encounter['difficulty'].capitalize()} Encounter ===")
    if encounter.get('terrain'):
        print(f"Terrain: {encounter['terrain']}")
    print(f"XP Budget: {encounter['xp_budget']}")
    print(f"Adjusted XP: {encounter['adjusted_xp']}")
    print(f"\nMonsters ({encounter['monster_count']}):")

    for monster in encounter['monsters']:
        count = monster.get('count', 1)
        prefix = "👹 " if monster.get('is_boss') else "💀 " if monster.get('is_minion') else "• "
        stats = f"CR {monster['cr']}, AC {monster['ac']}, HP {monster['hp']}"
        if monster.get('legendary_resistance'):
            stats += f", LR: {monster['legendary_resistance']}"
        print(f"  {prefix}{count}x {monster['name']} ({stats})")
        
        if monster.get('lair_actions'):
            print(f"      Lair Actions: {', '.join(monster['lair_actions'])}")
        if monster.get('legendary_actions'):
            print(f"      Legendary Actions: {', '.join(monster['legendary_actions'])}")

    if encounter.get('environmental_hazards'):
        print(f"\nEnvironmental Hazards:")
        for hazard in encounter['environmental_hazards']:
            print(f"  • {hazard}")

    if encounter.get('boss'):
        print(f"\nBoss: {encounter['boss']} with {encounter['minion_count']} minions")


if __name__ == "__main__":
    main()
