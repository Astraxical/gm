#!/usr/bin/env python3
"""
DnD Status Tracker v1.0

Track party status, conditions, resources, and provide visual dashboards.
Perfect for DMs to monitor the party during sessions.

Features:
- Visual HP/status bars for each character
- Condition tracking (prone, stunned, etc.)
- Resource tracking (spell slots, hit dice, abilities)
- Short/long rest tracking
- Inspiration and hero points
- Death save tracking
- Party overview dashboard
- Export to JSON/Markdown
"""

import json
import logging
from typing import Dict, List, Optional, Any, TypedDict
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ConditionType(str, Enum):
    """Standard DnD 5e conditions."""
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


class ResourceCategory(str, Enum):
    """Categories of resources to track."""
    SPELL_SLOTS = "spell_slots"
    HIT_DICE = "hit_dice"
    CLASS_FEATURE = "class_feature"
    CUSTOM = "custom"


@dataclass
class Condition:
    """Represents a condition affecting a character."""
    name: str
    duration: Optional[int] = None  # Rounds, None = until removed
    source: str = ""
    exhaustion_level: int = 0  # For exhaustion condition
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Resource:
    """Represents a trackable resource."""
    name: str
    current: int
    maximum: int
    category: str = "custom"
    short_rest_recover: bool = False
    long_rest_recover: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @property
    def percentage(self) -> float:
        if self.maximum <= 0:
            return 0.0
        return (self.current / self.maximum) * 100
    
    def recover(self, amount: int = 0, full: bool = False) -> int:
        """Recover resource. Returns actual amount recovered."""
        old = self.current
        if full:
            self.current = self.maximum
        else:
            self.current = min(self.maximum, self.current + amount)
        return self.current - old
    
    def spend(self, amount: int) -> int:
        """Spend resource. Returns actual amount spent."""
        old = self.current
        self.current = max(0, self.current - amount)
        return old - self.current


