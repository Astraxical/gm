#!/usr/bin/env python3
"""
DnD NPC Generator v2.0

Generate complete NPCs with names, appearance, personality, quirks, secrets,
stat blocks, relationships, and inventory.
Integrates with name generator for cultural naming.
"""

import random
from typing import Dict, Optional, List, Any
from pathlib import Path

# Import from sibling modules
try:
    from name_gen import NameGenerator
except ImportError:
    NameGenerator = None


class NPCGenerator:
    """Generate complete DnD NPCs with stat blocks and relationships."""

    # Race-specific data with ability bonuses
    RACES = {
        "human": {"abilities": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1}, "speed": 30, "size": "Medium", "lifespan": "80 years", "culture": "human"},
        "elf": {"abilities": {"DEX": 2}, "speed": 30, "size": "Medium", "lifespan": "700+ years", "culture": "elvish", "traits": ["Darkvision", "Fey Ancestry"]},
        "high_elf": {"abilities": {"DEX": 2, "INT": 1}, "speed": 30, "size": "Medium", "lifespan": "700+ years", "culture": "elvish", "traits": ["Darkvision", "Cantrip"]},
        "wood_elf": {"abilities": {"DEX": 2, "WIS": 1}, "speed": 35, "size": "Medium", "lifespan": "700+ years", "culture": "elvish", "traits": ["Darkvision", "Mask of the Wild"]},
        "dwarf": {"abilities": {"CON": 2}, "speed": 25, "size": "Medium", "lifespan": "350 years", "culture": "dwarvish", "traits": ["Darkvision", "Dwarven Resilience"]},
        "hill_dwarf": {"abilities": {"CON": 2, "WIS": 1}, "speed": 25, "size": "Medium", "lifespan": "350 years", "culture": "dwarvish", "traits": ["Darkvision", "Dwarven Toughness"]},
        "mountain_dwarf": {"abilities": {"CON": 2, "STR": 2}, "speed": 25, "size": "Medium", "lifespan": "350 years", "culture": "dwarvish", "traits": ["Darkvision", "Armor Proficiency"]},
        "halfling": {"abilities": {"DEX": 2}, "speed": 25, "size": "Small", "lifespan": "150 years", "culture": "halfling", "traits": ["Lucky", "Brave"]},
        "lightfoot_halfling": {"abilities": {"DEX": 2, "CHA": 1}, "speed": 25, "size": "Small", "lifespan": "150 years", "culture": "halfling", "traits": ["Lucky", "Naturally Stealthy"]},
        "stout_halfling": {"abilities": {"DEX": 2, "CON": 1}, "speed": 25, "size": "Small", "lifespan": "150 years", "culture": "halfling", "traits": ["Lucky", "Stout Resilience"]},
        "gnome": {"abilities": {"INT": 2}, "speed": 25, "size": "Small", "lifespan": "400 years", "culture": "gnomish", "traits": ["Darkvision", "Gnome Cunning"]},
        "half_orc": {"abilities": {"STR": 2, "CON": 1}, "speed": 30, "size": "Medium", "lifespan": "75 years", "culture": "orcish", "traits": ["Darkvision", "Relentless Endurance"]},
        "tiefling": {"abilities": {"CHA": 2, "INT": 1}, "speed": 30, "size": "Medium", "lifespan": "100 years", "culture": "human", "traits": ["Darkvision", "Hellish Resistance"]},
        "dragonborn": {"abilities": {"STR": 2, "CHA": 1}, "speed": 30, "size": "Medium", "lifespan": "80 years", "culture": "draconic", "traits": ["Draconic Ancestry", "Breath Weapon"]},
        "orc": {"abilities": {"STR": 2, "CON": 1, "INT": -2}, "speed": 30, "size": "Medium", "lifespan": "50 years", "culture": "orcish", "traits": ["Aggressive", "Menacing"]},
        "goblin": {"abilities": {"DEX": 2, "CON": 1, "STR": -2}, "speed": 30, "size": "Small", "lifespan": "40 years", "culture": "goblin", "traits": ["Nimble Escape", "Fury of the Small"]},
        "kobold": {"abilities": {"DEX": 2, "STR": -2}, "speed": 30, "size": "Small", "lifespan": "120 years", "culture": "draconic", "traits": ["Pack Tactics", "Sunlight Sensitivity"]},
    }

    # Class templates with stat blocks
    CLASSES = {
        "fighter": {
            "hit_die": 10, "proficiencies": ["all armor", "shields", "simple weapons", "martial weapons"],
            "saving_throws": ["STR", "CON"], "skills": ["Athletics", "Intimidation", "Acrobatics"],
            "features": ["Fighting Style", "Second Wind", "Action Surge"]
        },
        "wizard": {
            "hit_die": 6, "proficiencies": ["daggers", "darts", "slings", "quarterstaffs", "light crossbows"],
            "saving_throws": ["INT", "WIS"], "skills": ["Arcana", "History", "Investigation"],
            "features": ["Spellcasting", "Arcane Recovery", "Spellbook"]
        },
        "rogue": {
            "hit_die": 8, "proficiencies": ["light armor", "simple weapons", "hand crossbows", "longswords", "rapiers", "shortswords"],
            "saving_throws": ["DEX", "INT"], "skills": ["Stealth", "Sleight of Hand", "Acrobatics"],
            "features": ["Sneak Attack", "Thieves' Cant", "Cunning Action"]
        },
        "cleric": {
            "hit_die": 8, "proficiencies": ["light armor", "medium armor", "shields", "simple weapons"],
            "saving_throws": ["WIS", "CHA"], "skills": ["History", "Insight", "Medicine"],
            "features": ["Spellcasting", "Divine Domain", "Channel Divinity"]
        },
        "barbarian": {
            "hit_die": 12, "proficiencies": ["light armor", "medium armor", "shields", "simple weapons", "martial weapons"],
            "saving_throws": ["STR", "CON"], "skills": ["Athletics", "Intimidation", "Survival"],
            "features": ["Rage", "Unarmored Defense", "Reckless Attack"]
        },
        "paladin": {
            "hit_die": 10, "proficiencies": ["all armor", "shields", "simple weapons", "martial weapons"],
            "saving_throws": ["WIS", "CHA"], "skills": ["Athletics", "Insight", "Persuasion"],
            "features": ["Divine Sense", "Lay on Hands", "Fighting Style"]
        },
        "ranger": {
            "hit_die": 10, "proficiencies": ["light armor", "medium armor", "shields", "simple weapons", "martial weapons"],
            "saving_throws": ["STR", "DEX"], "skills": ["Animal Handling", "Nature", "Perception"],
            "features": ["Favored Enemy", "Natural Explorer", "Fighting Style"]
        },
        "bard": {
            "hit_die": 8, "proficiencies": ["light armor", "simple weapons", "hand crossbows", "longswords", "rapiers", "shortswords"],
            "saving_throws": ["DEX", "CHA"], "skills": ["Performance", "Persuasion", "Stealth"],
            "features": ["Spellcasting", "Bardic Inspiration", "Jack of All Trades"]
        },
        "druid": {
            "hit_die": 8, "proficiencies": ["light armor", "medium armor", "shields", "clubs", "daggers", "darts", "javelins", "maces", "quarterstaffs", "scimitars", "sickles", "slings", "spears"],
            "saving_throws": ["INT", "WIS"], "skills": ["Animal Handling", "Medicine", "Nature"],
            "features": ["Spellcasting", "Druidic", "Wild Shape"]
        },
        "sorcerer": {
            "hit_die": 6, "proficiencies": ["daggers", "darts", "slings", "quarterstaffs", "light crossbows"],
            "saving_throws": ["CON", "CHA"], "skills": ["Arcana", "Persuasion", "Deception"],
            "features": ["Spellcasting", "Sorcerous Origin", "Font of Magic"]
        },
        "warlock": {
            "hit_die": 8, "proficiencies": ["light armor", "simple weapons"],
            "saving_throws": ["WIS", "CHA"], "skills": ["Arcana", "Deception", "Investigation"],
            "features": ["Otherworldly Patron", "Pact Magic", "Eldritch Invocations"]
        },
        "monk": {
            "hit_die": 8, "proficiencies": ["simple weapons", "shortswords", "artisan's tools"],
            "saving_throws": ["STR", "DEX"], "skills": ["Acrobatics", "Athletics", "Stealth"],
            "features": ["Unarmored Defense", "Martial Arts", "Ki"]
        },
        "commoner": {
            "hit_die": 6, "proficiencies": ["simple weapons"],
            "saving_throws": [], "skills": [],
            "features": []
        }
    }

    # Backgrounds with skill proficiencies and features
    BACKGROUNDS = {
        "acolyte": {"skills": ["Insight", "Religion"], "feature": "Shelter of the Faithful", "languages": 2},
        "charlatan": {"skills": ["Deception", "Sleight of Hand"], "feature": "False Identity", "languages": 0},
        "criminal": {"skills": ["Deception", "Stealth"], "feature": "Criminal Contact", "languages": 0},
        "entertainer": {"skills": ["Acrobatics", "Performance"], "feature": "By Popular Demand", "languages": 0},
        "folk_hero": {"skills": ["Animal Handling", "Survival"], "feature": "Rustic Hospitality", "languages": 0},
        "guild_artisan": {"skills": ["Insight", "Persuasion"], "feature": "Guild Membership", "languages": 2},
        "hermit": {"skills": ["Medicine", "Religion"], "feature": "Discovery", "languages": 1},
        "noble": {"skills": ["History", "Persuasion"], "feature": "Position of Privilege", "languages": 1},
        "outlander": {"skills": ["Athletics", "Survival"], "feature": "Wanderer", "languages": 1},
        "sage": {"skills": ["Arcana", "History"], "feature": "Researcher", "languages": 2},
        "sailor": {"skills": ["Athletics", "Perception"], "feature": "Ship's Passage", "languages": 0},
        "soldier": {"skills": ["Athletics", "Intimidation"], "feature": "Military Rank", "languages": 0},
        "urchin": {"skills": ["Sleight of Hand", "Stealth"], "feature": "City Secrets", "languages": 0},
    }

    # Alignment options
    ALIGNMENTS = [
        "Lawful Good", "Neutral Good", "Chaotic Good",
        "Lawful Neutral", "True Neutral", "Chaotic Neutral",
        "Lawful Evil", "Neutral Evil", "Chaotic Evil"
    ]

    # Relationship types
    RELATIONSHIP_TYPES = [
        "ally", "friend", "contact", "patron", "rival", "enemy", "mentor",
        "student", "family", "lover", "rival_lover", "business_partner",
        "debt_or", "debtor", "secret_admirer", "blackmailer"
    ]

    # Factions
    FACTIONS = [
        "Harpers", "Order of the Gauntlet", "Emerald Enclave",
        "Lords' Alliance", "Zhentarim", "Red Wizards",
        "Cult of the Dragon", "Firebreathing Kittens", "Independent"
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the NPC generator.

        Args:
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self.name_generator = NameGenerator() if NameGenerator else None
        self.data_dir = Path(__file__).parent / "data"

    def _random_id(self, length: int = 12) -> str:
        """Generate a random ID string."""
        import string
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _roll_ability(self, method: str = "4d6dl3") -> int:
        """Roll ability scores using specified method."""
        if method == "4d6dl3":
            rolls = sorted([random.randint(1, 6) for _ in range(4)])
            return sum(rolls[1:])
        elif method == "3d6":
            return sum([random.randint(1, 6) for _ in range(3)])
        elif method == "standard":
            return random.choice([13, 14, 14, 15, 15, 16])
        return self._roll_ability("4d6dl3")

    def _generate_ability_scores(self, race: str, class_name: str,
                                  level: int = 1, method: str = "4d6dl3") -> Dict[str, int]:
        """Generate ability scores with racial bonuses."""
        # Base scores
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

        # Apply level-based improvements
        if level >= 4:
            # Add +2 to primary ability
            class_data = self.CLASSES.get(class_name, {})
            primary = self._get_primary_ability(class_name)
            abilities[primary] = abilities.get(primary, 10) + 2

        return abilities

    def _get_primary_ability(self, class_name: str) -> str:
        """Get the primary ability for a class."""
        primary_abilities = {
            "fighter": "STR", "barbarian": "STR", "paladin": "STR",
            "wizard": "INT", "rogue": "DEX", "ranger": "DEX",
            "cleric": "WIS", "druid": "WIS", "monk": "DEX",
            "bard": "CHA", "sorcerer": "CHA", "warlock": "CHA",
            "commoner": "CON"
        }
        return primary_abilities.get(class_name.lower(), "STR")

    def _calculate_modifiers(self, abilities: Dict[str, int]) -> Dict[str, int]:
        """Calculate ability modifiers from scores."""
        return {ability: (score - 10) // 2 for ability, score in abilities.items()}

    def _calculate_hp(self, level: int, class_name: str, con_mod: int) -> int:
        """Calculate hit points."""
        class_data = self.CLASSES.get(class_name, self.CLASSES["commoner"])
        hit_die = class_data.get("hit_die", 6)
        
        # First level: max hit die + CON mod
        hp = hit_die + con_mod
        # Subsequent levels: average of hit die (rounded up) + CON mod
        for _ in range(1, level):
            hp += (hit_die // 2 + 1) + con_mod
        
        return max(1, hp)

    def _generate_stat_block(self, level: int, class_name: str,
                              abilities: Dict[str, int],
                              modifiers: Dict[str, int]) -> Dict[str, Any]:
        """Generate a DnD 5e-style stat block."""
        class_data = self.CLASSES.get(class_name, self.CLASSES["commoner"])
        
        return {
            "level": level,
            "class": class_name,
            "hit_die": class_data.get("hit_die", 6),
            "armor_class": 10 + modifiers.get("DEX", 0),
            "hit_points": self._calculate_hp(level, class_name, modifiers.get("CON", 0)),
            "speed": 30,
            "ability_scores": abilities,
            "modifiers": modifiers,
            "saving_throws": class_data.get("saving_throws", []),
            "proficiencies": class_data.get("proficiencies", []),
            "skills": class_data.get("skills", [])[:2],
            "features": class_data.get("features", [])[:level],
            "actions": self._generate_actions(class_name, level, modifiers),
            "reactions": self._generate_reactions(class_name, level),
            "legendary_actions": [] if level < 10 else self._generate_legendary_actions(class_name)
        }

    def _generate_actions(self, class_name: str, level: int,
                          modifiers: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate combat actions for the NPC."""
        actions = []
        mod_bonus = max(modifiers.get("STR", 0), modifiers.get("DEX", 0))
        prof_bonus = 2 + (level - 1) // 4
        
        if class_name in ["fighter", "paladin", "barbarian", "ranger"]:
            actions.append({
                "name": "Weapon Attack",
                "bonus": prof_bonus + mod_bonus,
                "damage": f"1d8 + {mod_bonus}",
                "description": "Melee or ranged weapon attack"
            })
        elif class_name in ["wizard", "sorcerer", "warlock", "cleric", "druid", "bard"]:
            spell_mod = modifiers.get(self._get_primary_ability(class_name), 0)
            actions.append({
                "name": "Spell Attack",
                "bonus": prof_bonus + spell_mod,
                "damage": f"2d6 + {spell_mod}",
                "description": "Magical attack"
            })
        elif class_name == "rogue":
            sneak_attack = f"{(level // 2 + 1)}d6" if level >= 1 else "1d6"
            actions.append({
                "name": "Sneak Attack",
                "bonus": prof_bonus + mod_bonus,
                "damage": f"1d6 + {mod_bonus} + {sneak_attack} (if advantaged)",
                "description": "Finesse or ranged weapon"
            })
        else:
            actions.append({
                "name": "Unarmed Strike",
                "bonus": prof_bonus + mod_bonus,
                "damage": f"1d4 + {mod_bonus}",
                "description": "Melee attack"
            })
        
        return actions

    def _generate_reactions(self, class_name: str, level: int) -> List[Dict[str, Any]]:
        """Generate reactions for the NPC."""
        reactions = []
        
        if class_name == "fighter" and level >= 10:
            reactions.append({
                "name": "Parry",
                "trigger": "Hit by melee attack",
                "effect": "+2 AC"
            })
        elif class_name == "rogue" and level >= 2:
            reactions.append({
                "name": "Uncanny Dodge",
                "trigger": "Hit by attack",
                "effect": "Half damage"
            })
        
        return reactions

    def _generate_legendary_actions(self, class_name: str) -> List[Dict[str, Any]]:
        """Generate legendary actions for high-level NPCs."""
        return [
            {"name": "Detect", "description": "Make a Perception check"},
            {"name": "Command", "description": "Give an order to an ally"},
            {"name": "Attack", "description": "Make one weapon attack"}
        ]

    def _generate_inventory(self, class_name: str, level: int,
                            background: str) -> Dict[str, Any]:
        """Generate NPC inventory and equipment."""
        inventory = {
            "weapons": [],
            "armor": [],
            "equipment": [],
            "currency": {
                "pp": 0,
                "gp": random.randint(5, 50) * level,
                "ep": 0,
                "sp": random.randint(10, 100),
                "cp": random.randint(50, 200)
            },
            "magic_items": []
        }

        # Class-based equipment
        if class_name in ["fighter", "paladin", "barbarian", "ranger"]:
            inventory["weapons"] = ["Longsword", "Shield", "Handaxe"]
            inventory["armor"] = ["Chain Mail"]
        elif class_name == "rogue":
            inventory["weapons"] = ["Rapier", "Dagger", "Shortbow"]
            inventory["armor"] = ["Leather Armor"]
        elif class_name in ["wizard", "sorcerer", "warlock"]:
            inventory["weapons"] = ["Dagger", "Quarterstaff"]
            inventory["armor"] = []
            inventory["equipment"] = ["Spellbook", "Component Pouch"]
        elif class_name in ["cleric", "druid"]:
            inventory["weapons"] = ["Mace", "Shield"]
            inventory["armor"] = ["Scale Mail"]
        else:
            inventory["weapons"] = ["Club"]
            inventory["armor"] = []

        # Background equipment
        inventory["equipment"].extend(["Backpack", "Bedroll", "Rations (5 days)", "Waterskin"])

        # Add magic items for higher levels
        if level >= 5 and random.random() < 0.3:
            inventory["magic_items"].append({
                "name": f"Potion of Healing",
                "quantity": random.randint(1, 3)
            })
        if level >= 10 and random.random() < 0.2:
            inventory["magic_items"].append({
                "name": random.choice(["Ring of Protection", "Cloak of Protection", "Weapon +1"]),
                "quantity": 1
            })

        return inventory

    def _generate_relationships(self, npc_name: str, faction: str,
                                 num_relationships: int = 3) -> List[Dict[str, Any]]:
        """Generate NPC relationships."""
        relationships = []
        
        for _ in range(num_relationships):
            rel_type = random.choice(self.RELATIONSHIP_TYPES)
            relationships.append({
                "type": rel_type,
                "npc_name": self._random_name(),
                "description": self._get_relationship_description(rel_type),
                "strength": random.randint(1, 10),
                "known_to_npc": random.choice([True, False])
            })
        
        return relationships

    def _get_relationship_description(self, rel_type: str) -> str:
        """Get a description for a relationship type."""
        descriptions = {
            "ally": "Will fight alongside the NPC",
            "friend": "Trusted companion",
            "contact": "Source of information",
            "patron": "Provides resources or employment",
            "rival": "Competes for the same goals",
            "enemy": "Actively hostile",
            "mentor": "Teaches and guides",
            "student": "Learns from the NPC",
            "family": "Blood relation",
            "lover": "Romantic involvement",
            "rival_lover": "Competes for someone's affection",
            "business_partner": "Shared commercial interests",
            "debt_or": "Owes a favor",
            "debtor": "Is owed a favor",
            "secret_admirer": "Admires from afar",
            "blackmailer": "Has compromising information"
        }
        return descriptions.get(rel_type, "Unknown relationship")

    def _random_name(self) -> str:
        """Generate a random character name."""
        if self.name_generator:
            self.name_generator.culture = "human"
            return self.name_generator.generate_name()
        prefixes = ["Aer", "Bal", "Cor", "Dar", "Eld", "Fen", "Gor", "Had", "Iri", "Jor"]
        suffixes = ["ion", "us", "as", "os", "is", "th", "gar", "dor", "mar", "wyn"]
        return random.choice(prefixes) + random.choice(suffixes)

    def generate_npc(self, race: str = "human",
                     class_name: str = "commoner",
                     level: int = 1,
                     background: Optional[str] = None,
                     gender: Optional[str] = None,
                     name: Optional[str] = None,
                     faction: Optional[str] = None,
                     include_stat_block: bool = True,
                     include_relationships: bool = True,
                     include_inventory: bool = True,
                     seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a complete NPC with stat block, relationships, and inventory.

        Args:
            race: Character race
            class_name: Character class
            level: Character level
            background: Character background
            gender: Character gender
            name: Character name
            faction: Faction affiliation
            include_stat_block: Include DnD stat block
            include_relationships: Include relationship web
            include_inventory: Include equipment and currency
            seed: Optional random seed

        Returns:
            Complete NPC dict
        """
        if seed is not None:
            random.seed(seed)

        # Random selections if not specified
        if background is None:
            background = random.choice(list(self.BACKGROUNDS.keys()))
        if gender is None:
            gender = random.choice(["Male", "Female", "Non-binary"])
        if name is None:
            name = self._random_name()
        if faction is None:
            faction = random.choice(self.FACTIONS)

        # Generate ability scores
        abilities = self._generate_ability_scores(race, class_name, level)
        modifiers = self._calculate_modifiers(abilities)

        # Build NPC
        npc = {
            "_meta": {
                "schemaVersion": "2.0.0",
                "createdAt": __import__('datetime').datetime.now().isoformat(),
                "generator": "npc_gen v2.0"
            },
            "identity": {
                "id": self._random_id(),
                "name": name,
                "race": race,
                "class": class_name,
                "level": level,
                "background": background,
                "gender": gender,
                "alignment": random.choice(self.ALIGNMENTS),
                "faction": faction,
                "age": self._generate_age(race),
                "appearance": self._generate_appearance(),
                "personality": self._generate_personality(),
                "voice": self._generate_voice(),
                "backstory": self._generate_backstory(name, class_name, background)
            }
        }

        # Add stat block
        if include_stat_block:
            npc["stat_block"] = self._generate_stat_block(level, class_name, abilities, modifiers)

        # Add inventory
        if include_inventory:
            npc["inventory"] = self._generate_inventory(class_name, level, background)

        # Add relationships
        if include_relationships:
            npc["relationships"] = self._generate_relationships(name, faction)
            npc["secret"] = self._generate_secret()

        # Add description
        npc["description"] = self._generate_full_description(npc)

        return npc

    def _generate_age(self, race: str) -> Dict[str, Any]:
        """Generate age details based on race."""
        race_data = self.RACES.get(race, self.RACES["human"])
        lifespan = race_data.get("lifespan", "80 years")
        
        # Parse max age
        max_age = 80
        if "+" in lifespan:
            max_age = int(lifespan.split("+")[0])
        elif lifespan.isdigit():
            max_age = int(lifespan)
        
        age = random.randint(18, max_age)
        
        if age < max_age * 0.2:
            stage = "young"
        elif age < max_age * 0.6:
            stage = "adult"
        else:
            stage = "elderly"

        return {"years": age, "stage": stage, "lifespan": lifespan}

    def _generate_appearance(self) -> Dict[str, str]:
        """Generate physical appearance details."""
        return {
            "build": random.choice(["slender", "athletic", "stocky", "gaunt", "portly", "muscular", "frail", "imposing"]),
            "complexion": random.choice(["pale", "sun-kissed", "weathered", "ruddy", "olive", "dark", "bronzed"]),
            "eyes": random.choice(["piercing blue", "warm brown", "mysterious gray", "vibrant green", "amber", "hazel"]),
            "hair": random.choice(["flowing blonde", "jet black", "fiery red", "chestnut brown", "silver", "white"]),
            "distinguishing_feature": random.choice([
                "a prominent scar", "an unusual tattoo", "a missing finger",
                "a birthmark", "unusually long ears", "a crooked nose",
                "piercing eyes", "a limp", "intricate braided beard"
            ])
        }

    def _generate_personality(self) -> Dict[str, str]:
        """Generate personality details."""
        return {
            "trait": random.choice(["brave", "cautious", "warm", "cold", "cheerful", "cynical", "proud", "humble"]),
            "ideal": random.choice(["justice", "freedom", "knowledge", "protection", "wealth", "order"]),
            "flaw": random.choice(["trusts too easily", "trusts no one", "greedy", "holds grudges", "cowardly"]),
            "mannerism": random.choice(["strokes beard", "paces", "avoids eye contact", "speaks in riddles"])
        }

    def _generate_voice(self) -> Dict[str, str]:
        """Generate voice details."""
        return {
            "tone": random.choice(["deep", "high", "soft", "gravelly", "smooth", "nasal"]),
            "pace": random.choice(["rapid", "slow", "measured", "erratic"]),
            "vocabulary": random.choice(["simple", "eloquent", "technical", "slang"])
        }

    def _generate_backstory(self, name: str, class_name: str, background: str) -> str:
        """Generate a brief backstory."""
        templates = [
            "{name} grew up as a {background}, learning to {skill}. Their life changed when {event}.",
            "Born to a {family} family, {name} always dreamed of {dream}. Now they work as a {class_name}.",
            "After {event}, {name} took up the life of a {class_name}. They now pursue {dream}."
        ]
        
        events = ["their village was attacked", "they discovered a hidden power",
                  "a prophecy was revealed", "they lost everything"]
        dreams = ["revenge", "to protect the innocent", "forbidden knowledge", "glory"]
        skills = ["fight", "cast spells", "sneak", "heal", "persuade"]
        families = ["noble", "common", "merchant", "military"]
        
        template = random.choice(templates)
        return template.format(
            name=name,
            background=background.replace("_", " "),
            skill=random.choice(skills),
            event=random.choice(events),
            dream=random.choice(dreams),
            family=random.choice(families),
            class_name=class_name
        )

    def _generate_secret(self) -> Dict[str, str]:
        """Generate a secret for the NPC."""
        categories = {
            "past": ["was once a criminal", "fled their homeland", "witnessed a crime"],
            "present": ["owes money to dangerous people", "is being blackmailed", "harbors a fugitive"],
            "future": ["plans to betray their allies", "seeks revenge", "wants to flee"],
            "supernatural": ["is haunted", "has a curse", "made a dark pact"]
        }
        
        category = random.choice(list(categories.keys()))
        return {
            "category": category,
            "secret": random.choice(categories[category])
        }

    def _generate_full_description(self, npc: Dict[str, Any]) -> str:
        """Generate a prose description of the NPC."""
        identity = npc.get("identity", {})
        appearance = identity.get("appearance", {})
        
        return (
            f"{identity.get('name', 'Unknown')} is a {identity.get('age', {}).get('stage', 'adult')} "
            f"{identity.get('race', 'human')} {identity.get('class', 'commoner')}. "
            f"{appearance.get('build', 'Average').capitalize()} build with "
            f"{appearance.get('complexion', 'fair')} skin, {appearance.get('eyes', 'brown eyes')}, "
            f"and {appearance.get('hair', 'brown hair')}. "
            f"They are {identity.get('personality', {}).get('trait', 'neutral')}."
        )

    def generate_multiple(self, count: int, race: Optional[str] = None,
                          class_name: Optional[str] = None,
                          level: int = 1, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate multiple NPCs."""
        if seed is not None:
            random.seed(seed)
        
        npcs = []
        for i in range(count):
            npc = self.generate_npc(
                race=race or "human",
                class_name=class_name or "commoner",
                level=level,
                seed=seed + i if seed else None
            )
            npcs.append(npc)
        
        return npcs

    def generate_party_contacts(self, party_level: int = 5) -> Dict[str, Dict[str, Any]]:
        """Generate NPCs that a party might know."""
        return {
            "ally": self.generate_npc(level=party_level, class_name="fighter", include_stat_block=True),
            "informant": self.generate_npc(level=party_level, class_name="rogue", background="criminal"),
            "patron": self.generate_npc(level=party_level, class_name="noble", background="noble"),
            "rival": self.generate_npc(level=party_level, include_stat_block=True),
            "mentor": self.generate_npc(level=party_level + 2, class_name="wizard", background="sage")
        }


def main():
    """CLI for the NPC generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DnD NPC Generator v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python npc_gen.py -r elf -c wizard -l 5
  python npc_gen.py -r dwarf --class fighter --level 3
  python npc_gen.py -n 5 --list
  python npc_gen.py --contacts --party-level 5
  python npc_gen.py --no-stat-block
        """
    )

    parser.add_argument("-r", "--race",
                        choices=list(NPCGenerator.RACES.keys()),
                        help="Specific race")
    parser.add_argument("-c", "--class", dest="class_name",
                        choices=list(NPCGenerator.CLASSES.keys()),
                        help="Specific class")
    parser.add_argument("-l", "--level", type=int, default=1,
                        help="Character level")
    parser.add_argument("-b", "--background",
                        choices=list(NPCGenerator.BACKGROUNDS.keys()),
                        help="Character background")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Number of NPCs to generate")
    parser.add_argument("--list", action="store_true",
                        help="List NPCs in table format")
    parser.add_argument("--contacts", action="store_true",
                        help="Generate party contacts")
    parser.add_argument("--party-level", type=int, default=5,
                        help="Party level for contacts")
    parser.add_argument("--no-stat-block", action="store_true",
                        help="Exclude stat block")
    parser.add_argument("--no-relationships", action="store_true",
                        help="Exclude relationships")
    parser.add_argument("--no-inventory", action="store_true",
                        help="Exclude inventory")
    parser.add_argument("--seed", type=int, help="Random seed")

    args = parser.parse_args()

    generator = NPCGenerator(seed=args.seed)

    if args.contacts:
        contacts = generator.generate_party_contacts(party_level=args.party_level)
        print("=== Party Contacts ===\n")
        for role, npc in contacts.items():
            print(f"--- {role.capitalize()} ---")
            print(f"Name: {npc['identity']['name']}")
            print(f"Race: {npc['identity']['race']}, Class: {npc['identity']['class']} {npc['identity']['level']}")
            print(f"Faction: {npc['identity']['faction']}")
            if npc.get('stat_block'):
                sb = npc['stat_block']
                print(f"HP: {sb['hit_points']}, AC: {sb['armor_class']}")
            print()
    elif args.list:
        npcs = generator.generate_multiple(
            args.count,
            race=args.race,
            class_name=args.class_name,
            level=args.level
        )
        print(f"{'Name':<25} {'Race':<12} {'Class':<12} {'Level':<6} {'HP':<6}")
        print("-" * 61)
        for npc in npcs:
            hp = npc.get('stat_block', {}).get('hit_points', 'N/A')
            print(f"{npc['identity']['name']:<25} {npc['identity']['race']:<12} {npc['identity']['class']:<12} {npc['identity']['level']:<6} {hp:<6}")
    else:
        npc = generator.generate_npc(
            race=args.race or "human",
            class_name=args.class_name or "commoner",
            level=args.level,
            background=args.background,
            include_stat_block=not args.no_stat_block,
            include_relationships=not args.no_relationships,
            include_inventory=not args.no_inventory
        )

        print(f"=== {npc['identity']['name']} ===\n")
        print(f"Race: {npc['identity']['race']}")
        print(f"Class: {npc['identity']['class']} {npc['identity']['level']}")
        print(f"Background: {npc['identity']['background']}")
        print(f"Alignment: {npc['identity']['alignment']}")
        print(f"Faction: {npc['identity']['faction']}")
        print(f"\nAppearance:")
        app = npc['identity']['appearance']
        print(f"  Build: {app['build']}, Complexion: {app['complexion']}")
        print(f"  Eyes: {app['eyes']}, Hair: {app['hair']}")
        print(f"  Distinguishing: {app['distinguishing_feature']}")
        
        if npc.get('stat_block'):
            sb = npc['stat_block']
            print(f"\nStat Block:")
            print(f"  HP: {sb['hit_points']}, AC: {sb['armor_class']}")
            print(f"  Abilities: STR {sb['ability_scores']['STR']}, DEX {sb['ability_scores']['DEX']}, CON {sb['ability_scores']['CON']}, INT {sb['ability_scores']['INT']}, WIS {sb['ability_scores']['WIS']}, CHA {sb['ability_scores']['CHA']}")
            if sb.get('actions'):
                print(f"  Actions:")
                for action in sb['actions']:
                    print(f"    - {action['name']}: +{action['bonus']} to hit, {action['damage']} damage")
        
        if npc.get('inventory'):
            inv = npc['inventory']
            print(f"\nInventory:")
            print(f"  Weapons: {', '.join(inv['weapons']) if inv['weapons'] else 'None'}")
            print(f"  Armor: {', '.join(inv['armor']) if inv['armor'] else 'None'}")
            print(f"  Gold: {inv['currency']['gp']} gp")
        
        if npc.get('relationships'):
            print(f"\nRelationships:")
            for rel in npc['relationships'][:3]:
                print(f"  - {rel['npc_name']} ({rel['type']}): {rel['description']}")
        
        if npc.get('secret'):
            print(f"\nSecret ({npc['secret']['category']}):")
            print(f"  {npc['secret']['secret']}")
        
        print(f"\nDescription:")
        print(f"  {npc['description']}")


if __name__ == "__main__":
    main()
