#!/usr/bin/env python3
"""
RPG Character Generator

Generate complete RPG characters with stats, equipment, inventory, and backstory.
Integrates with the DnD tools for names, NPCs, and encounters.
"""

import json
import random
import string
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import from sibling modules
try:
    from .name_gen import NameGenerator
    from .npc_gen import NPCGenerator
    from .loot_gen import LootGenerator
except ImportError:
    # Fallback if running standalone
    from name_gen import NameGenerator
    from npc_gen import NPCGenerator
    from loot_gen import LootGenerator


class RPGCharacterGenerator:
    """Generate complete RPG characters."""

    # Character classes with hit dice and primary abilities
    CLASSES = {
        "Barbarian": {"hit_die": 12, "primary": ["STR", "CON"], "saving_throws": ["STR", "CON"]},
        "Bard": {"hit_die": 8, "primary": ["CHA"], "saving_throws": ["DEX", "CHA"]},
        "Cleric": {"hit_die": 8, "primary": ["WIS"], "saving_throws": ["WIS", "CHA"]},
        "Druid": {"hit_die": 8, "primary": ["WIS"], "saving_throws": ["INT", "WIS"]},
        "Fighter": {"hit_die": 10, "primary": ["STR", "DEX"], "saving_throws": ["STR", "CON"]},
        "Monk": {"hit_die": 8, "primary": ["DEX", "WIS"], "saving_throws": ["STR", "DEX"]},
        "Paladin": {"hit_die": 10, "primary": ["STR", "CHA"], "saving_throws": ["WIS", "CHA"]},
        "Ranger": {"hit_die": 10, "primary": ["DEX", "WIS"], "saving_throws": ["STR", "DEX"]},
        "Rogue": {"hit_die": 8, "primary": ["DEX"], "saving_throws": ["DEX", "INT"]},
        "Sorcerer": {"hit_die": 6, "primary": ["CHA"], "saving_throws": ["CON", "CHA"]},
        "Warlock": {"hit_die": 8, "primary": ["CHA"], "saving_throws": ["WIS", "CHA"]},
        "Wizard": {"hit_die": 6, "primary": ["INT"], "saving_throws": ["INT", "WIS"]},
    }

    # Races with ability bonuses and traits
    RACES = {
        "Human": {"abilities": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1}, "speed": 30, "size": "Medium"},
        "Elf": {"abilities": {"DEX": 2}, "speed": 30, "size": "Medium", "traits": ["Darkvision", "Fey Ancestry"]},
        "Dwarf": {"abilities": {"CON": 2}, "speed": 25, "size": "Medium", "traits": ["Darkvision", "Dwarven Resilience"]},
        "Halfling": {"abilities": {"DEX": 2}, "speed": 25, "size": "Small", "traits": ["Lucky", "Brave"]},
        "Dragonborn": {"abilities": {"STR": 2, "CHA": 1}, "speed": 30, "size": "Medium", "traits": ["Draconic Ancestry", "Breath Weapon"]},
        "Gnome": {"abilities": {"INT": 2}, "speed": 25, "size": "Small", "traits": ["Darkvision", "Gnome Cunning"]},
        "Half-Elf": {"abilities": {"CHA": 2}, "speed": 30, "size": "Medium", "traits": ["Darkvision", "Fey Ancestry", "Skill Versatility"]},
        "Half-Orc": {"abilities": {"STR": 2, "CON": 1}, "speed": 30, "size": "Medium", "traits": ["Darkvision", "Menacing", "Relentless Endurance"]},
        "Tiefling": {"abilities": {"CHA": 2, "INT": 1}, "speed": 30, "size": "Medium", "traits": ["Darkvision", "Hellish Resistance", "Infernal Legacy"]},
    }

    # Backgrounds with skill proficiencies
    BACKGROUNDS = {
        "Acolyte": {"skills": ["Insight", "Religion"], "feature": "Shelter of the Faithful"},
        "Criminal": {"skills": ["Deception", "Stealth"], "feature": "Criminal Contact"},
        "Folk Hero": {"skills": ["Animal Handling", "Survival"], "feature": "Rustic Hospitality"},
        "Noble": {"skills": ["History", "Persuasion"], "feature": "Position of Privilege"},
        "Sage": {"skills": ["Arcana", "History"], "feature": "Researcher"},
        "Soldier": {"skills": ["Athletics", "Intimidation"], "feature": "Military Rank"},
        "Urchin": {"skills": ["Sleight of Hand", "Stealth"], "feature": "City Secrets"},
        "Sailor": {"skills": ["Athletics", "Perception"], "feature": "Ship's Passage"},
    }

    # Alignment options
    ALIGNMENTS = [
        "Lawful Good", "Neutral Good", "Chaotic Good",
        "Lawful Neutral", "True Neutral", "Chaotic Neutral",
        "Lawful Evil", "Neutral Evil", "Chaotic Evil"
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the character generator.

        Args:
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self.name_generator = NameGenerator() if NameGenerator else None
        self.npc_generator = NPCGenerator() if NPCGenerator else None
        self.loot_generator = LootGenerator() if LootGenerator else None

    def _random_id(self, length: int = 12) -> str:
        """Generate a random ID string."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _roll_ability(self, method: str = "4d6dl3") -> int:
        """
        Roll ability scores using specified method.

        Args:
            method: Rolling method ("4d6dl3", "3d6", "standard", "heroic")

        Returns:
            Ability score value
        """
        if method == "4d6dl3":
            # Roll 4d6, drop lowest
            rolls = sorted([random.randint(1, 6) for _ in range(4)])
            return sum(rolls[1:])
        elif method == "3d6":
            return sum([random.randint(1, 6) for _ in range(3)])
        elif method == "standard":
            return random.choice([13, 14, 14, 15, 15, 16])
        elif method == "heroic":
            return random.randint(10, 16)
        else:
            return self._roll_ability("4d6dl3")

    def _generate_ability_scores(self, race: str, method: str = "4d6dl3") -> Dict[str, int]:
        """
        Generate ability scores with racial bonuses.

        Args:
            race: Character race
            method: Rolling method

        Returns:
            Dict of ability scores
        """
        abilities = {
            "STR": self._roll_ability(method),
            "DEX": self._roll_ability(method),
            "CON": self._roll_ability(method),
            "INT": self._roll_ability(method),
            "WIS": self._roll_ability(method),
            "CHA": self._roll_ability(method)
        }

        # Apply racial bonuses
        if race in self.RACES:
            for ability, bonus in self.RACES[race].get("abilities", {}).items():
                abilities[ability] = abilities.get(ability, 10) + bonus

        return abilities

    def _calculate_modifiers(self, abilities: Dict[str, int]) -> Dict[str, int]:
        """Calculate ability modifiers from scores."""
        return {ability: (score - 10) // 2 for ability, score in abilities.items()}

    def _calculate_hp(self, level: int, class_name: str, con_mod: int) -> int:
        """Calculate hit points."""
        hit_die = self.CLASSES.get(class_name, {}).get("hit_die", 8)
        # First level: max hit die + CON mod
        hp = hit_die + con_mod
        # Subsequent levels: average of hit die (rounded up) + CON mod
        for _ in range(1, level):
            hp += (hit_die // 2 + 1) + con_mod
        return max(1, hp)  # Minimum 1 HP

    def _generate_backstory(self, background: str, char_class: str, race: str) -> str:
        """Generate a brief backstory."""
        backstory_templates = [
            "{name} grew up in {place}, where they learned to {skill}. Their life changed when {event}.",
            "Born to a {family} family, {name} always dreamed of {dream}. Now they seek to {goal}.",
            "After {event}, {name} took up the life of a {class_name}. They now travel to {place}.",
            "{name}'s journey began in {place}. Trained as a {class_name}, they now pursue {goal}."
        ]

        events = [
            "their village was attacked", "they discovered a hidden power",
            "a prophecy was revealed", "they lost everything",
            "they found an ancient artifact", "a mentor took them in"
        ]

        goals = [
            "revenge against their enemies", "to protect the innocent",
            "forbidden knowledge", "to restore their family's honor",
            "the truth about their past", "to become a legend"
        ]

        template = random.choice(backstory_templates)
        return template.format(
            name=self._random_name(),
            place=random.choice(["a small village", "the capital city", "the frontier", "ancient ruins"]),
            skill=random.choice(["fight", "cast spells", "sneak", "heal", "persuade"]),
            event=random.choice(events),
            family=random.choice(["noble", "common", "merchant", "military"]),
            dream=random.choice(["adventure", "power", "knowledge", "redemption"]),
            goal=random.choice(goals),
            class_name=char_class.lower()
        )

    def _random_name(self) -> str:
        """Generate a random character name."""
        if self.name_generator:
            self.name_generator.culture = "human"
            return self.name_generator.generate_name()
        prefixes = ["Aer", "Bal", "Cor", "Dar", "Eld", "Fen", "Gor", "Had", "Iri", "Jor"]
        suffixes = ["ion", "us", "as", "os", "is", "th", "gar", "dor", "mar", "wyn"]
        return random.choice(prefixes) + random.choice(suffixes)

    def generate_character(self, level: int = 1,
                           char_class: Optional[str] = None,
                           race: Optional[str] = None,
                           background: Optional[str] = None,
                           gender: Optional[str] = None,
                           name: Optional[str] = None,
                           ability_method: str = "4d6dl3",
                           seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a complete character.

        Args:
            level: Character level (1-20)
            char_class: Character class (random if None)
            race: Character race (random if None)
            background: Character background (random if None)
            gender: Character gender (random if None)
            name: Character name (random if None)
            ability_method: Ability rolling method
            seed: Optional random seed

        Returns:
            Complete character dict
        """
        if seed is not None:
            random.seed(seed)

        # Random selections if not specified
        if char_class is None:
            char_class = random.choice(list(self.CLASSES.keys()))
        if race is None:
            race = random.choice(list(self.RACES.keys()))
        if background is None:
            background = random.choice(list(self.BACKGROUNDS.keys()))
        if gender is None:
            gender = random.choice(["Male", "Female", "Non-binary"])
        if name is None:
            name = self._random_name()

        # Generate ability scores
        abilities = self._generate_ability_scores(race, ability_method)
        modifiers = self._calculate_modifiers(abilities)

        # Calculate HP
        hp = self._calculate_hp(level, char_class, modifiers.get("CON", 0))

        # Get class info
        class_info = self.CLASSES.get(char_class, {})
        race_info = self.RACES.get(race, {})
        bg_info = self.BACKGROUNDS.get(background, {})

        # Build character
        character = {
            "_meta": {
                "schemaVersion": "1.0.0",
                "templateVersion": "1.0.0",
                "createdAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "generator": "rpg_character_gen"
            },
            "identity": {
                "id": self._random_id(),
                "name": name,
                "class": char_class,
                "subclass": "",
                "race": race,
                "subrace": "",
                "gender": gender,
                "age": random.randint(18, 50) if race == "Human" else random.randint(20, 200),
                "alignment": random.choice(self.ALIGNMENTS),
                "deity": "",
                "background": background,
                "level": level,
                "experience": 0,
                "proficiencyBonus": 2 + (level - 1) // 4
            },
            "abilities": {
                "scores": abilities,
                "modifiers": modifiers,
                "saving_throws": class_info.get("saving_throws", [])
            },
            "combat": {
                "hp": {"current": hp, "maximum": hp, "temporary": 0},
                "ac": 10 + modifiers.get("DEX", 0),  # Base AC
                "initiative": modifiers.get("DEX", 0),
                "speed": race_info.get("speed", 30),
                "hitDice": {"total": level, "used": 0, "die": f"1d{class_info.get('hit_die', 8)}"},
                "deathSaves": {"success": 0, "failure": 0}
            },
            "proficiencies": {
                "armor": [],
                "weapons": [],
                "tools": [],
                "skills": bg_info.get("skills", [])[:2] if bg_info else []
            },
            "features": {
                "class_features": [],
                "racial_traits": race_info.get("traits", []),
                "background_feature": bg_info.get("feature", "")
            },
            "equipment": {
                "weapons": [],
                "armor": [],
                "inventory": [],
                "currency": {
                    "pp": 0, "gp": random.randint(5, 20) * level,
                    "ep": 0, "sp": random.randint(10, 50), "cp": random.randint(50, 200)
                }
            },
            "backstory": self._generate_backstory(background, char_class, race),
            "appearance": {
                "height": round(random.uniform(1.5, 2.0), 2),
                "weight": round(random.uniform(50, 100), 1),
                "eyes": random.choice(["Brown", "Blue", "Green", "Hazel", "Gray", "Amber"]),
                "hair": random.choice(["Black", "Brown", "Blonde", "Red", "Gray", "White"]),
                "skin": random.choice(["Fair", "Tan", "Dark", "Pale", "Olive"])
            }
        }

        # Add starting equipment based on class
        character["equipment"] = self._generate_starting_equipment(char_class, level)

        return character

    def _generate_starting_equipment(self, char_class: str, level: int) -> Dict[str, Any]:
        """Generate starting equipment for a character."""
        equipment = {
            "weapons": [],
            "armor": [],
            "inventory": [],
            "currency": {
                "pp": 0, "gp": random.randint(5, 20) * level,
                "ep": 0, "sp": random.randint(10, 50), "cp": random.randint(50, 200)
            }
        }

        # Class-based starting equipment
        class_equipment = {
            "Fighter": {"weapons": ["Longsword", "Shield"], "armor": ["Chain Mail"]},
            "Wizard": {"weapons": ["Dagger", "Quarterstaff"], "armor": []},
            "Rogue": {"weapons": ["Rapier", "Dagger"], "armor": ["Leather Armor"]},
            "Cleric": {"weapons": ["Mace"], "armor": ["Scale Mail"]},
            "Barbarian": {"weapons": ["Greataxe", "Handaxe"], "armor": []},
            "Ranger": {"weapons": ["Longbow", "Shortsword"], "armor": ["Leather Armor"]},
            "Paladin": {"weapons": ["Longsword"], "armor": ["Chain Mail"]},
            "Druid": {"weapons": ["Staff"], "armor": ["Leather Armor"]},
            "Bard": {"weapons": ["Rapier"], "armor": ["Leather Armor"]},
            "Sorcerer": {"weapons": ["Dagger"], "armor": []},
            "Warlock": {"weapons": ["Light Crossbow"], "armor": []},
            "Monk": {"weapons": ["Shortsword", "Dagger"], "armor": []},
        }

        eq = class_equipment.get(char_class, {"weapons": ["Club"], "armor": []})
        equipment["weapons"] = eq.get("weapons", [])
        equipment["armor"] = eq.get("armor", [])
        equipment["inventory"] = [
            "Backpack", "Bedroll", "Rations (5 days)", "Waterskin",
            "Rope (50 ft)", "Torch", "Flint and Steel"
        ]

        return equipment

    def generate_party(self, party_size: int = 4,
                       level: int = 1,
                       seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate a complete adventuring party.

        Args:
            party_size: Number of characters
            level: Party level
            seed: Optional random seed

        Returns:
            List of character dicts
        """
        if seed is not None:
            random.seed(seed)

        # Ensure class diversity
        classes = list(self.CLASSES.keys())
        selected_classes = random.sample(classes, min(party_size, len(classes)))

        party = []
        for i in range(party_size):
            char_class = selected_classes[i % len(selected_classes)]
            character = self.generate_character(
                level=level,
                char_class=char_class,
                seed=seed + i if seed else None
            )
            party.append(character)

        return party

    def export_to_json(self, character: Dict[str, Any], filepath: str) -> None:
        """
        Export character to JSON file.

        Args:
            character: Character dict
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump(character, f, indent=2)

    def export_party_to_json(self, party: List[Dict[str, Any]], filepath: str) -> None:
        """
        Export party to JSON file.

        Args:
            party: List of character dicts
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump({"party": party, "party_size": len(party)}, f, indent=2)


def main():
    """CLI for the RPG character generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="RPG Character Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rpg_char_gen.py -l 5 -c Wizard -r Human
  python rpg_char_gen.py --party 4 -l 3 -o party.json
  python rpg_char_gen.py --ability-method heroic
  python rpg_char_gen.py --list-classes
        """
    )

    parser.add_argument("-l", "--level", type=int, default=1,
                        help="Character level (1-20)")
    parser.add_argument("-c", "--class", dest="char_class",
                        choices=list(RPGCharacterGenerator.CLASSES.keys()),
                        help="Character class")
    parser.add_argument("-r", "--race",
                        choices=list(RPGCharacterGenerator.RACES.keys()),
                        help="Character race")
    parser.add_argument("-b", "--background",
                        choices=list(RPGCharacterGenerator.BACKGROUNDS.keys()),
                        help="Character background")
    parser.add_argument("--gender", choices=["Male", "Female", "Non-binary"],
                        help="Character gender")
    parser.add_argument("-n", "--name", help="Character name")
    parser.add_argument("--ability-method", default="4d6dl3",
                        choices=["4d6dl3", "3d6", "standard", "heroic"],
                        help="Ability score generation method")
    parser.add_argument("--party", type=int, help="Generate a party of N characters")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--list-classes", action="store_true",
                        help="List available classes")
    parser.add_argument("--list-races", action="store_true",
                        help="List available races")
    parser.add_argument("--seed", type=int, help="Random seed")

    args = parser.parse_args()

    generator = RPGCharacterGenerator(seed=args.seed)

    if args.list_classes:
        print("Available Classes:")
        for cls, info in generator.CLASSES.items():
            print(f"  {cls}: HD d{info['hit_die']}, Primary: {', '.join(info['primary'])}")
        return

    if args.list_races:
        print("Available Races:")
        for race, info in generator.RACES.items():
            abilities = ', '.join(f"{k}+{v}" for k, v in info.get('abilities', {}).items())
            print(f"  {race}: {abilities}, Speed: {info.get('speed', 30)}")
        return

    if args.party:
        party = generator.generate_party(party_size=args.party, level=args.level)
        if args.output:
            generator.export_party_to_json(party, args.output)
            print(f"Party exported to {args.output}")
        else:
            print(f"=== Adventuring Party (Level {args.level}) ===\n")
            for i, char in enumerate(party, 1):
                print(f"{i}. {char['identity']['name']} - {char['identity']['race']} {char['identity']['class']}")
                print(f"   Level {char['identity']['level']}, HP: {char['combat']['hp']['maximum']}, AC: {char['combat']['ac']}")
                print(f"   Abilities: STR {char['abilities']['scores']['STR']}, DEX {char['abilities']['scores']['DEX']}, CON {char['abilities']['scores']['CON']}, INT {char['abilities']['scores']['INT']}, WIS {char['abilities']['scores']['WIS']}, CHA {char['abilities']['scores']['CHA']}")
                print()
    else:
        character = generator.generate_character(
            level=args.level,
            char_class=args.char_class,
            race=args.race,
            background=args.background,
            gender=args.gender,
            name=args.name,
            ability_method=args.ability_method
        )

        if args.output:
            generator.export_to_json(character, args.output)
            print(f"Character exported to {args.output}")
        else:
            print(f"=== {character['identity']['name']} ===")
            print(f"Level {character['identity']['level']} {character['identity']['race']} {character['identity']['class']}")
            print(f"Background: {character['identity']['background']}")
            print(f"Alignment: {character['identity']['alignment']}")
            print(f"\nAbility Scores:")
            for ability, score in character['abilities']['scores'].items():
                mod = character['abilities']['modifiers'][ability]
                print(f"  {ability}: {score} ({mod:+d})")
            print(f"\nCombat:")
            print(f"  HP: {character['combat']['hp']['maximum']}")
            print(f"  AC: {character['combat']['ac']}")
            print(f"  Initiative: {character['combat']['initiative']:+d}")
            print(f"  Speed: {character['combat']['speed']} ft")
            print(f"\nEquipment:")
            print(f"  Weapons: {', '.join(character['equipment']['weapons'])}")
            print(f"  Armor: {', '.join(character['equipment']['armor']) if character['equipment']['armor'] else 'None'}")
            print(f"  Gold: {character['equipment']['currency']['gp']} gp")
            print(f"\nBackstory:")
            print(f"  {character['backstory']}")


if __name__ == "__main__":
    main()