@dataclass
class SpellSlotTracker:
    """Track spell slots by level."""
    slots: Dict[int, Dict[str, int]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.slots:
            self.slots = {}
    
    def set_slots(self, level: int, maximum: int) -> None:
        """Set maximum slots for a level."""
        if level not in self.slots:
            self.slots[level] = {"current": maximum, "maximum": maximum}
        else:
            self.slots[level]["maximum"] = maximum
            self.slots[level]["current"] = maximum
    
    def use_slot(self, level: int) -> bool:
        """Use a spell slot of given level."""
        if level in self.slots and self.slots[level]["current"] > 0:
            self.slots[level]["current"] -= 1
            return True
        return False
    
    def recover_all(self) -> None:
        """Recover all spell slots."""
        for level in self.slots:
            self.slots[level]["current"] = self.slots[level]["maximum"]
    
    def to_dict(self) -> Dict[str, Any]:
        return {"slots": self.slots}


@dataclass
class CharacterStatus:
    """Complete status for a single character."""
    name: str
    player: str
    char_class: str
    level: int
    hp_current: int
    hp_max: int
    temp_hp: int = 0
    ac: int = 10
    initiative: int = 0
    speed: int = 30
    
    # Tracking
    conditions: List[Condition] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    spell_slots: Optional[SpellSlotTracker] = None
    hit_dice_current: int = 0
    hit_dice_total: int = 0
    
    # Special tracking
    inspiration: bool = False
    hero_points: int = 0
    death_save_successes: int = 0
    death_save_failures: int = 0
    
    # Status
    is_concentrating: bool = False
    concentration_spell: str = ""
    concentration_dc: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.spell_slots:
            data["spell_slots"] = self.spell_slots.to_dict()
        return data
    
    @property
    def hp_percentage(self) -> float:
        if self.hp_max <= 0:
            return 0.0
        return ((self.hp_current + self.temp_hp) / self.hp_max) * 100
    
    @property
    def is_unconscious(self) -> bool:
        return self.hp_current <= 0
    
    @property
    def is_stable(self) -> bool:
        return self.is_unconscious and self.death_save_successes >= 3
    
    @property
    def is_dead(self) -> bool:
        return self.death_save_failures >= 3
    
    def take_damage(self, damage: int) -> int:
        """Apply damage. Returns actual damage taken."""
        # Use temp HP first
        if self.temp_hp > 0:
            if damage <= self.temp_hp:
                self.temp_hp -= damage
                return 0
            damage -= self.temp_hp
            self.temp_hp = 0
        
        old_hp = self.hp_current
        self.hp_current = max(-self.hp_max, self.hp_current - damage)
        
        # Reset death saves if healed
        if old_hp <= 0 and self.hp_current > 0:
            self.death_save_successes = 0
            self.death_save_failures = 0
        
        return old_hp - self.hp_current
    
    def heal(self, amount: int) -> int:
        """Heal character. Returns actual amount healed."""
        if self.hp_current <= 0:
            # Waking up from unconscious
            old = self.hp_current
            self.hp_current = min(self.hp_max, self.hp_current + amount)
            self.death_save_successes = 0
            self.death_save_failures = 0
            return self.hp_current - old
        
        old = self.hp_current
        self.hp_current = min(self.hp_max, self.hp_current + amount)
        return self.hp_current - old
    
    def add_temp_hp(self, amount: int) -> int:
        """Add temp HP (doesn't stack). Returns actual temp HP gained."""
        if amount > self.temp_hp:
            gained = amount - self.temp_hp
            self.temp_hp = amount
            return gained
        return 0
    
    def add_condition(self, name: str, duration: Optional[int] = None, source: str = "") -> None:
        """Add a condition."""
        # Check for exhaustion
        if name.lower() == "exhaustion":
            # Remove existing exhaustion and add new level
            self.conditions = [c for c in self.conditions if c.name.lower() != "exhaustion"]
            level = duration if duration else 1
            self.conditions.append(Condition("Exhaustion", source=source, exhaustion_level=level))
        else:
            self.conditions.append(Condition(name, duration, source))
    
    def remove_condition(self, name: str) -> bool:
        """Remove a condition."""
        for i, cond in enumerate(self.conditions):
            if cond.name.lower() == name.lower():
                self.conditions.pop(i)
                return True
        return False
    
    def add_resource(self, name: str, current: int, maximum: int, 
                     category: str = "custom",
                     short_rest: bool = False,
                     long_rest: bool = True) -> Resource:
        """Add a trackable resource."""
        resource = Resource(name, current, maximum, category, short_rest, long_rest)
        self.resources.append(resource)
        return resource
    
    def death_save(self, roll: int) -> Dict[str, Any]:
        """Make a death save."""
        if self.hp_current > 0:
            return {"error": "Not making death saves"}
        
        if roll == 20:
            self.hp_current = 1
            self.death_save_successes = 0
            self.death_save_failures = 0
            return {"result": "awake", "hp": 1}
        elif roll >= 10:
            self.death_save_successes += 1
            if self.death_save_successes >= 3:
                self.death_save_successes = 0
                return {"result": "stable"}
            return {"result": "success", "successes": self.death_save_successes}
        elif roll == 1:
            self.death_save_failures += 2
            if self.death_save_failures >= 3:
                return {"result": "dead"}
            return {"result": "critical_fail", "failures": self.death_save_failures}
        else:
            self.death_save_failures += 1
            if self.death_save_failures >= 3:
                return {"result": "dead"}
            return {"result": "failure", "failures": self.death_save_failures}


@dataclass
class PartyStatus:
    """Complete party status."""
    name: str
    characters: List[CharacterStatus] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "characters": [c.to_dict() for c in self.characters],
            "created": self.created,
            "last_updated": self.last_updated,
            "session_notes": self.session_notes
        }


