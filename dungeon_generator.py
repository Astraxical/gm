#!/usr/bin/env python3
"""
DnD Dungeon Generator v1.0

Generate procedural dungeons, rooms, traps, and features.
Create complete dungeon maps with encounters and treasure.

Features:
- Procedural room generation
- Room types (combat, trap, treasure, puzzle, etc.)
- Corridor connections
- Dungeon themes (crypt, cave, castle, etc.)
- Export to JSON/Markdown/ASCII map
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class RoomType(str, Enum):
    """Types of dungeon rooms."""
    ENTRANCE = "entrance"
    CORRIDOR = "corridor"
    EMPTY = "empty"
    COMBAT = "combat"
    TRAP = "trap"
    TREASURE = "treasure"
    PUZZLE = "puzzle"
    NPC = "npc"
    BOSS = "boss"
    SECRET = "secret"
    TRAP_TREASURE = "trap_treasure"


class DungeonTheme(str, Enum):
    """Dungeon themes/aesthetics."""
    CRYPT = "crypt"
    CAVE = "cave"
    CASTLE = "castle"
    RUINS = "ruins"
    MINE = "mine"
    TEMPLE = "temple"
    SEWER = "sewer"
    TOWER = "tower"
    UNDERDARK = "underdark"
    LABYRINTH = "labyrinth"


@dataclass
class Room:
    """A single dungeon room."""
    id: int
    name: str
    room_type: str
    x: int = 0
    y: int = 0
    width: int = 10
    height: int = 10
    description: str = ""
    features: List[str] = field(default_factory=list)
    encounters: List[Dict[str, Any]] = field(default_factory=list)
    traps: List[Dict[str, Any]] = field(default_factory=list)
    treasure: List[Dict[str, Any]] = field(default_factory=list)
    exits: List[str] = field(default_factory=list)  # N, S, E, W
    secret_exits: List[str] = field(default_factory=list)
    dc_to_enter: int = 0
    explored: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DungeonLevel:
    """A single level of a dungeon."""
    level_number: int
    name: str
    difficulty: str  # easy, medium, hard, deadly
    rooms: List[Room] = field(default_factory=list)
    connections: List[Tuple[int, int]] = field(default_factory=list)  # (room1_id, room2_id)
    level_feature: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["connections"] = [(c[0], c[1]) for c in self.connections]
        return data


@dataclass
class Dungeon:
    """Complete dungeon structure."""
    name: str
    theme: str
    total_levels: int
    levels: List[DungeonLevel] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    backstory: str = ""
    dungeon_features: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "theme": self.theme,
            "total_levels": self.total_levels,
            "levels": [l.to_dict() for l in self.levels],
            "created": self.created,
            "backstory": self.backstory,
            "dungeon_features": self.dungeon_features
        }


class DungeonGenerator:
    """Generate procedural dungeons."""

    # Room name templates by type
    ROOM_NAMES = {
        RoomType.ENTRANCE: ["Entrance Hall", "Main Gate", "Entry Chamber", "Threshold", "Vestibule"],
        RoomType.CORRIDOR: ["Long Corridor", "Hallway", "Passage", "Gallery", "Walkway"],
        RoomType.EMPTY: ["Empty Chamber", "Vacant Room", "Hollow Hall", "Bare Chamber", "Desolate Room"],
        RoomType.COMBAT: ["Battle Chamber", "Arena", "Guard Room", "War Room", "Combat Hall"],
        RoomType.TRAP: ["Trap Corridor", "Hazard Chamber", "Danger Zone", "Death Trap", "Peril Room"],
        RoomType.TREASURE: ["Treasure Vault", "Storeroom", "Cache", "Armory", "Reliquary"],
        RoomType.PUZZLE: ["Puzzle Chamber", "Riddle Room", "Mystery Hall", "Enigma Chamber", "Test Room"],
        RoomType.NPC: ["Guard Post", "Meeting Chamber", "Audience Hall", "Throne Room", "Sanctuary"],
        RoomType.BOSS: ["Boss Chamber", "Final Hall", "Master's Sanctum", "Inner Sanctum", "Crown Chamber"],
        RoomType.SECRET: ["Hidden Chamber", "Secret Room", "Concealed Hall", "Vault", "Sanctuary"],
        RoomType.TRAP_TREASURE: ["Trapped Vault", "Guarded Treasury", "Warded Cache", "Protected Hoard", "Sealed Vault"],
    }

    # Room descriptions by theme
    ROOM_DESCRIPTIONS = {
        DungeonTheme.CRYPT: [
            "Ancient stone walls covered in funeral inscriptions.",
            "Sarcophagi line the walls, dust covering every surface.",
            "The air is cold and still, heavy with the weight of death.",
            "Flickering torches cast dancing shadows on the stone.",
            "Bone fragments crunch underfoot with each step."
        ],
        DungeonTheme.CAVE: [
            "Natural stone formations create an otherworldly landscape.",
            "Stalactites hang from the ceiling like stone daggers.",
            "Water drips steadily from somewhere in the darkness.",
            "The cave walls shimmer with mineral deposits.",
            "Narrow passages wind through the natural rock."
        ],
        DungeonTheme.CASTLE: [
            "Well-crafted stonework speaks of ancient craftsmanship.",
            "Tattered banners hang from the vaulted ceiling.",
            "Arrow slits let thin beams of light pierce the darkness.",
            "The remains of a once-grand hall now lie in ruin.",
            "Suit of armor stand guard along the walls."
        ],
        DungeonTheme.RUINS: [
            "Collapsed rubble blocks several passageways.",
            "Vines and moss have reclaimed much of the structure.",
            "The remnants of ancient civilization surround you.",
            "Weathered stone crumbles at your touch.",
            "What was once magnificent now lies in decay."
        ],
        DungeonTheme.TEMPLE: [
            "Sacred symbols adorn every available surface.",
            "The air hums with divine energy.",
            "Stone altars stand in various states of preservation.",
            "Incense burns despite the passage of time.",
            "Holy texts are carved into the walls."
        ],
    }

    # Features by room type
    ROOM_FEATURES = {
        RoomType.ENTRANCE: ["Torch sconces", "Welcome inscription", "Guard statues", "Weapon rack", "Coat hooks"],
        RoomType.COMBAT: ["Pillars for cover", "Elevated platform", "Weapon racks", "Bloodstains", "Broken furniture"],
        RoomType.TREASURE: ["Pedestal", "Locked chest", "Display case", "Safe", "Treasure pile"],
        RoomType.PUZZLE: ["Stone tablets", "Pressure plates", "Rotating rings", "Symbol patterns", "Riddle inscription"],
        RoomType.NPC: ["Throne", "Desk", "Chairs", "Food spread", "Servant quarters"],
        RoomType.TRAP: ["Strange markings", "Worn floor tiles", "Draft sensation", "Clicking sounds", "Skeleton remains"],
    }

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the dungeon generator.
        
        Args:
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

    def generate_dungeon(
        self,
        name: str = "The Forgotten Dungeon",
        theme: str = "crypt",
        levels: int = 3,
        rooms_per_level: int = 8,
        difficulty: str = "medium"
    ) -> Dungeon:
        """
        Generate a complete dungeon.
        
        Args:
            name: Dungeon name
            theme: Dungeon theme (crypt, cave, castle, etc.)
            levels: Number of dungeon levels
            rooms_per_level: Average rooms per level
            difficulty: Overall difficulty
            
        Returns:
            Complete Dungeon object
        """
        dungeon = Dungeon(
            name=name,
            theme=theme,
            total_levels=levels,
            backstory=self._generate_backstory(theme),
            dungeon_features=self._generate_dungeon_features(theme)
        )
        
        for level_num in range(1, levels + 1):
            level = self._generate_level(
                level_num=level_num,
                theme=theme,
                num_rooms=rooms_per_level + random.randint(-2, 2),
                difficulty=difficulty
            )
            dungeon.levels.append(level)
        
        logger.info(f"Generated dungeon: {name} ({levels} levels, {theme})")
        return dungeon

    def _generate_level(
        self,
        level_num: int,
        theme: str,
        num_rooms: int,
        difficulty: str
    ) -> DungeonLevel:
        """Generate a single dungeon level."""
        level = DungeonLevel(
            level_number=level_num,
            name=f"Level {level_num}: {self._get_level_name(level_num, theme)}",
            difficulty=difficulty,
            level_feature=self._get_level_feature(level_num, theme)
        )
        
        # Generate rooms
        rooms = []
        room_types = self._get_room_distribution(level_num, num_rooms)
        
        for i, room_type in enumerate(room_types):
            room = self._generate_room(
                room_id=i,
                room_type=room_type,
                theme=theme,
                level=level_num
            )
            rooms.append(room)
        
        level.rooms = rooms
        
        # Connect rooms (simple linear + some branches)
        level.connections = self._connect_rooms(rooms)
        
        return level

    def _get_room_distribution(self, level_num: int, num_rooms: int) -> List[RoomType]:
        """Determine room type distribution for a level."""
        distribution = []
        
        # Always start with entrance
        distribution.append(RoomType.ENTRANCE)
        
        # Fill with various room types
        remaining = num_rooms - 2  # Reserve last for boss
        weights = {
            RoomType.EMPTY: 20,
            RoomType.COMBAT: 25,
            RoomType.TRAP: 15,
            RoomType.TREASURE: 10,
            RoomType.PUZZLE: 10,
            RoomType.NPC: 10,
            RoomType.TRAP_TREASURE: 5,
            RoomType.SECRET: 5,
        }
        
        for _ in range(remaining):
            room_type = random.choices(
                list(weights.keys()),
                weights=list(weights.values())
            )[0]
            distribution.append(room_type)
        
        # End with boss on final levels
        distribution.append(RoomType.BOSS)
        
        return distribution

    def _generate_room(
        self,
        room_id: int,
        room_type: RoomType,
        theme: str,
        level: int
    ) -> Room:
        """Generate a single room."""
        name_list = self.ROOM_NAMES.get(room_type, ["Chamber"])
        name = random.choice(name_list)
        
        # Get description based on theme
        descriptions = self.ROOM_DESCRIPTIONS.get(theme, self.ROOM_DESCRIPTIONS[DungeonTheme.CRYPT])
        description = random.choice(descriptions)
        
        # Get features
        features = random.sample(
            self.ROOM_FEATURES.get(room_type, []),
            min(2, len(self.ROOM_FEATURES.get(room_type, ["Feature"])))
        )
        
        # Room size varies
        width = random.randint(8, 20)
        height = random.randint(8, 20)
        
        room = Room(
            id=room_id,
            name=name,
            room_type=room_type.value,
            width=width,
            height=height,
            description=description,
            features=features,
            exits=self._generate_exits()
        )
        
        # Add type-specific content
        if room_type == RoomType.COMBAT:
            room.encounters = self._generate_encounter(level)
        elif room_type == RoomType.TRAP:
            room.traps = self._generate_trap(level)
        elif room_type == RoomType.TREASURE:
            room.treasure = self._generate_treasure(level)
        elif room_type == RoomType.TRAP_TREASURE:
            room.traps = self._generate_trap(level)
            room.treasure = self._generate_treasure(level)
        elif room_type == RoomType.PUZZLE:
            room.features.append(self._generate_puzzle())
        elif room_type == RoomType.NPC:
            room.encounters = [{"type": "npc", "description": "Friendly or hostile NPC"}]
        elif room_type == RoomType.BOSS:
            room.encounters = self._generate_encounter(level, boss=True)
            room.treasure = self._generate_treasure(level, boss=True)
        
        # Secret exits chance
        if random.random() < 0.2:
            room.secret_exits = random.sample(["N", "S", "E", "W"], random.randint(1, 2))
        
        return room

    def _generate_exits(self) -> List[str]:
        """Generate room exits."""
        possible = ["N", "S", "E", "W"]
        num_exits = random.randint(1, 3)
        return random.sample(possible, num_exits)

    def _generate_encounter(self, level: int, boss: bool = False) -> List[Dict[str, Any]]:
        """Generate a combat encounter."""
        if boss:
            return [{
                "type": "boss",
                "description": f"Powerful boss monster (CR {level + 2})",
                "tactics": "Uses lair actions and legendary actions"
            }]
        
        num_enemies = random.randint(1, 4)
        return [{
            "type": "combat",
            "description": f"{num_enemies} enemies (CR {max(1, level - 1)}-{level})",
            "tactics": "Uses cover and flanking"
        }]

    def _generate_trap(self, level: int) -> List[Dict[str, Any]]:
        """Generate a trap."""
        traps = [
            {"name": "Pit Trap", "dc": 12 + level, "damage": f"{level}d6", "type": "falling"},
            {"name": "Poison Dart", "dc": 13 + level, "damage": f"{level}d4 poison", "type": "ranged"},
            {"name": "Swinging Blade", "dc": 14 + level, "damage": f"{level + 1}d8 slashing", "type": "melee"},
            {"name": "Fire Jet", "dc": 13 + level, "damage": f"{level}d6 fire", "type": "elemental"},
            {"name": "Poison Gas", "dc": 14 + level, "damage": f"{level}d6 poison", "type": "cloud"},
            {"name": "Collapsing Ceiling", "dc": 15 + level, "damage": f"{level + 2}d6 bludgeoning", "type": "environment"},
        ]
        trap = random.choice(traps)
        trap["perception_dc"] = trap["dc"] - 2
        trap["disable_dc"] = trap["dc"]
        return [trap]

    def _generate_treasure(self, level: int, boss: bool = False) -> List[Dict[str, Any]]:
        """Generate treasure."""
        if boss:
            return [{
                "type": "major",
                "gold": random.randint(500, 1000) * level,
                "items": f"1d4 magic items (rarity: rare+)",
                "gems": f"{random.randint(3, 6)} gems worth {random.randint(100, 500)} gp each"
            }]
        
        return [{
            "type": "minor",
            "gold": random.randint(50, 200) * level,
            "items": "1 magic item or scroll" if random.random() < 0.3 else "None",
            "gems": f"{random.randint(1, 4)} gems worth {random.randint(10, 100)} gp each" if random.random() < 0.5 else "None"
        }]

    def _generate_puzzle(self) -> str:
        """Generate a puzzle feature."""
        puzzles = [
            "Align the symbols to match the constellation pattern",
            "Step on pressure plates in the correct sequence",
            "Rotate the rings to form a complete image",
            "Speak the command word discovered elsewhere",
            "Place the correct offering on the altar",
            "Solve the riddle: 'I have keys but no locks...'"
        ]
        return random.choice(puzzles)

    def _connect_rooms(self, rooms: List[Room]) -> List[Tuple[int, int]]:
        """Connect rooms with corridors."""
        connections = []
        
        # Linear connection
        for i in range(len(rooms) - 1):
            connections.append((rooms[i].id, rooms[i + 1].id))
        
        # Add some branches
        if len(rooms) > 4:
            num_branches = random.randint(1, min(3, len(rooms) - 2))
            for _ in range(num_branches):
                room1 = random.choice(rooms[:-1])
                room2 = random.choice([r for r in rooms if r.id != room1.id])
                conn = (min(room1.id, room2.id), max(room1.id, room2.id))
                if conn not in connections:
                    connections.append(conn)
        
        return connections

    def _generate_backstory(self, theme: str) -> str:
        """Generate dungeon backstory."""
        backstories = {
            DungeonTheme.CRYPT: "Ancient burial grounds of a forgotten kingdom, now disturbed by grave robbers.",
            DungeonTheme.CAVE: "Natural caverns that hide secrets of the underworld.",
            DungeonTheme.CASTLE: "Once a mighty fortress, now fallen into darkness.",
            DungeonTheme.RUINS: "Remnants of an ancient civilization, lost to time.",
            DungeonTheme.TEMPLE: "Sacred grounds corrupted by unholy forces.",
        }
        return backstories.get(theme, "A mysterious place of danger and opportunity.")

    def _generate_dungeon_features(self, theme: str) -> List[str]:
        """Generate dungeon-wide features."""
        features = {
            DungeonTheme.CRYPT: ["Undead wander the halls", "Cold spots throughout", "Whispers in the dark"],
            DungeonTheme.CAVE: ["Underground streams", "Bioluminescent fungi", "Echoing chambers"],
            DungeonTheme.CASTLE: ["Portcullis gates", "Arrow slits", "Secret passages"],
            DungeonTheme.RUINS: ["Unstable floors", "Overgrown vegetation", "Collapsed sections"],
            DungeonTheme.TEMPLE: ["Holy symbols", "Prayer alcoves", "Consecrated ground"],
        }
        return features.get(theme, ["Mysterious atmosphere"])

    def _get_level_name(self, level_num: int, theme: str) -> str:
        """Generate level name."""
        names = {
            DungeonTheme.CRYPT: ["The Entry Tombs", "The Deep Crypts", "The Sarcophagus Hall", "The Bone Pits", "The Pharaoh's Chamber"],
            DungeonTheme.CAVE: ["The Entrance Cavern", "The Crystal Caves", "The Underground River", "The Deep Dark", "The Heart of Stone"],
            DungeonTheme.CASTLE: ["The Gatehouse", "The Great Hall", "The Tower Levels", "The Royal Chambers", "The Throne Room"],
            DungeonTheme.RUINS: ["The Outer Ruins", "The Collapsed Wing", "The Ancient Plaza", "The Forbidden Section", "The Inner Sanctum"],
            DungeonTheme.TEMPLE: ["The Outer Courtyard", "The Hall of Worship", "The Priest Quarters", "The Sacred Vault", "The God's Chamber"],
        }
        level_names = names.get(theme, names[DungeonTheme.CRYPT])
        return level_names[min(level_num - 1, len(level_names) - 1)]

    def _get_level_feature(self, level_num: int, theme: str) -> str:
        """Generate special level feature."""
        features = [
            "Environmental hazard: Difficult terrain throughout",
            "Magical effect: All healing reduced by half",
            "Time distortion: Rests take twice as long",
            "Guardian presence: Extra patrols",
            "Treasure trove: Additional loot in rooms",
        ]
        return random.choice(features)

    def render_ascii_map(self, dungeon: Dungeon, level_num: int = 1) -> str:
        """
        Render ASCII map of a dungeon level.
        
        Args:
            dungeon: Dungeon object
            level_num: Which level to render
            
        Returns:
            ASCII map string
        """
        if level_num > len(dungeon.levels):
            return f"Level {level_num} does not exist"
        
        level = dungeon.levels[level_num - 1]
        
        # Simple room box representation
        lines = []
        lines.append(f"=== {level.name} ===")
        lines.append(f"Difficulty: {level.difficulty}")
        lines.append(f"Feature: {level.level_feature}")
        lines.append("")
        
        # Create simple map
        room_symbols = {
            RoomType.ENTRANCE.value: "E",
            RoomType.CORRIDOR.value: "=",
            RoomType.EMPTY.value: " ",
            RoomType.COMBAT.value: "X",
            RoomType.TRAP.value: "T",
            RoomType.TREASURE.value: "$",
            RoomType.PUZZLE.value: "?",
            RoomType.NPC.value: "N",
            RoomType.BOSS.value: "B",
            RoomType.SECRET.value: "S",
            RoomType.TRAP_TREASURE.value: "!",
        }
        
        for room in level.rooms:
            symbol = room_symbols.get(room.room_type, "R")
            connections = [c[1] for c in level.connections if c[0] == room.id]
            conn_str = "".join([f"->{c}" for c in connections])
            lines.append(f"[{symbol}] {room.name} {conn_str}")
        
        lines.append("")
        lines.append("Legend: E=Entrance, X=Combat, T=Trap, $=Treasure, ?=Puzzle, N=NPC, B=Boss, S=Secret")
        
        return "\n".join(lines)

    def export_to_json(self, dungeon: Dungeon, filepath: str) -> None:
        """Export dungeon to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(dungeon.to_dict(), f, indent=2)
        logger.info(f"Dungeon exported to {filepath}")

    def export_to_markdown(self, dungeon: Dungeon, filepath: str) -> None:
        """Export dungeon to Markdown file."""
        lines = []
        lines.append(f"# {dungeon.name}")
        lines.append(f"\n**Theme:** {dungeon.theme} | **Levels:** {dungeon.total_levels}\n")
        lines.append(f"## Backstory\n\n{dungeon.backstory}\n")
        lines.append(f"## Features\n\n{', '.join(dungeon.dungeon_features)}\n")
        
        for level in dungeon.levels:
            lines.append(f"\n---\n\n## {level.name}\n")
            lines.append(f"**Difficulty:** {level.difficulty}\n")
            lines.append(f"**Feature:** {level.level_feature}\n\n")
            
            for room in level.rooms:
                lines.append(f"### {room.name}")
                lines.append(f"*Type: {room.room_type} | Size: {room.width}x{room.height}*\n")
                lines.append(f"{room.description}\n")
                
                if room.features:
                    lines.append(f"**Features:** {', '.join(room.features)}\n")
                
                if room.encounters:
                    lines.append("**Encounters:**")
                    for enc in room.encounters:
                        lines.append(f"- {enc.get('description', enc)}")
                    lines.append("")
                
                if room.traps:
                    lines.append("**Traps:**")
                    for trap in room.traps:
                        lines.append(f"- {trap.get('name', 'Trap')} (DC {trap.get('dc', 10)})")
                    lines.append("")
                
                if room.treasure:
                    lines.append("**Treasure:**")
                    for t in room.treasure:
                        lines.append(f"- Gold: {t.get('gold', 0)} gp")
                    lines.append("")
        
        with open(filepath, 'w') as f:
            f.write("\n".join(lines))
        logger.info(f"Dungeon exported to {filepath}")


