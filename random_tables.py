#!/usr/bin/env python3
"""
DnD Random Table Builder v1.0

Create, manage, and roll on custom random tables.
Perfect for generating unique content for your campaigns.

Features:
- Create custom tables with weighted entries
- Roll on tables with single command
- Import/export tables (JSON)
- Pre-built tables (names, events, treasures, etc.)
- Nested table support
- Category organization
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TableEntry:
    """Single entry in a random table."""
    text: str
    weight: int = 1
    min_roll: int = 0
    max_roll: int = 0
    tags: List[str] = field(default_factory=list)
    result_type: str = "text"  # text, table_ref, effect
    sub_table: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "weight": self.weight,
            "tags": self.tags,
            "result_type": self.result_type,
            "sub_table": self.sub_table
        }


@dataclass
class RandomTable:
    """A random table with entries."""
    name: str
    description: str = ""
    category: str = "custom"
    entries: List[TableEntry] = field(default_factory=list)
    roll_type: str = "d100"  # d6, d8, d10, d12, d20, d100, custom
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "entries": [e.to_dict() for e in self.entries],
            "roll_type": self.roll_type,
            "created": self.created
        }
    
    def get_max_roll(self) -> int:
        """Get maximum roll value based on roll type."""
        dice_max = {
            "d6": 6, "d8": 8, "d10": 10, "d12": 12, "d20": 20, "d100": 100
        }
        return dice_max.get(self.roll_type, 100)


class TableBuilder:
    """Build and manage random tables."""

    # Pre-built tables
    PREBUILT_TABLES = {
        "tavern_rumors": {
            "name": "Tavern Rumors",
            "description": "Rumors heard in taverns",
            "category": "social",
            "roll_type": "d20",
            "entries": [
                {"text": "A dragon was spotted in the northern mountains", "weight": 1},
                {"text": "The king's health is failing", "weight": 1},
                {"text": "A new tavern just opened in the lower district", "weight": 2},
                {"text": "Goblin raids have increased on the trade road", "weight": 2},
                {"text": "A mysterious stranger arrived last night", "weight": 2},
                {"text": "The local mine struck a rich vein of silver", "weight": 1},
                {"text": "Wolves have been howling every night this week", "weight": 2},
                {"text": "A traveling circus is coming to town", "weight": 2},
                {"text": "The old wizard's tower has strange lights", "weight": 1},
                {"text": "Bandits have been ambushing merchants", "weight": 2},
                {"text": "A plague is spreading in the next town over", "weight": 1},
                {"text": "The harvest will be poor this year", "weight": 1},
                {"text": "A hero defeated a monster nearby", "weight": 2},
                {"text": "The temple received a generous donation", "weight": 1},
                {"text": "Strange creatures lurk in the sewers", "weight": 1},
                {"text": "A noble's daughter has gone missing", "weight": 1},
                {"text": "The river has been running red", "weight": 1},
                {"text": "An ancient tomb was discovered", "weight": 1},
                {"text": "The guild is recruiting adventurers", "weight": 2},
                {"text": "A comet will pass overhead tonight", "weight": 1},
            ]
        },
        "random_encounters_forest": {
            "name": "Forest Encounters",
            "description": "Random encounters in forest terrain",
            "category": "encounters",
            "roll_type": "d12",
            "entries": [
                {"text": "1d6 Wolves", "weight": 2},
                {"text": "1d4 Bandits", "weight": 2},
                {"text": "A lost traveler seeking help", "weight": 1},
                {"text": "1d3 Bears", "weight": 1},
                {"text": "A hunter checking traps", "weight": 1},
                {"text": "1d6 Goblins", "weight": 2},
                {"text": "A wounded unicorn", "weight": 1},
                {"text": "An owlbear den", "weight": 1},
                {"text": "A druid performing a ritual", "weight": 1},
                {"text": "1d4 Giant Spiders", "weight": 1},
                {"text": "A merchant caravan under attack", "weight": 1},
                {"text": "Nothing - peaceful forest", "weight": 2},
            ]
        },
        "treasure_minor": {
            "name": "Minor Treasure",
            "description": "Small treasures and trinkets",
            "category": "treasure",
            "roll_type": "d20",
            "entries": [
                {"text": "1d6 gp", "weight": 3},
                {"text": "1d10 sp", "weight": 3},
                {"text": "A gemstone worth 10 gp", "weight": 2},
                {"text": "A silver ring worth 5 gp", "weight": 2},
                {"text": "A potion of healing", "weight": 2},
                {"text": "A scroll with a cantrip", "weight": 2},
                {"text": "A masterwork weapon", "weight": 1},
                {"text": "A +1 weapon", "weight": 1},
                {"text": "A bag of 100 cp", "weight": 2},
                {"text": "A golden locket worth 25 gp", "weight": 1},
                {"text": "A map to a hidden location", "weight": 1},
                {"text": "A mysterious key", "weight": 1},
                {"text": "A letter of credit worth 50 gp", "weight": 1},
                {"text": "A jeweled dagger worth 30 gp", "weight": 1},
                {"text": "A clockwork toy worth 20 gp", "weight": 1},
                {"text": "A vial of rare perfume worth 15 gp", "weight": 1},
                {"text": "A silk robe worth 40 gp", "weight": 1},
                {"text": "A +1 piece of armor", "weight": 1},
                {"text": "A wand with 1d10 charges", "weight": 1},
                {"text": "A ring of protection", "weight": 1},
            ]
        },
        "wild_magic": {
            "name": "Wild Magic Surges",
            "description": "Random magical effects",
            "category": "magic",
            "roll_type": "d100",
            "entries": [
                {"text": "You turn blue for 1d4 rounds", "weight": 1},
                {"text": "You grow a tail for 1d6 rounds", "weight": 1},
                {"text": "Maximum damage on next spell", "weight": 1},
                {"text": "Minimum damage on next spell", "weight": 1},
                {"text": "You teleport 30 feet randomly", "weight": 1},
                {"text": "All creatures within 30 ft are polymorphed into sheep", "weight": 1},
                {"text": "You cast fireball centered on yourself", "weight": 1},
                {"text": "You regain all spell slots", "weight": 1},
                {"text": "You lose all spell slots", "weight": 1},
                {"text": "A random creature is summoned", "weight": 1},
            ]
        },
        "plot_twists": {
            "name": "Plot Twists",
            "description": "Unexpected story developments",
            "category": "story",
            "roll_type": "d20",
            "entries": [
                {"text": "The ally is actually a spy", "weight": 1},
                {"text": "The villain is the hero's parent", "weight": 1},
                {"text": "The artifact is a fake", "weight": 1},
                {"text": "The quest giver is the real villain", "weight": 1},
                {"text": "Time travel is involved", "weight": 1},
                {"text": "The party member has a secret twin", "weight": 1},
                {"text": "The kingdom is actually a simulation", "weight": 1},
                {"text": "The gods are dead", "weight": 1},
                {"text": "The prophecy was mistranslated", "weight": 1},
                {"text": "The party has been dead all along", "weight": 1},
                {"text": "The villain is trying to save the world", "weight": 1},
                {"text": "The hero is the chosen one's sibling", "weight": 1},
                {"text": "Magic is disappearing from the world", "weight": 1},
                {"text": "The dungeon is a living creature", "weight": 1},
                {"text": "The party is being manipulated by a greater power", "weight": 1},
                {"text": "The timeline has been altered", "weight": 1},
                {"text": "The NPC is from the future", "weight": 1},
                {"text": "The party created the villain", "weight": 1},
                {"text": "There is a mole in the organization", "weight": 1},
                {"text": "The MacGuffin is sentient", "weight": 1},
            ]
        },
        "npc_quirks": {
            "name": "NPC Quirks",
            "description": "Memorable NPC characteristics",
            "category": "npc",
            "roll_type": "d20",
            "entries": [
                {"text": "Always polishing something", "weight": 1},
                {"text": "Speaks in third person", "weight": 1},
                {"text": "Has a pet animal companion", "weight": 1},
                {"text": "Constantly eating", "weight": 1},
                {"text": "Nervous tick when lying", "weight": 1},
                {"text": "Collects unusual items", "weight": 1},
                {"text": "Speaks very loudly", "weight": 1},
                {"text": "Whispers everything", "weight": 1},
                {"text": "Has a distinctive laugh", "weight": 1},
                {"text": "Always late", "weight": 1},
                {"text": "Superstitious about numbers", "weight": 1},
                {"text": "Talks to inanimate objects", "weight": 1},
                {"text": "Wears mismatched clothing", "weight": 1},
                {"text": "Has an unusual phobia", "weight": 1},
                {"text": "Quotes famous people", "weight": 1},
                {"text": "Cannot remember names", "weight": 1},
                {"text": "Always carries a weapon", "weight": 1},
                {"text": "Has a distinctive scent", "weight": 1},
                {"text": "Moves unusually fast/slow", "weight": 1},
                {"text": "Has a mysterious scar", "weight": 1},
            ]
        },
    }

    def __init__(self, tables_dir: Optional[str] = None):
        """
        Initialize the table builder.
        
        Args:
            tables_dir: Directory to store custom tables
        """
        self.tables_dir = Path(tables_dir) if tables_dir else Path(__file__).parent / "data" / "tables"
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        self.tables: Dict[str, RandomTable] = {}
        self._load_prebuilt_tables()

    def _load_prebuilt_tables(self):
        """Load pre-built tables."""
        for table_name, table_data in self.PREBUILT_TABLES.items():
            table = RandomTable(
                name=table_data["name"],
                description=table_data["description"],
                category=table_data["category"],
                roll_type=table_data["roll_type"],
            )
            for entry_data in table_data["entries"]:
                entry = TableEntry(
                    text=entry_data["text"],
                    weight=entry_data.get("weight", 1)
                )
                table.entries.append(entry)
            self.tables[table_name] = table
        logger.debug(f"Loaded {len(self.PREBUILT_TABLES)} pre-built tables")

    def create_table(
        self,
        name: str,
        description: str = "",
        category: str = "custom",
        roll_type: str = "d100"
    ) -> RandomTable:
        """
        Create a new empty table.
        
        Args:
            name: Table name
            description: Table description
            category: Category for organization
            roll_type: Type of die to roll
            
        Returns:
            Created RandomTable
        """
        table = RandomTable(
            name=name,
            description=description,
            category=category,
            roll_type=roll_type
        )
        self.tables[name.lower()] = table
        return table

    def add_entry(
        self,
        table_name: str,
        text: str,
        weight: int = 1,
        tags: Optional[List[str]] = None,
        sub_table: Optional[str] = None
    ) -> bool:
        """
        Add an entry to a table.
        
        Args:
            table_name: Name of the table
            text: Entry text/result
            weight: Entry weight (for weighted rolls)
            tags: Optional tags for filtering
            sub_table: Optional sub-table reference
            
        Returns:
            True if successful
        """
        table = self.tables.get(table_name.lower())
        if not table:
            logger.error(f"Table '{table_name}' not found")
            return False
        
        entry = TableEntry(
            text=text,
            weight=weight,
            tags=tags or [],
            sub_table=sub_table
        )
        table.entries.append(entry)
        logger.debug(f"Added entry to {table_name}: {text[:30]}...")
        return True

    def roll(
        self,
        table_name: str,
        times: int = 1,
        unique: bool = False,
        seed: Optional[int] = None
    ) -> List[TableEntry]:
        """
        Roll on a table.
        
        Args:
            table_name: Name of the table
            times: Number of rolls
            unique: Ensure unique results
            seed: Random seed
            
        Returns:
            List of rolled entries
        """
        if seed is not None:
            random.seed(seed)
        
        table = self.tables.get(table_name.lower())
        if not table:
            logger.error(f"Table '{table_name}' not found")
            return []
        
        results = []
        available_entries = table.entries.copy()
        
        for _ in range(times):
            if not available_entries:
                break
            
            # Weighted random selection
            total_weight = sum(e.weight for e in available_entries)
            roll = random.uniform(0, total_weight)
            cumulative = 0
            
            selected = None
            for entry in available_entries:
                cumulative += entry.weight
                if roll <= cumulative:
                    selected = entry
                    break
            
            if selected:
                results.append(selected)
                if unique:
                    available_entries.remove(selected)
        
        return results

    def roll_detailed(
        self,
        table_name: str,
        times: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Roll on a table with detailed results.
        
        Args:
            table_name: Name of the table
            times: Number of rolls
            
        Returns:
            List of detailed result dicts
        """
        entries = self.roll(table_name, times)
        results = []
        
        for entry in entries:
            result = {
                "text": entry.text,
                "table": table_name,
                "tags": entry.tags
            }
            
            # Handle sub-table references
            if entry.sub_table:
                sub_results = self.roll(entry.sub_table, 1)
                if sub_results:
                    result["sub_result"] = sub_results[0].text
            
            results.append(result)
        
        return results

    def list_tables(self, category: Optional[str] = None) -> List[str]:
        """
        List available tables.
        
        Args:
            category: Filter by category
            
        Returns:
            List of table names
        """
        if category:
            return [t.name for t in self.tables.values() if t.category == category]
        return [t.name for t in self.tables.values()]

    def get_table(self, name: str) -> Optional[RandomTable]:
        """Get a table by name."""
        return self.tables.get(name.lower())

    def remove_entry(self, table_name: str, entry_index: int) -> bool:
        """Remove an entry from a table."""
        table = self.tables.get(table_name.lower())
        if not table or entry_index >= len(table.entries):
            return False
        
        table.entries.pop(entry_index)
        return True

    def export_table(self, table_name: str, filepath: Optional[str] = None) -> str:
        """
        Export a table to JSON.
        
        Args:
            table_name: Name of the table
            filepath: Output file path (optional)
            
        Returns:
            JSON string
        """
        table = self.tables.get(table_name.lower())
        if not table:
            return ""
        
        json_str = json.dumps(table.to_dict(), indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
            logger.info(f"Exported table to {filepath}")
        
        return json_str

    def import_table(self, filepath: str) -> bool:
        """
        Import a table from JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            table = RandomTable(
                name=data.get("name", "Imported Table"),
                description=data.get("description", ""),
                category=data.get("category", "custom"),
                roll_type=data.get("roll_type", "d100"),
                created=data.get("created", datetime.now(timezone.utc).isoformat())
            )
            
            for entry_data in data.get("entries", []):
                entry = TableEntry(
                    text=entry_data.get("text", ""),
                    weight=entry_data.get("weight", 1),
                    tags=entry_data.get("tags", []),
                    sub_table=entry_data.get("sub_table")
                )
                table.entries.append(entry)
            
            self.tables[table.name.lower()] = table
            logger.info(f"Imported table: {table.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import table: {e}")
            return False

    def export_all_tables(self, filepath: str) -> None:
        """Export all custom tables to a single JSON file."""
        data = {name: table.to_dict() for name, table in self.tables.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported all tables to {filepath}")

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return list(set(t.category for t in self.tables.values()))


def main():
    """CLI for random table builder."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DnD Random Table Builder v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python random_tables.py --list
  python random_tables.py --roll tavern_rumors
  python random_tables.py --roll wild_magic -n 3
  python random_tables.py --create "My Table" --category custom
  python random_tables.py --roll plot_twists --unique
        """
    )
    
    parser.add_argument("--list", action="store_true",
                        help="List available tables")
    parser.add_argument("--categories", action="store_true",
                        help="List table categories")
    parser.add_argument("--roll", type=str,
                        help="Roll on a table")
    parser.add_argument("-n", "--times", type=int, default=1,
                        help="Number of rolls")
    parser.add_argument("--unique", action="store_true",
                        help="Ensure unique results")
    parser.add_argument("--create", type=str,
                        help="Create a new table")
    parser.add_argument("--category", type=str, default="custom",
                        help="Table category")
    parser.add_argument("--add-entry", type=str,
                        help="Add entry to table (format: table:text:weight)")
    parser.add_argument("--export", type=str,
                        help="Export table to file")
    parser.add_argument("--seed", type=int,
                        help="Random seed")
    
    args = parser.parse_args()
    
    builder = TableBuilder()
    
    if args.list:
        print("=== Available Tables ===\n")
        categories = {}
        for table in builder.tables.values():
            if table.category not in categories:
                categories[table.category] = []
            categories[table.category].append(table.name)
        
        for category, tables in sorted(categories.items()):
            print(f"\n{category.upper()}:")
            for table in tables:
                print(f"  • {table}")
        return
    
    if args.categories:
        print("=== Table Categories ===\n")
        for cat in builder.get_categories():
            print(f"  • {cat}")
        return
    
    if args.create:
        table = builder.create_table(args.create, category=args.category)
        print(f"Created table: {table.name}")
        print(f"Category: {table.category}")
        print(f"Roll type: {table.roll_type}")
        return
    
    if args.add_entry:
        parts = args.add_entry.split(":")
        if len(parts) >= 2:
            table_name = parts[0]
            text = parts[1]
            weight = int(parts[2]) if len(parts) > 2 else 1
            builder.add_entry(table_name, text, weight)
            print(f"Added '{text}' to {table_name}")
        return
    
    if args.roll:
        results = builder.roll_detailed(args.roll, args.times)
        print(f"\n=== {args.roll} ({len(results)} rolls) ===\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['text']}")
            if result.get('sub_result'):
                print(f"   → {result['sub_result']}")
        return
    
    if args.export:
        if args.roll:
            builder.export_table(args.roll, args.export)
        else:
            builder.export_all_tables(args.export)
        print(f"Exported to {args.export}")
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
