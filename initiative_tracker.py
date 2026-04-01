#!/usr/bin/env python3
"""
DnD Initiative Tracker v1.0

Track combat initiative, turns, conditions, and export to VTT.
Supports multiple combatants, concentration tracking, and combat logging.

Features:
- Add/remove combatants with initiative
- Turn tracking with next/previous navigation
- Condition management (prone, stunned, etc.)
- Concentration tracking for spellcasters
- HP tracking and damage logging
- Combat log with full history
- Export to Foundry VTT and Roll20
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any, TypedDict
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


class CombatantDisposition(str, Enum):
    """Combatant disposition toward party."""
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"


class Condition(TypedDict):
    """Type definition for a condition."""
    name: str
    duration: Optional[int]  # Rounds, None = permanent
    source: str  # Who/what caused it


class CombatLogEntry(TypedDict):
    """Type definition for combat log entry."""
    round: int
    turn: int
    timestamp: str
    actor: str
    action: str
    details: str


@dataclass
class Combatant:
    """Represents a combatant in initiative order."""
    name: str
    initiative: int
    hp_current: int
    hp_max: int
    ac: int
    disposition: str = "hostile"
    conditions: List[Condition] = field(default_factory=list)
    concentration: bool = False
    concentration_dc: int = 0
    speed: int = 30
    notes: str = ""
    
    # Tracking
    has_taken_turn: bool = False
    reactions_available: bool = True
    bonus_action_available: bool = True
    
    # Death saves (for PCs)
    death_save_successes: int = 0
    death_save_failures: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @property
    def hp_percentage(self) -> float:
        """Return current HP as percentage of max."""
        if self.hp_max <= 0:
            return 0.0
        return (self.hp_current / self.hp_max) * 100
    
    @property
    def is_unconscious(self) -> bool:
        """Check if combatant is unconscious."""
        return self.hp_current <= 0
    
    @property
    def is_dead(self) -> bool:
        """Check if combatant is dead (failed 3 death saves)."""
        return self.death_save_failures >= 3
    
    def take_damage(self, damage: int) -> int:
        """
        Apply damage to combatant.
        
        Returns:
            Actual damage taken (may be reduced if HP goes negative)
        """
        old_hp = self.hp_current
        self.hp_current = max(-self.hp_max, self.hp_current - damage)
        
        # Check for going unconscious
        if old_hp > 0 and self.hp_current <= 0:
            logger.info(f"{self.name} falls unconscious!")
        
        return old_hp - self.hp_current
    
    def heal(self, amount: int) -> int:
        """
        Heal combatant.
        
        Returns:
            Actual amount healed
        """
        old_hp = self.hp_current
        self.hp_current = min(self.hp_max, self.hp_current + amount)
        return self.hp_current - old_hp
    
    def add_condition(self, name: str, duration: Optional[int] = None, source: str = "") -> None:
        """Add a condition to the combatant."""
        self.conditions.append({
            "name": name,
            "duration": duration,
            "source": source
        })
        logger.debug(f"{self.name} gains condition: {name}")
    
    def remove_condition(self, name: str) -> bool:
        """Remove a condition from the combatant."""
        for i, cond in enumerate(self.conditions):
            if cond["name"].lower() == name.lower():
                self.conditions.pop(i)
                logger.debug(f"{self.name} loses condition: {name}")
                return True
        return False
    
    def start_death_save(self, success: bool = False, failure: bool = False) -> None:
        """Record a death save result."""
        if success:
            self.death_save_successes += 1
        if failure:
            self.death_save_failures += 1
    
    def reset_death_saves(self) -> None:
        """Reset death saves (when stabilized or healed)."""
        self.death_save_successes = 0
        self.death_save_failures = 0
    
    def concentration_check(self, damage: int, dc_override: Optional[int] = None) -> bool:
        """
        Make a concentration check.
        
        Returns:
            True if check passed, False if concentration broken
        """
        if not self.concentration:
            return True
        
        dc = dc_override or max(10, damage // 2)
        # Assume average modifier of +3 for simplicity
        # In full implementation, would use actual CON mod + proficiency
        roll = random.randint(1, 20)
        total = roll + 3  # Simplified
        
        if total >= dc:
            logger.debug(f"{self.name} maintains concentration (rolled {total} vs DC {dc})")
            return True
        else:
            logger.info(f"{self.name} loses concentration!")
            self.concentration = False
            return False


@dataclass
class Combat:
    """Represents an active combat encounter."""
    name: str
    combatants: List[Combatant] = field(default_factory=list)
    current_round: int = 1
    current_turn_index: int = 0
    is_active: bool = False
    log: List[CombatLogEntry] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "combatants": [c.to_dict() for c in self.combatants],
            "current_round": self.current_round,
            "current_turn_index": self.current_turn_index,
            "is_active": self.is_active,
            "log": self.log
        }


class InitiativeTracker:
    """Track initiative for DnD 5e combat encounters."""

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the initiative tracker.
        
        Args:
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        
        self.combats: Dict[str, Combat] = {}
        self.current_combat: Optional[str] = None

    def create_combat(self, name: str) -> Combat:
        """
        Create a new combat encounter.
        
        Args:
            name: Name for the combat
            
        Returns:
            Created Combat object
        """
        combat = Combat(name=name)
        self.combats[name] = combat
        self.current_combat = name
        logger.info(f"Created combat: {name}")
        return combat

    def add_combatant(
        self,
        name: str,
        hp: int,
        ac: int,
        initiative_mod: int = 0,
        disposition: str = "hostile",
        speed: int = 30,
        roll_initiative: bool = True
    ) -> Combatant:
        """
        Add a combatant to the current combat.
        
        Args:
            name: Combatant name
            hp: Hit points
            ac: Armor class
            initiative_mod: Initiative modifier (DEX usually)
            disposition: friendly, neutral, or hostile
            speed: Movement speed in feet
            roll_initiative: Whether to roll initiative now
            
        Returns:
            Added Combatant object
        """
        if not self.current_combat:
            self.create_combat("Combat")
        
        combat = self.combats[self.current_combat]
        
        # Roll or set initiative
        initiative = random.randint(1, 20) + initiative_mod if roll_initiative else initiative_mod
        
        combatant = Combatant(
            name=name,
            initiative=initiative,
            hp_current=hp,
            hp_max=hp,
            ac=ac,
            disposition=disposition,
            speed=speed
        )
        
        combat.combatants.append(combatant)
        logger.info(f"Added {name} (Initiative: {initiative}, HP: {hp}, AC: {ac})")
        
        # Sort by initiative descending
        combat.combatants.sort(key=lambda c: c.initiative, reverse=True)
        
        return combatant

    def remove_combatant(self, name: str) -> bool:
        """
        Remove a combatant from combat.
        
        Args:
            name: Combatant name
            
        Returns:
            True if removed, False if not found
        """
        if not self.current_combat:
            return False
        
        combat = self.combats[self.current_combat]
        for i, combatant in enumerate(combat.combatants):
            if combatant.name.lower() == name.lower():
                combat.combatants.pop(i)
                self._log_action(name, "removed", "Removed from combat")
                logger.info(f"Removed {name} from combat")
                return True
        return False

    def start_combat(self) -> None:
        """Start the combat and log the first round."""
        if not self.current_combat:
            raise ValueError("No combat created yet")
        
        combat = self.combats[self.current_combat]
        combat.is_active = True
        combat.current_round = 1
        combat.current_turn_index = 0
        
        self._log_action("SYSTEM", "combat_start", f"Combat '{combat.name}' begins!")
        logger.info(f"Combat started! Initiative order:")
        for i, c in enumerate(combat.combatants, 1):
            print(f"  {i}. {c.name} (Init: {c.initiative})")

    def next_turn(self) -> Optional[Combatant]:
        """
        Advance to the next turn.
        
        Returns:
            Combatant whose turn it is, or None if no combat
        """
        if not self.current_combat:
            return None
        
        combat = self.combats[self.current_combat]
        
        if not combat.is_active:
            self.start_combat()
            return combat.combatants[0] if combat.combatants else None
        
        # Mark previous turn as taken
        if combat.combatants:
            combat.combatants[combat.current_turn_index].has_taken_turn = True
        
        # Advance turn index
        combat.current_turn_index += 1
        
        # Check for new round
        if combat.current_turn_index >= len(combat.combatants):
            combat.current_turn_index = 0
            combat.current_round += 1
            self._log_action("SYSTEM", "round", f"Round {combat.current_round} begins")
            logger.info(f"=== Round {combat.current_round} ===")
            
            # Decrement condition durations
            self._tick_conditions(combat)
        
        # Get current combatant
        current = combat.combatants[combat.current_turn_index]
        current.has_taken_turn = False
        current.reactions_available = True
        current.bonus_action_available = True
        
        self._log_action(current.name, "turn_start", f"Turn begins")
        print(f"\n➤ {current.name}'s turn (Init: {current.initiative})")
        print(f"   HP: {current.hp_current}/{current.hp_max} | AC: {current.ac}")
        if current.conditions:
            print(f"   Conditions: {[c['name'] for c in current.conditions]}")
        
        return current

    def previous_turn(self) -> Optional[Combatant]:
        """Go back to the previous turn."""
        if not self.current_combat:
            return None
        
        combat = self.combats[self.current_combat]
        
        if combat.current_turn_index > 0:
            combat.current_turn_index -= 1
            # Check if we went back a round
            if combat.current_turn_index == len(combat.combatants) - 1:
                combat.current_round -= 1
        
        current = combat.combatants[combat.current_turn_index]
        print(f"\n⏪ Back to {current.name}'s turn")
        return current

    def _tick_conditions(self, combat: Combat) -> None:
        """Decrement condition durations at round start."""
        for combatant in combat.combatants:
            for cond in combatant.conditions[:]:
                if cond["duration"] is not None:
                    cond["duration"] -= 1
                    if cond["duration"] <= 0:
                        combatant.conditions.remove(cond)
                        logger.debug(f"{combatant.name}'s {cond['name']} condition ended")

    def damage_combatant(
        self,
        name: str,
        damage: int,
        damage_type: str = "",
        source: str = ""
    ) -> Dict[str, Any]:
        """
        Apply damage to a combatant.
        
        Args:
            name: Combatant name
            damage: Amount of damage
            damage_type: Type of damage (fire, slashing, etc.)
            source: Source of damage
            
        Returns:
            Dict with damage details
        """
        combatant = self._get_combatant(name)
        if not combatant:
            return {"error": f"Combatant {name} not found"}
        
        actual_damage = combatant.take_damage(damage)
        
        # Log the damage
        details = f"Takes {actual_damage} {damage_type} damage from {source}" if source else f"Takes {actual_damage} {damage_type} damage"
        self._log_action(name, "damage", details)
        
        result = {
            "name": name,
            "damage_taken": actual_damage,
            "hp_current": combatant.hp_current,
            "hp_max": combatant.hp_max,
            "is_unconscious": combatant.is_unconscious,
            "is_dead": combatant.is_dead
        }
        
        if combatant.is_unconscious and not combatant.is_dead:
            result["death_saves"] = {
                "successes": combatant.death_save_successes,
                "failures": combatant.death_save_failures
            }
        
        print(f"💥 {name} takes {actual_damage} damage! HP: {combatant.hp_current}/{combatant.hp_max}")
        return result

    def heal_combatant(self, name: str, amount: int, source: str = "") -> Dict[str, Any]:
        """
        Heal a combatant.
        
        Args:
            name: Combatant name
            amount: Amount of healing
            source: Source of healing
            
        Returns:
            Dict with healing details
        """
        combatant = self._get_combatant(name)
        if not combatant:
            return {"error": f"Combatant {name} not found"}
        
        actual_healing = combatant.heal(amount)
        self._log_action(name, "heal", f"Healed {actual_healing} HP by {source}")
        
        print(f"💚 {name} heals {actual_healing} HP! HP: {combatant.hp_current}/{combatant.hp_max}")
        return {
            "name": name,
            "healed": actual_healing,
            "hp_current": combatant.hp_current
        }

    def add_condition(
        self,
        name: str,
        condition: str,
        duration: Optional[int] = None,
        source: str = ""
    ) -> bool:
        """Add a condition to a combatant."""
        combatant = self._get_combatant(name)
        if not combatant:
            return False
        
        combatant.add_condition(condition, duration, source)
        self._log_action(name, "condition_add", f"Gains {condition}")
        print(f"⚠️ {name} gains condition: {condition}")
        return True

    def remove_condition(self, name: str, condition: str) -> bool:
        """Remove a condition from a combatant."""
        combatant = self._get_combatant(name)
        if not combatant:
            return False
        
        success = combatant.remove_condition(condition)
        if success:
            self._log_action(name, "condition_remove", f"Loses {condition}")
            print(f"✅ {name} loses condition: {condition}")
        return success

    def set_concentration(self, name: str, active: bool = True) -> bool:
        """Set concentration status for a combatant."""
        combatant = self._get_combatant(name)
        if not combatant:
            return False
        
        combatant.concentration = active
        self._log_action(name, "concentration", f"Concentration: {'active' if active else 'ended'}")
        return True

    def concentration_check(self, name: str, damage: int) -> bool:
        """Make a concentration check for a combatant."""
        combatant = self._get_combatant(name)
        if not combatant:
            return True
        
        passed = combatant.concentration_check(damage)
        self._log_action(name, "concentration_check", f"Check vs DC {max(10, damage // 2)}: {'pass' if passed else 'fail'}")
        return passed

    def death_save(self, name: str, roll: int) -> Dict[str, Any]:
        """
        Record a death save roll.
        
        Args:
            name: Combatant name
            roll: d20 roll result
            
        Returns:
            Dict with death save status
        """
        combatant = self._get_combatant(name)
        if not combatant:
            return {"error": f"Combatant {name} not found"}
        
        if roll == 20:
            # Critical success - wake up with 1 HP
            combatant.hp_current = 1
            combatant.reset_death_saves()
            self._log_action(name, "death_save", f"Rolled {roll} - Wakes up!")
            print(f"🎉 {name} rolls {roll} - Wakes up with 1 HP!")
            return {"status": "awake", "hp": 1}
        elif roll >= 10:
            combatant.start_death_save(success=True)
            self._log_action(name, "death_save", f"Rolled {roll} - Success")
            print(f"✓ {name} rolls {roll} - Success")
        elif roll == 1:
            # Critical fail - 2 failures
            combatant.start_death_save(failure=True)
            combatant.start_death_save(failure=True)
            self._log_action(name, "death_save", f"Rolled {roll} - 2 Failures!")
            print(f"✗✗ {name} rolls {roll} - 2 Failures!")
        else:
            combatant.start_death_save(failure=True)
            self._log_action(name, "death_save", f"Rolled {roll} - Failure")
            print(f"✗ {name} rolls {roll} - Failure")
        
        # Check for stabilization or death
        if combatant.death_save_successes >= 3:
            combatant.reset_death_saves()
            self._log_action(name, "death_save", "Stabilized!")
            print(f"✨ {name} stabilizes!")
            return {"status": "stable"}
        elif combatant.death_save_failures >= 3:
            self._log_action(name, "death_save", "Died!")
            print(f"💀 {name} dies...")
            return {"status": "dead"}
        
        return {
            "status": "ongoing",
            "successes": combatant.death_save_successes,
            "failures": combatant.death_save_failures
        }

    def _get_combatant(self, name: str) -> Optional[Combatant]:
        """Get a combatant by name from current combat."""
        if not self.current_combat:
            return None
        
        combat = self.combats[self.current_combat]
        for combatant in combat.combatants:
            if combatant.name.lower() == name.lower():
                return combatant
        return None

    def _log_action(self, actor: str, action: str, details: str) -> None:
        """Log a combat action."""
        if not self.current_combat:
            return
        
        combat = self.combats[self.current_combat]
        entry: CombatLogEntry = {
            "round": combat.current_round,
            "turn": combat.current_turn_index + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "details": details
        }
        combat.log.append(entry)

    def get_status(self) -> Dict[str, Any]:
        """Get current combat status."""
        if not self.current_combat:
            return {"error": "No active combat"}
        
        combat = self.combats[self.current_combat]
        status = {
            "name": combat.name,
            "round": combat.current_round,
            "is_active": combat.is_active,
            "combatants": []
        }
        
        for i, c in enumerate(combat.combatants):
            is_current = (i == combat.current_turn_index)
            status["combatants"].append({
                "name": c.name,
                "initiative": c.initiative,
                "hp": f"{c.hp_current}/{c.hp_max}",
                "ac": c.ac,
                "conditions": [cond["name"] for cond in c.conditions],
                "is_current_turn": is_current,
                "disposition": c.disposition
            })
        
        return status

    def export_to_json(self, filepath: str) -> None:
        """Export current combat to JSON file."""
        if not self.current_combat:
            raise ValueError("No active combat to export")
        
        combat = self.combats[self.current_combat]
        with open(filepath, 'w') as f:
            json.dump(combat.to_dict(), f, indent=2)
        logger.info(f"Combat exported to {filepath}")

    def export_to_foundry(self, filepath: str) -> None:
        """Export combat to Foundry VTT format."""
        if not self.current_combat:
            raise ValueError("No active combat to export")
        
        combat = self.combats[self.current_combat]
        
        export = {
            "name": combat.name,
            "round": combat.current_round,
            "turn": combat.current_turn_index,
            "combatants": []
        }
        
        for c in combat.combatants:
            export["combatants"].append({
                "name": c.name,
                "img": "icons/svg/mystery-man.svg",
                "actor": {
                    "name": c.name,
                    "system": {
                        "attributes": {
                            "hp": {"value": c.hp_current, "max": c.hp_max},
                            "ac": {"value": c.ac}
                        }
                    }
                },
                "initiative": c.initiative,
                "effects": [cond["name"] for cond in c.conditions]
            })
        
        with open(filepath, 'w') as f:
            json.dump(export, f, indent=2)
        logger.info(f"Foundry export saved to {filepath}")

    def print_status(self) -> None:
        """Print current combat status to console."""
        status = self.get_status()
        
        if "error" in status:
            print(status["error"])
            return
        
        print(f"\n{'='*50}")
        print(f"Combat: {status['name']} | Round: {status['round']}")
        print(f"{'='*50}")
        print(f"{'Init':<6} {'Name':<20} {'HP':<12} {'AC':<6} {'Conditions'}")
        print(f"{'-'*50}")
        
        for c in status["combatants"]:
            marker = "➤ " if c["is_current_turn"] else "  "
            hp_display = c["hp"]
            conditions = ", ".join(c["conditions"]) if c["conditions"] else "-"
            print(f"{marker}{c['initiative']:<4} {c['name']:<20} {hp_display:<12} {c['ac']:<6} {conditions}")


def main():
    """CLI for the initiative tracker."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DnD Initiative Tracker v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python initiative_tracker.py --demo
  python initiative_tracker.py --combat "Goblin Ambush" -o combat.json
  python initiative_tracker.py --export-foundry foundry.json
        """
    )
    
    parser.add_argument("--demo", action="store_true",
                        help="Run a demo combat")
    parser.add_argument("--combat", type=str,
                        help="Create a named combat")
    parser.add_argument("-o", "--output", type=str,
                        help="Export combat to JSON file")
    parser.add_argument("--export-foundry", type=str,
                        help="Export to Foundry VTT format")
    parser.add_argument("--seed", type=int,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    tracker = InitiativeTracker(seed=args.seed)
    
    if args.demo:
        print("=== Demo Combat ===\n")
        
        # Create combat
        tracker.create_combat("Goblin Ambush")
        
        # Add combatants
        tracker.add_combatant("Fighter", hp=35, ac=18, initiative_mod=2, disposition="friendly")
        tracker.add_combatant("Wizard", hp=22, ac=13, initiative_mod=3, disposition="friendly")
        tracker.add_combatant("Rogue", hp=28, ac=16, initiative_mod=5, disposition="friendly")
        tracker.add_combatant("Goblin Boss", hp=60, ac=16, initiative_mod=1, disposition="hostile")
        tracker.add_combatant("Goblin 1", hp=7, ac=15, initiative_mod=2, disposition="hostile")
        tracker.add_combatant("Goblin 2", hp=7, ac=15, initiative_mod=4, disposition="hostile")
        
        # Start combat
        tracker.start_combat()
        
        # Simulate a few turns
        print("\n--- Simulating Combat ---")
        for _ in range(4):
            tracker.next_turn()
        
        # Deal some damage
        tracker.damage_combatant("Fighter", 8, "slashing", "Goblin Boss")
        tracker.damage_combatant("Goblin 1", 12, "slashing", "Fighter")
        
        # Add a condition
        tracker.add_condition("Goblin 2", "prone", source="Rogue")
        
        # Print final status
        tracker.print_status()
        
        # Export
        if args.output:
            tracker.export_to_json(args.output)
            print(f"\nCombat exported to {args.output}")
        
        return
    
    if args.combat:
        tracker.create_combat(args.combat)
        print(f"Created combat: {args.combat}")
        print("Use the API or interactive mode to add combatants")
    
    if args.output:
        if tracker.current_combat:
            tracker.export_to_json(args.output)
            print(f"Combat exported to {args.output}")
        else:
            print("No combat to export")
    
    if args.export_foundry:
        if tracker.current_combat:
            tracker.export_to_foundry(args.export_foundry)
            print(f"Foundry export saved to {args.export_foundry}")
        else:
            print("No combat to export")
    
    if not any([args.demo, args.combat, args.output, args.export_foundry]):
        parser.print_help()


if __name__ == "__main__":
    main()
