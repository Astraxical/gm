#!/usr/bin/env python3
"""
DnD GM Toolkit - Shared Data Module

Common data structures, enums, and reference tables used across all modules.
Centralizes D&D 5e game data to avoid duplication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================


class Difficulty(str, Enum):
    """Encounter/task difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    DEADLY = "deadly"
    BOSS = "boss"
    EPIC = "epic"


class CreatureType(str, Enum):
    """D&D creature types."""
    ABERRATION = "aberration"
    BEAST = "beast"
    CELESTIAL = "celestial"
    CONSTRUCT = "construct"
    DRAGON = "dragon"
    ELEMENTAL = "elemental"
    FEY = "fey"
    FIEND = "fiend"
    GIANT = "giant"
    HUMANOID = "humanoid"
    MONSTROSITY = "monstrosity"
    OOZE = "ooze"
    PLANT = "plant"
    UNDEAD = "undead"


class Alignment(str, Enum):
    """D&D alignments."""
    LAWFUL_GOOD = "lawful good"
    NEUTRAL_GOOD = "neutral good"
    CHAOTIC_GOOD = "chaotic good"
    LAWFUL_NEUTRAL = "lawful neutral"
    TRUE_NEUTRAL = "true neutral"
    CHAOTIC_NEUTRAL = "chaotic neutral"
    LAWFUL_EVIL = "lawful evil"
    NEUTRAL_EVIL = "neutral evil"
    CHAOTIC_EVIL = "chaotic evil"