def main():
    """CLI for dungeon generator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DnD Dungeon Generator v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dungeon_generator.py --theme crypt --levels 3
  python dungeon_generator.py -n "The Dark Tower" -t tower -l 5
  python dungeon_generator.py --theme castle --export dungeon.json
  python dungeon_generator.py --theme underdark --map
        """
    )
    
    parser.add_argument("-n", "--name", default="The Forgotten Dungeon",
                        help="Dungeon name")
    parser.add_argument("-t", "--theme", default="crypt",
                        choices=["crypt", "cave", "castle", "ruins", "mine", 
                                 "temple", "sewer", "tower", "underdark", "labyrinth"],
                        help="Dungeon theme")
    parser.add_argument("-l", "--levels", type=int, default=3,
                        help="Number of dungeon levels")
    parser.add_argument("-r", "--rooms", type=int, default=8,
                        help="Rooms per level")
    parser.add_argument("-d", "--difficulty", default="medium",
                        choices=["easy", "medium", "hard", "deadly"],
                        help="Dungeon difficulty")
    parser.add_argument("--export", type=str,
                        help="Export to JSON file")
    parser.add_argument("--export-md", type=str,
                        help="Export to Markdown file")
    parser.add_argument("--map", action="store_true",
                        help="Show ASCII map")
    parser.add_argument("--seed", type=int,
                        help="Random seed")
    
    args = parser.parse_args()
    
    generator = DungeonGenerator(seed=args.seed)
    
    dungeon = generator.generate_dungeon(
        name=args.name,
        theme=args.theme,
        levels=args.levels,
        rooms_per_level=args.rooms,
        difficulty=args.difficulty
    )
    
    print(f"\n=== {dungeon.name} ===")
    print(f"Theme: {dungeon.theme}")
    print(f"Levels: {dungeon.total_levels}")
    print(f"Backstory: {dungeon.backstory}")
    print(f"Features: {', '.join(dungeon.dungeon_features)}")
    
    if args.map:
        for i in range(1, min(dungeon.total_levels + 1, 4)):
            print()
            print(generator.render_ascii_map(dungeon, i))
    else:
        print(f"\nGenerated {sum(len(l.rooms) for l in dungeon.levels)} rooms across {dungeon.total_levels} levels")
    
    if args.export:
        generator.export_to_json(dungeon, args.export)
        print(f"\nExported to {args.export}")
    
    if args.export_md:
        generator.export_to_markdown(dungeon, args.export_md)
        print(f"\nExported to {args.export_md}")


if __name__ == "__main__":
    main()