class StatusTracker:
    """Track and display party status."""

    # Visual bar characters
    BAR_FULL = "█"
    BAR_HALF = "▌"
    BAR_EMPTY = "░"
    
    # Condition colors/symbols
    CONDITION_SYMBOLS = {
        "blinded": "👁️",
        "charmed": "💕",
        "deafened": "👂",
        "frightened": "😨",
        "grappled": "🤝",
        "incapacitated": "💫",
        "invisible": "👻",
        "paralyzed": "⚡",
        "petrified": "🗿",
        "poisoned": "☠️",
        "prone": "📍",
        "restrained": "⛓️",
        "stunned": "💥",
        "unconscious": "💤",
        "exhaustion": "😫"
    }

    def __init__(self, party_name: str = "Adventuring Party"):
        """
        Initialize the status tracker.
        
        Args:
            party_name: Name for the party
        """
        self.party = PartyStatus(name=party_name)
        self.bar_width = 20

    def add_character(
        self,
        name: str,
        player: str,
        char_class: str,
        level: int,
        hp_max: int,
        ac: int = 10,
        speed: int = 30,
        hit_dice: int = 0
    ) -> CharacterStatus:
        """
        Add a character to the party.
        
        Args:
            name: Character name
            player: Player name
            char_class: Character class
            level: Character level
            hp_max: Maximum hit points
            ac: Armor class
            speed: Movement speed
            hit_dice: Number of hit dice (default = level)
            
        Returns:
            Created CharacterStatus
        """
        if hit_dice == 0:
            hit_dice = level
        
        char = CharacterStatus(
            name=name,
            player=player,
            char_class=char_class,
            level=level,
            hp_current=hp_max,
            hp_max=hp_max,
            ac=ac,
            speed=speed,
            hit_dice_current=hit_dice,
            hit_dice_total=hit_dice
        )
        
        # Add spell slots for casters
        if char_class in ["Wizard", "Cleric", "Druid", "Sorcerer", "Bard", "Warlock", "Paladin", "Ranger"]:
            char.spell_slots = SpellSlotTracker()
            self._setup_spell_slots(char, char_class, level)
        
        self.party.characters.append(char)
        self._update_timestamp()
        logger.info(f"Added character: {name} ({char_class} {level})")
        return char

    def _setup_spell_slots(self, char: CharacterStatus, char_class: str, level: int) -> None:
        """Set up initial spell slots based on class and level."""
        if not char.spell_slots:
            return
        
        # Simplified full caster progression
        full_casters = ["Wizard", "Cleric", "Druid", "Sorcerer", "Bard"]
        
        if char_class in full_casters:
            slot_progression = {
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
            }
            slots = slot_progression.get(min(level, 10), {})
            for slot_level, count in slots.items():
                char.spell_slots.set_slots(slot_level, count)

    def remove_character(self, name: str) -> bool:
        """Remove a character from the party."""
        for i, char in enumerate(self.party.characters):
            if char.name.lower() == name.lower():
                self.party.characters.pop(i)
                self._update_timestamp()
                logger.info(f"Removed character: {name}")
                return True
        return False

    def get_character(self, name: str) -> Optional[CharacterStatus]:
        """Get a character by name."""
        for char in self.party.characters:
            if char.name.lower() == name.lower():
                return char
        return None

    def damage_character(self, name: str, damage: int, source: str = "") -> Dict[str, Any]:
        """Deal damage to a character."""
        char = self.get_character(name)
        if not char:
            return {"error": f"Character {name} not found"}
        
        actual = char.take_damage(damage)
        logger.info(f"{name} takes {actual} damage from {source}")
        
        return {
            "name": name,
            "damage": actual,
            "hp_current": char.hp_current,
            "temp_hp": char.temp_hp,
            "is_unconscious": char.is_unconscious
        }

    def heal_character(self, name: str, amount: int, source: str = "") -> Dict[str, Any]:
        """Heal a character."""
        char = self.get_character(name)
        if not char:
            return {"error": f"Character {name} not found"}
        
        actual = char.heal(amount)
        logger.info(f"{name} heals {actual} HP from {source}")
        
        return {
            "name": name,
            "healed": actual,
            "hp_current": char.hp_current
        }

    def add_temp_hp(self, name: str, amount: int) -> Dict[str, Any]:
        """Add temp HP to a character."""
        char = self.get_character(name)
        if not char:
            return {"error": f"Character {name} not found"}
        
        gained = char.add_temp_hp(amount)
        
        return {
            "name": name,
            "temp_hp": char.temp_hp,
            "gained": gained
        }

    def add_condition(self, name: str, condition: str, duration: Optional[int] = None) -> bool:
        """Add a condition to a character."""
        char = self.get_character(name)
        if not char:
            return False
        
        char.add_condition(condition, duration)
        logger.info(f"{name} gains condition: {condition}")
        return True

    def remove_condition(self, name: str, condition: str) -> bool:
        """Remove a condition from a character."""
        char = self.get_character(name)
        if not char:
            return False
        
        success = char.remove_condition(condition)
        if success:
            logger.info(f"{name} loses condition: {condition}")
        return success

    def use_spell_slot(self, name: str, level: int) -> bool:
        """Use a spell slot."""
        char = self.get_character(name)
        if not char or not char.spell_slots:
            return False
        
        return char.spell_slots.use_slot(level)

    def short_rest(self) -> Dict[str, Any]:
        """
        Perform a short rest for the entire party.
        
        Returns:
            Summary of what was recovered
        """
        recovered = {"characters": []}
        
        for char in self.party.characters:
            char_recovery = {"name": char.name, "recovered": []}
            
            # Recover hit dice (half)
            dice_recovered = char.hit_dice_total // 2
            char.hit_dice_current = min(char.hit_dice_total, char.hit_dice_current + dice_recovered)
            char_recovery["recovered"].append(f"Hit Dice: +{dice_recovered}")
            
            # Recover short rest resources
            for resource in char.resources:
                if resource.short_rest_recover:
                    recovered_amt = resource.recover(full=True)
                    char_recovery["recovered"].append(f"{resource.name}: +{recovered_amt}")
            
            # Remove some conditions
            conditions_removed = []
            for cond in char.conditions[:]:
                if cond.duration is not None:
                    cond.duration -= 1
                    if cond.duration <= 0:
                        conditions_removed.append(cond.name)
                        char.conditions.remove(cond)
            
            if conditions_removed:
                char_recovery["recovered"].append(f"Conditions ended: {', '.join(conditions_removed)}")
            
            recovered["characters"].append(char_recovery)
        
        self._update_timestamp()
        logger.info("Party completed short rest")
        return recovered

    def long_rest(self) -> Dict[str, Any]:
        """
        Perform a long rest for the entire party.
        
        Returns:
            Summary of what was recovered
        """
        recovered = {"characters": []}
        
        for char in self.party.characters:
            char_recovery = {"name": char.name, "recovered": []}
            
            # Recover all HP
            if char.hp_current < char.hp_max:
                healed = char.hp_max - char.hp_current
                char.hp_current = char.hp_max
                char_recovery["recovered"].append(f"HP: +{healed}")
            
            # Recover all hit dice (half minimum)
            dice_recovered = max(char.hit_dice_total // 2, char.hit_dice_total - char.hit_dice_current)
            char.hit_dice_current = char.hit_dice_total
            char_recovery["recovered"].append(f"Hit Dice: +{dice_recovered}")
            
            # Recover spell slots
            if char.spell_slots:
                char.spell_slots.recover_all()
                char_recovery["recovered"].append("Spell Slots: All")
            
            # Recover all resources
            for resource in char.resources:
                if resource.long_rest_recover:
                    recovered_amt = resource.recover(full=True)
                    char_recovery["recovered"].append(f"{resource.name}: +{recovered_amt}")
            
            # Reset death saves
            char.death_save_successes = 0
            char.death_save_failures = 0
            
            # Remove all conditions except exhaustion
            conditions_removed = []
            for cond in char.conditions[:]:
                if cond.name.lower() != "exhaustion":
                    conditions_removed.append(cond.name)
                    char.conditions.remove(cond)
            
            # Reduce exhaustion level
            for cond in char.conditions:
                if cond.name.lower() == "exhaustion":
                    if cond.exhaustion_level > 1:
                        cond.exhaustion_level -= 1
                        char_recovery["recovered"].append(f"Exhaustion reduced to {cond.exhaustion_level}")
                    else:
                        char.conditions.remove(cond)
                        char_recovery["recovered"].append("Exhaustion removed")
            
            if conditions_removed:
                char_recovery["recovered"].append(f"Conditions ended: {', '.join(conditions_removed)}")
            
            recovered["characters"].append(char_recovery)
        
        self._update_timestamp()
        logger.info("Party completed long rest")
        return recovered

    def _update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.party.last_updated = datetime.now(timezone.utc).isoformat()

    def _create_bar(self, current: int, maximum: int, width: int = None) -> str:
        """Create a visual status bar."""
        if width is None:
            width = self.bar_width
        
        if maximum <= 0:
            return self.BAR_EMPTY * width
        
        filled = int((current / maximum) * width)
        empty = width - filled
        
        bar = self.BAR_FULL * filled
        if empty > 0 and filled < width:
            bar += self.BAR_EMPTY * empty
        
        return bar

    def _get_condition_display(self, char: CharacterStatus) -> str:
        """Get formatted condition display."""
        if not char.conditions:
            return "-"
        
        symbols = []
        for cond in char.conditions:
            symbol = self.CONDITION_SYMBOLS.get(cond.name.lower(), "•")
            if cond.name.lower() == "exhaustion":
                symbol = f"😫{cond.exhaustion_level}"
            symbols.append(symbol)
        
        return " ".join(symbols)

    def display_party_status(self) -> str:
        """
        Generate a visual party status display.
        
        Returns:
            Formatted status string
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"  {self.party.name} - Status Dashboard")
        lines.append(f"  Updated: {self.party.last_updated[:19].replace('T', ' ')}")
        lines.append("=" * 70)
        lines.append("")
        
        for char in self.party.characters:
            # Character header
            status = "💀" if char.is_dead else "💤" if char.is_unconscious else "✓"
            lines.append(f"{status} {char.name} ({char.char_class} {char.level}) - {char.player}")
            lines.append("-" * 50)
            
            # HP Bar
            total_hp = char.hp_current + char.temp_hp
            hp_bar = self._create_bar(total_hp, char.hp_max)
            hp_text = f"HP: {char.hp_current}/{char.hp_max}"
            if char.temp_hp > 0:
                hp_text += f" (+{char.temp_hp} temp)"
            lines.append(f"  {hp_bar} {hp_text}")
            
            # AC, Speed, Initiative
            lines.append(f"  AC: {char.ac} | Speed: {char.speed} | Init: {char.initiative:+d}")
            
            # Hit Dice
            lines.append(f"  Hit Dice: {char.hit_dice_current}/{char.hit_dice_total}")
            
            # Conditions
            cond_display = self._get_condition_display(char)
            lines.append(f"  Conditions: {cond_display}")
            
            # Spell slots
            if char.spell_slots:
                slots_str = " | ".join([
                    f"L{lvl}: {data['current']}/{data['maximum']}"
                    for lvl, data in sorted(char.spell_slots.slots.items())
                    if data['maximum'] > 0
                ])
                lines.append(f"  Spell Slots: {slots_str}")
            
            # Resources
            for resource in char.resources:
                res_bar = self._create_bar(resource.current, resource.maximum, width=10)
                lines.append(f"  {resource.name}: {res_bar} {resource.current}/{resource.maximum}")
            
            # Special tracking
            extras = []
            if char.inspiration:
                extras.append("Inspiration: ✓")
            if char.hero_points > 0:
                extras.append(f"Hero Points: {char.hero_points}")
            if char.is_concentrating:
                extras.append(f"Concentrating: {char.concentration_spell}")
            if char.death_save_successes > 0 or char.death_save_failures > 0:
                extras.append(f"Death Saves: {'✓' * char.death_save_successes}{'✗' * char.death_save_failures}")
            
            if extras:
                lines.append(f"  {', '.join(extras)}")
            
            lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)

    def display_quick_view(self) -> str:
        """
        Generate a compact quick view of the party.
        
        Returns:
            Compact status string
        """
        lines = []
        lines.append(f"{'Name':<15} {'HP':<12} {'AC':<5} {'Conditions':<20}")
        lines.append("-" * 55)
        
        for char in self.party.characters:
            status = "💀" if char.is_dead else "💤" if char.is_unconscious else ""
            hp = f"{char.hp_current}/{char.hp_max}"
            if char.temp_hp > 0:
                hp += f"+{char.temp_hp}"
            
            conditions = self._get_condition_display(char)
            lines.append(f"{status} {char.name:<14} {hp:<12} {char.ac:<5} {conditions:<20}")
        
        return "\n".join(lines)

    def export_to_json(self, filepath: str) -> None:
        """Export party status to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.party.to_dict(), f, indent=2)
        logger.info(f"Exported party status to {filepath}")

    def export_to_markdown(self, filepath: str) -> None:
        """Export party status to Markdown."""
        lines = []
        lines.append(f"# {self.party.name} - Status")
        lines.append(f"\n*Updated: {self.party.last_updated[:19].replace('T', ' ')}*\n")
        
        for char in self.party.characters:
            lines.append(f"## {char.name}")
            lines.append(f"**Class/Level:** {char.char_class} {char.level} | **Player:** {char.player}\n")
            lines.append(f"**HP:** {char.hp_current}/{char.hp_max} | **AC:** {char.ac} | **Speed:** {char.speed}\n")
            
            if char.conditions:
                lines.append(f"**Conditions:** {', '.join([c.name for c in char.conditions])}\n")
            
            if char.spell_slots:
                lines.append("**Spell Slots:**")
                for lvl, data in sorted(char.spell_slots.slots.items()):
                    lines.append(f"- Level {lvl}: {data['current']}/{data['maximum']}")
                lines.append("")
        
        if self.party.session_notes:
            lines.append(f"## Session Notes\n\n{self.party.session_notes}\n")
        
        with open(filepath, 'w') as f:
            f.write("\n".join(lines))
        logger.info(f"Exported party status to {filepath}")