class Rarity(str, Enum):
    """Item rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"
    ARTIFACT = "artifact"


class SpellSchool(str, Enum):
    """Magic schools."""
    ABJURATION = "abjuration"
    CONJURATION = "conjuration"
    DIVINATION = "divination"
    ENCHANTMENT = "enchantment"
    EVOCATION = "evocation"
    ILLUSION = "illusion"
    NECROMANCY = "necromancy"
    TRANSMUTATION = "transmutation"


class ConditionType(str, Enum):
    """Standard D&D conditions."""
    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"
    EXHAUSTION = "exhaustion"


class CharacterClass(str, Enum):
    """D&D character classes."""
    BARBARIAN = "barbarian"
    BARD = "bard"
    CLERIC = "cleric"
    DRUID = "druid"
    FIGHTER = "fighter"
    MONK = "monk"
    PALADIN = "paladin"
    RANGER = "ranger"
    ROGUE = "rogue"
    SORCERER = "sorcerer"
    WARLOCK = "warlock"
    WIZARD = "wizard"


class RaceType(str, Enum):
    """Common character races."""
    HUMAN = "human"
    ELF = "elf"
    DWARF = "dwarf"
    HALFLING = "halfling"
    DRAGONBORN = "dragonborn"
    GNOME = "gnome"
    HALF_ELF = "half_elf"
    HALF_ORC = "half_orc"
    TIEFLING = "tiefling"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class AbilityScores:
    """Standard D&D ability scores."""
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    def get_modifier(self, ability: str) -> int:
        """Get modifier for an ability score."""
        score = getattr(self, ability.lower(), 10)
        return (score - 10) // 2
    
    def get_all_modifiers(self) -> Dict[str, int]:
        """Get all ability modifiers."""
        return {
            "STR": self.get_modifier("strength"),
            "DEX": self.get_modifier("dexterity"),
            "CON": self.get_modifier("constitution"),
            "INT": self.get_modifier("intelligence"),
            "WIS": self.get_modifier("wisdom"),
            "CHA": self.get_modifier("charisma")
        }


@dataclass
class Damage:
    """Damage specification."""
    amount: str  # e.g., "2d6"
    damage_type: str  # e.g., "fire", "slashing"
    modifier: int = 0
    
    @property
    def average(self) -> float:
        """Calculate average damage."""
        import re
        match = re.match(r'(\d+)d(\d+)', self.amount)
        if match:
            num_dice = int(match.group(1))
            die_size = int(match.group(2))
            return num_dice * (die_size + 1) / 2 + self.modifier
        return float(self.amount) if self.amount.isdigit() else 0


@dataclass
class Action:
    """Combat action specification."""
    name: str
    description: str
    attack_bonus: int = 0
    damage: Optional[Damage] = None
    save_dc: int = 0
    save_ability: str = ""
    range: str = ""
    target: str = ""


@dataclass
class Spell:
    """Spell specification."""
    name: str
    level: int
    school: str
    casting_time: str = "1 action"
    range: str = ""
    components: List[str] = field(default_factory=list)
    duration: str = ""
    description: str = ""
    at_higher_levels: str = ""
    classes: List[str] = field(default_factory=list)


@dataclass
class MagicItem:
    """Magic item specification."""
    name: str
    type: str
    rarity: str
    requires_attunement: bool = False
    description: str = ""
    properties: List[str] = field(default_factory=list)
    curses: List[str] = field(default_factory=list)


@dataclass
class Creature:
    """Creature/NPC specification."""
    name: str
    creature_type: str
    alignment: str = "neutral"
    armor_class: int = 10
    hit_points: int = 10
    hit_dice: str = ""
    speed: int = 30
    ability_scores: Optional[AbilityScores] = None
    challenge_rating: float = 0
    traits: List[str] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    reactions: List[Action] = field(default_factory=list)
    legendary_actions: List[Action] = field(default_factory=list)


@dataclass
class Location:
    """Location specification."""
    name: str
    location_type: str
    description: str = ""
    features: List[str] = field(default_factory=list)
    encounters: List[str] = field(default_factory=list)
    exits: List[str] = field(default_factory=list)


@dataclass
class Treasure:
    """Treasure specification."""
    gold_pieces: int = 0
    platinum_pieces: int = 0
    silver_pieces: int = 0
    copper_pieces: int = 0
    electrum_pieces: int = 0
    gems: List[Dict[str, Any]] = field(default_factory=list)
    magic_items: List[MagicItem] = field(default_factory=list)
    art_objects: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def total_gp_value(self) -> int:
        """Calculate total value in gold pieces."""
        return (
            self.platinum_pieces * 10 +
            self.gold_pieces +
            self.silver_pieces // 10 +
            self.copper_pieces // 100 +
            self.electrum_pieces // 2 +
            sum(g.get('value', 0) for g in self.gems) +
            sum(a.get('value', 0) for a in self.art_objects)
        )


@dataclass
class Quest:
    """Quest specification."""
    title: str
    quest_type: str
    description: str = ""
    hook: str = ""
    objectives: List[str] = field(default_factory=list)
    rewards: Optional[Treasure] = None
    npcs: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    complications: List[str] = field(default_factory=list)


# =============================================================================
# REFERENCE TABLES
# =============================================================================

# Class hit dice
CLASS_HIT_DICE = {
    "barbarian": 12,
    "bard": 8,
    "cleric": 8,
    "druid": 8,
    "fighter": 10,
    "monk": 8,
    "paladin": 10,
    "ranger": 10,
    "rogue": 8,
    "sorcerer": 6,
    "warlock": 8,
    "wizard": 6
}

# Class primary abilities
CLASS_PRIMARY_ABILITIES = {
    "barbarian": ["STR", "CON"],
    "bard": ["CHA"],
    "cleric": ["WIS"],
    "druid": ["WIS"],
    "fighter": ["STR", "DEX"],
    "monk": ["DEX", "WIS"],
    "paladin": ["STR", "CHA"],
    "ranger": ["DEX", "WIS"],
    "rogue": ["DEX"],
    "sorcerer": ["CHA"],
    "warlock": ["CHA"],
    "wizard": ["INT"]
}

# Class saving throw proficiencies
CLASS_SAVING_THROWS = {
    "barbarian": ["STR", "CON"],
    "bard": ["DEX", "CHA"],
    "cleric": ["WIS", "CHA"],
    "druid": ["INT", "WIS"],
    "fighter": ["STR", "CON"],
    "monk": ["STR", "DEX"],
    "paladin": ["WIS", "CHA"],
    "ranger": ["STR", "DEX"],
    "rogue": ["DEX", "INT"],
    "sorcerer": ["CON", "CHA"],
    "warlock": ["WIS", "CHA"],
    "wizard": ["INT", "WIS"]
}

# Racial ability bonuses (standard)
RACIAL_ABILITY_BONUSES = {
    "human": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
    "elf": {"DEX": 2},
    "dwarf": {"CON": 2},
    "halfling": {"DEX": 2},
    "dragonborn": {"STR": 2, "CHA": 1},
    "gnome": {"INT": 2},
    "half_elf": {"CHA": 2},
    "half_orc": {"STR": 2, "CON": 1},
    "tiefling": {"CHA": 2, "INT": 1}
}

# Background skill proficiencies
BACKGROUND_SKILLS = {
    "acolyte": ["Insight", "Religion"],
    "charlatan": ["Deception", "Sleight of Hand"],
    "criminal": ["Deception", "Stealth"],
    "entertainer": ["Acrobatics", "Performance"],
    "folk_hero": ["Animal Handling", "Survival"],
    "guild_artisan": ["Insight", "Persuasion"],
    "hermit": ["Medicine", "Religion"],
    "noble": ["History", "Persuasion"],
    "outlander": ["Athletics", "Survival"],
    "sage": ["Arcana", "History"],
    "sailor": ["Athletics", "Perception"],
    "soldier": ["Athletics", "Intimidation"],
    "urchin": ["Sleight of Hand", "Stealth"]
}

# XP thresholds by character level
XP_THRESHOLDS = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
    6: 14000,
    7: 23000,
    8: 34000,
    9: 48000,
    10: 64000,
    11: 85000,
    12: 100000,
    13: 120000,
    14: 140000,
    15: 165000,
    16: 195000,
    17: 225000,
    18: 265000,
    19: 305000,
    20: 355000
}

# Proficiency bonus by level
PROFICIENCY_BONUS = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6
}

# Condition effects
CONDITION_EFFECTS = {
    "blinded": {"attack_disadvantage": True, "attacks_against_advantage": True},
    "charmed": {"cant_attack_source": True},
    "deafened": {"can_hear": False},
    "frightened": {"ability_disadvantage": True, "cant_move_closer": True},
    "grappled": {"speed": 0},
    "incapacitated": {"cant_take_actions": True, "cant_take_reactions": True},
    "invisible": {"attack_advantage": True, "attacks_against_disadvantage": True},
    "paralyzed": {"incapacitated": True, "attacks_against_critical": True},
    "petrified": {"incapacitated": True, "resistant_all_damage": True},
    "poisoned": {"attack_disadvantage": True, "ability_disadvantage": True},
    "prone": {"attack_disadvantage": True, "attacks_against_advantage_melee": True},
    "restrained": {"speed": 0, "attack_disadvantage": True, "attacks_against_advantage": True},
    "stunned": {"incapacitated": True, "attack_disadvantage": True, "attacks_against_advantage": True},
    "unconscious": {"incapacitated": True, "attacks_against_critical": True}
}

# Spell slots by class and level
SPELL_SLOTS = {
    "full_caster": {
        1: {1: 2},
        2: {1: 3},
        3: {1: 4, 2: 2},
        4: {1: 4, 2: 3},
        5: {1: 4, 2: 3, 3: 2},
        6: {1: 4, 2: 3, 3: 3},
        7: {1: 4, 2: 3, 3: 3, 4: 1},
        8: {1: 4, 2: 3, 3: 3, 4: 2},
        9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
        10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
    },
    "half_caster": {
        2: {1: 2},
        3: {1: 3},
        4: {1: 3},
        5: {1: 4, 2: 2},
    },
    "third_caster": {
        3: {1: 2},
        4: {1: 3},
    }
}

# Currency exchange rates (to GP)
CURRENCY_RATES = {
    "pp": 10,
    "gp": 1,
    "ep": 0.5,
    "sp": 0.1,
    "cp": 0.01
}

# Lifestyle expenses per day
LIFESTYLE_EXPENSES = {
    "wretched": 0,
    "squalid": 0.1,
    "poor": 0.2,
    "modest": 1,
    "comfortable": 2,
    "wealthy": 4,
    "aristocratic": 10
}

# Encumbrance rules
ENCUMBRANCE = {
    "carry": 15,  # STR x 15
    "push_drag_lift": 30,  # STR x 30
    "encumbered": 5,  # Speed -10 if carrying more than STR x 5
    "heavily_encumbered": 10  # Speed -20 and disadvantage if carrying more than STR x 10
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_xp_for_cr(cr: float) -> int:
    """Get XP value for a challenge rating."""
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


def get_level_from_xp(xp: int) -> int:
    """Get character level from total XP."""
    for level in range(20, 0, -1):
        if xp >= XP_THRESHOLDS[level]:
            return level
    return 1


def get_proficiency_bonus(level: int) -> int:
    """Get proficiency bonus for a level."""
    return PROFICIENCY_BONUS.get(level, 2)


def calculate_ability_modifier(score: int) -> int:
    """Calculate ability modifier from score."""
    return (score - 10) // 2


def parse_cr(cr: str) -> float:
    """Parse CR string to float."""
    if isinstance(cr, (int, float)):
        return float(cr)
    if "/" in str(cr):
        parts = str(cr).split("/")
        return int(parts[0]) / int(parts[1])
    return float(cr or 0)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'Difficulty',
    'CreatureType',
    'Alignment',
    'Rarity',
    'SpellSchool',
    'ConditionType',
    'CharacterClass',
    'RaceType',
    
    # Data classes
    'AbilityScores',
    'Damage',
    'Action',
    'Spell',
    'MagicItem',
    'Creature',
    'Location',
    'Treasure',
    'Quest',
    
    # Reference tables
    'CLASS_HIT_DICE',
    'CLASS_PRIMARY_ABILITIES',
    'CLASS_SAVING_THROWS',
    'RACIAL_ABILITY_BONUSES',
    'BACKGROUND_SKILLS',
    'XP_THRESHOLDS',
    'PROFICIENCY_BONUS',
    'CONDITION_EFFECTS',
    'SPELL_SLOTS',
    'CURRENCY_RATES',
    'LIFESTYLE_EXPENSES',
    'ENCUMBRANCE',
    
    # Utility functions
    'get_xp_for_cr',
    'get_level_from_xp',
    'get_proficiency_bonus',
    'calculate_ability_modifier',
    'parse_cr',
]
