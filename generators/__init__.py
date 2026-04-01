"""
DnD GM Toolkit - Generators

Content generators for encounters, loot, NPCs, characters, quests, and more.
"""

from .encounter_gen import EncounterGenerator
from .loot_gen import LootGenerator
from .rpg_char_gen import RPGCharacterGenerator
from .npc_gen import NPCGenerator
from .name_gen import NameGenerator
from .dungeon_generator import DungeonGenerator
from .weather_generator import WeatherGenerator
from .random_event_generator import EventGenerator
from .lair_action_generator import LairActionGenerator
from .quest_builder import QuestBuilder
from .one_shot_builder import OneShotBuilder
from .spell_card_generator import SpellCardGenerator

# Alias for backwards compatibility
CharacterGenerator = RPGCharacterGenerator

__all__ = [
    "EncounterGenerator",
    "LootGenerator",
    "RPGCharacterGenerator",
    "CharacterGenerator",  # Alias
    "NPCGenerator",
    "NameGenerator",
    "DungeonGenerator",
    "WeatherGenerator",
    "EventGenerator",
    "LairActionGenerator",
    "QuestBuilder",
    "OneShotBuilder",
    "SpellCardGenerator",
]