def main():
    """CLI for status tracker."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DnD Status Tracker v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python status_tracker.py --demo
  python status_tracker.py --party "The Dragon Slayers" --export party.json
  python status_tracker.py --quick-view
        """
    )
    
    parser.add_argument("--demo", action="store_true",
                        help="Run demo with sample party")
    parser.add_argument("--party", type=str,
                        help="Party name")
    parser.add_argument("--export", type=str,
                        help="Export to JSON file")
    parser.add_argument("--export-md", type=str,
                        help="Export to Markdown file")
    parser.add_argument("--quick-view", action="store_true",
                        help="Show compact view")
    
    args = parser.parse_args()
    
    tracker = StatusTracker(party_name=args.party or "Adventuring Party")
    
    if args.demo:
        print("=== Demo Party Status ===\n")
        
        # Add sample characters
        fighter = tracker.add_character("Thorin", "Mike", "Fighter", 5, hp_max=45, ac=18)
        fighter.add_condition("Poisoned")
        fighter.inspiration = True
        
        wizard = tracker.add_character("Elara", "Jess", "Wizard", 5, hp_max=27, ac=13)
        wizard.is_concentrating = True
        wizard.concentration_spell = "Haste"
        
        cleric = tracker.add_character("Bran", "Tom", "Cleric", 5, hp_max=35, ac=18)
        cleric.hp_current = 20  # Damaged
        cleric.tempo_hp = 5
        
        rogue = tracker.add_character("Shadow", "Alex", "Rogue", 5, hp_max=32, ac=16)
        rogue.add_condition("Exhaustion", duration=1)
        
        # Display full status
        print(tracker.display_party_status())
        
        print("\n=== Quick View ===\n")
        print(tracker.display_quick_view())
        
        if args.export:
            tracker.export_to_json(args.export)
        
        if args.export_md:
            tracker.export_to_markdown(args.export_md)
        
        return
    
    if args.quick_view:
        print(tracker.display_quick_view())
        return
    
    print(tracker.display_party_status())


if __name__ == "__main__":
    main()
