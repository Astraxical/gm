#!/usr/bin/env python3
"""
DnD Lair Action Generator v1.0

Generate custom lair actions, legendary actions, and boss mechanics.
Make your boss fights memorable and unique.

Features:
- Lair action generation
- Legendary action creation
- Regional effects
- Boss phase mechanics
- Custom ability design
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class LairAction:
    """A lair action."""
    name: str
    description: str
    initiative: int = 20
    save_dc: int = 15
    damage: str = ""
    effect_type: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "initiative": self.initiative,
            "save_dc": self.save_dc,
            "damage": self.damage,
            "effect_type": self.effect_type
        }


@dataclass
class LegendaryAction:
    """A legendary action."""
    name: str
    description: str
    cost: int = 1
    usage: str = "At the end of another creature's turn"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "cost": self.cost,
            "usage": self.usage
        }


@dataclass
class BossMechanic:
    """A boss phase mechanic."""
    name: str
    trigger: str
    effect: str
    flavor: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "trigger": self.trigger,
            "effect": self.effect,
            "flavor": self.flavor
        }


class LairActionGenerator:
    """Generate lair actions and boss mechanics."""

    # Lair action templates by theme
    LAIR_ACTION_TABLES = {
        "dungeon": [
            {"name": "Shifting Walls", "description": "Walls move, creating or blocking passages", "dc": 15, "type": "terrain"},
            {"name": "Falling Debris", "description": "Ceiling collapses in areas", "dc": 15, "damage": "2d6 bludgeoning", "type": "damage"},
            {"name": "Magical Darkness", "description": "Shadows deepen, creating heavily obscured areas", "dc": 0, "type": "control"},
            {"name": "Glyph Activation", "description": "Ancient glyphs fire energy beams", "dc": 16, "damage": "3d6 force", "type": "damage"},
            {"name": "Portcullis Drop", "description": "Gates fall, separating the party", "dc": 0, "type": "control"},
            {"name": "Poison Gas", "description": "Toxic fumes fill the chamber", "dc": 15, "damage": "2d6 poison", "type": "damage"},
        ],
        "cave": [
            {"name": "Stalactite Fall", "description": "Sharp rocks drop from ceiling", "dc": 15, "damage": "2d8 piercing", "type": "damage"},
            {"name": "Underground Stream", "description": "Water floods the area", "dc": 0, "type": "terrain"},
            {"name": "Earth Tremor", "description": "Ground shakes, knocking creatures prone", "dc": 15, "type": "control"},
            {"name": "Rockfall", "description": "Boulders cascade down", "dc": 16, "damage": "3d8 bludgeoning", "type": "damage"},
            {"name": "Cave-In", "description": "Section of cave collapses", "dc": 17, "damage": "4d6 bludgeoning", "type": "damage"},
        ],
        "castle": [
            {"name": "Arrow Volley", "description": "Defensive turrets fire", "dc": 15, "damage": "2d8 piercing", "type": "damage"},
            {"name": "Portcullis Trap", "description": "Gates trap creatures", "dc": 16, "type": "control"},
            {"name": "Boiling Oil", "description": "Hot oil pours from above", "dc": 15, "damage": "3d6 fire", "type": "damage"},
            {"name": "Drawbridge Movement", "description": "Access points change", "dc": 0, "type": "terrain"},
            {"name": "Defender Summoning", "description": "Animated armor awakens", "dc": 0, "type": "summon"},
        ],
        "temple": [
            {"name": "Divine Light", "description": "Beams of radiant energy", "dc": 16, "damage": "3d6 radiant", "type": "damage"},
            {"name": "Consecrated Ground", "description": "Area becomes holy/unholy", "dc": 0, "type": "buff"},
            {"name": "Statue Animation", "description": "Stone guardians awaken", "dc": 0, "type": "summon"},
            {"name": "Prayer Amplification", "description": "Magical effects intensify", "dc": 0, "type": "buff"},
            {"name": "Sacred Flame", "description": "Fire erupts from altars", "dc": 15, "damage": "2d6 fire", "type": "damage"},
        ],
        "forest": [
            {"name": "Entangling Vines", "description": "Plants grab creatures", "dc": 15, "type": "control"},
            {"name": "Falling Branches", "description": "Heavy limbs crash down", "dc": 14, "damage": "2d6 bludgeoning", "type": "damage"},
            {"name": "Poison Spores", "description": "Fungal clouds spread", "dc": 15, "damage": "2d6 poison", "type": "damage"},
            {"name": "Animal Swarm", "description": "Creatures attack intruders", "dc": 0, "type": "summon"},
            {"name": "Terrain Shift", "description": "Roots reshape the ground", "dc": 0, "type": "terrain"},
        ],
        "underdark": [
            {"name": "Bioluminescent Burst", "description": "Sudden bright light blinds", "dc": 14, "type": "control"},
            {"name": "Fungal Explosion", "description": "Spore clouds erupt", "dc": 15, "damage": "2d6 poison", "type": "damage"},
            {"name": "Crystal Growth", "description": "Sharp crystals erupt from surfaces", "dc": 15, "damage": "2d8 piercing", "type": "damage"},
            {"name": "Darkness Deepens", "description": "Magical darkness spreads", "dc": 0, "type": "control"},
            {"name": "Tunnel Collapse", "description": "Passages seal", "dc": 16, "type": "terrain"},
        ],
    }

    # Legendary action templates
    LEGENDARY_ACTION_TABLES = {
        "physical": [
            {"name": "Tail Attack", "description": "Make a tail attack", "cost": 1},
            {"name": "Wing Buffet", "description": "Creatures must save or be knocked prone", "cost": 2},
            {"name": "Multiattack", "description": "Make one additional attack", "cost": 1},
            {"name": "Charge", "description": "Move up to speed and attack", "cost": 2},
            {"name": "Knock Back", "description": "Push creature 10 feet", "cost": 1},
        ],
        "magical": [
            {"name": "Cast Cantrip", "description": "Cast a cantrip", "cost": 1},
            {"name": "Energy Burst", "description": "Deal damage in area", "cost": 2},
            {"name": "Teleport", "description": "Teleport up to 30 feet", "cost": 2},
            {"name": "Counterspell", "description": "Attempt to counter a spell", "cost": 2},
            {"name": "Shield", "description": "Gain +5 AC", "cost": 1},
        ],
        "utility": [
            {"name": "Detect", "description": "Make a Perception check", "cost": 1},
            {"name": "Command Minion", "description": "Order ally to move or attack", "cost": 1},
            {"name": "Intimidate", "description": "Frighten a creature", "cost": 2},
            {"name": "Regeneration", "description": "Regain hit points", "cost": 2},
            {"name": "Legendary Resistance", "description": "Succeed on failed save", "cost": 0, "usage": "Reaction to failed save"},
        ],
    }

    # Regional effects
    REGIONAL_EFFECTS = {
        "dungeon": [
            "Torches burn with unnatural colors",
            "Shadows move independently of their sources",
            "Whispers echo through empty corridors",
            "Temperature fluctuates wildly"
        ],
        "cave": [
            "Crystals hum with magical energy",
            "Underground winds create eerie sounds",
            "Bioluminescent fungi pulse rhythmically",
            "Water flows uphill in some areas"
        ],
        "castle": [
            "Banners move without wind",
            "Armor suits turn to watch intruders",
            "Portraits' eyes follow movement",
            "Distant sounds of feasts and battles"
        ],
        "temple": [
            "Incense burns without source",
            "Holy symbols glow faintly",
            "Choir voices echo from nowhere",
            "Prayer answers manifest physically"
        ],
        "forest": [
            "Animals watch silently",
            "Plants turn to follow movement",
            "Fairy lights dance in the distance",
            "Natural sounds suddenly cease"
        ],
    }

    # Boss phase mechanics
    PHASE_MECHANICS = [
        {
            "name": "Enrage",
            "trigger": "HP drops below 50%",
            "effect": "Damage increases by 50%, AC decreases by 2",
            "flavor": "The creature's eyes glow red as it enters a frenzy"
        },
        {
            "name": "Desperate Power",
            "trigger": "HP drops below 25%",
            "effect": "Gains legendary resistance and new abilities",
            "flavor": "Drawing on hidden reserves, the creature transforms"
        },
        {
            "name": "Call Reinforcements",
            "trigger": "Start of round 3",
            "effect": "2d4 minions join the fight",
            "flavor": "A horn sounds as allies arrive"
        },
        {
            "name": "Environmental Shift",
            "trigger": "HP drops below 50%",
            "effect": "Lair actions occur on initiative 10 instead of 20",
            "flavor": "The lair itself responds to the creature's distress"
        },
        {
            "name": "Last Stand",
            "trigger": "HP drops below 10%",
            "effect": "Cannot be reduced below 1 HP for 1 round",
            "flavor": "The creature refuses to fall"
        },
        {
            "name": "Power Surge",
            "trigger": "Every 3 rounds",
            "effect": "Next attack deals double damage",
            "flavor": "Energy crackles around the creature"
        },
    ]

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_lair_actions(self, theme: str = "dungeon", count: int = 3) -> List[LairAction]:
        """Generate lair actions for a theme."""
        table = self.LAIR_ACTION_TABLES.get(theme, self.LAIR_ACTION_TABLES["dungeon"])
        selected = random.sample(table, min(count, len(table)))
        
        return [
            LairAction(
                name=action["name"],
                description=action["description"],
                save_dc=action.get("dc", 15),
                damage=action.get("damage", ""),
                effect_type=action.get("type", "")
            )
            for action in selected
        ]

    def generate_legendary_actions(self, type: str = "mixed", count: int = 3) -> List[LegendaryAction]:
        """Generate legendary actions."""
        if type == "mixed":
            all_actions = []
            for table in self.LEGENDARY_ACTION_TABLES.values():
                all_actions.extend(table)
        else:
            all_actions = self.LEGENDARY_ACTION_TABLES.get(type, self.LEGENDARY_ACTION_TABLES["physical"])
        
        selected = random.sample(all_actions, min(count, len(all_actions)))
        
        return [
            LegendaryAction(
                name=action["name"],
                description=action["description"],
                cost=action.get("cost", 1)
            )
            for action in selected
        ]

    def generate_regional_effects(self, theme: str = "dungeon") -> List[str]:
        """Generate regional effects for a lair."""
        effects = self.REGIONAL_EFFECTS.get(theme, self.REGIONAL_EFFECTS["dungeon"])
        return random.sample(effects, min(3, len(effects)))

    def generate_boss_phases(self, count: int = 2) -> List[BossMechanic]:
        """Generate boss phase mechanics."""
        selected = random.sample(self.PHASE_MECHANICS, min(count, len(self.PHASE_MECHANICS)))
        
        return [
            BossMechanic(
                name=phase["name"],
                trigger=phase["trigger"],
                effect=phase["effect"],
                flavor=phase["flavor"]
            )
            for phase in selected
        ]

    def generate_complete_boss(self, theme: str = "dungeon", cr: int = 10) -> Dict[str, Any]:
        """Generate a complete boss encounter package."""
        return {
            "lair_actions": [la.to_dict() for la in self.generate_lair_actions(theme, 3)],
            "legendary_actions": [la.to_dict() for la in self.generate_legendary_actions("mixed", 3)],
            "regional_effects": self.generate_regional_effects(theme),
            "boss_phases": [p.to_dict() for p in self.generate_boss_phases(3)],
            "legendary_resistance": 3 if cr >= 10 else 0,
        }

    def display_lair(self, boss_data: Dict[str, Any]) -> str:
        """Display complete lair information."""
        lines = []
        lines.append("=" * 70)
        lines.append("LAIR ENCOUNTER PACKAGE")
        lines.append("=" * 70)
        
        lines.append("\n🏰 REGIONAL EFFECTS (Always Active):")
        for effect in boss_data.get("regional_effects", []):
            lines.append(f"   • {effect}")
        
        lines.append("\n⚡ LAIR ACTIONS (Initiative 20):")
        for action in boss_data.get("lair_actions", []):
            lines.append(f"   • {action['name']} (DC {action['save_dc']})")
            lines.append(f"     {action['description']}")
            if action.get('damage'):
                lines.append(f"     Damage: {action['damage']}")
        
        lines.append("\n⭐ LEGENDARY ACTIONS:")
        for action in boss_data.get("legendary_actions", []):
            cost = f" ({action['cost']} actions)" if action['cost'] > 0 else ""
            lines.append(f"   • {action['name']}{cost}")
            lines.append(f"     {action['description']}")
        
        lines.append(f"\n🛡️ LEGENDARY RESISTANCES: {boss_data.get('legendary_resistance', 0)}/day")
        
        lines.append("\n🔄 BOSS PHASE MECHANICS:")
        for phase in boss_data.get("boss_phases", []):
            lines.append(f"   • {phase['name']}")
            lines.append(f"     Trigger: {phase['trigger']}")
            lines.append(f"     Effect: {phase['effect']}")
            if phase.get('flavor'):
                lines.append(f"     Flavor: {phase['flavor']}")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    """CLI for lair action generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD Lair Action Generator v1.0")
    parser.add_argument("-t", "--theme", 
                       choices=["dungeon", "cave", "castle", "temple", "forest", "underdark"],
                       default="dungeon")
    parser.add_argument("--cr", type=int, default=10, help="Boss CR")
    parser.add_argument("--complete", action="store_true", help="Generate complete boss package")
    
    args = parser.parse_args()
    
    generator = LairActionGenerator()
    
    if args.complete:
        boss_data = generator.generate_complete_boss(args.theme, args.cr)
        print(generator.display_lair(boss_data))
    else:
        # Generate individual components
        print("\n=== Lair Actions ===")
        for action in generator.generate_lair_actions(args.theme, 3):
            print(f"\n{action.name} (DC {action.save_dc})")
            print(f"  {action.description}")
            if action.damage:
                print(f"  Damage: {action.damage}")
        
        print("\n=== Legendary Actions ===")
        for action in generator.generate_legendary_actions("mixed", 3):
            cost = f" ({action.cost} actions)" if action.cost > 0 else ""
            print(f"\n{action.name}{cost}")
            print(f"  {action.description}")
        
        print("\n=== Regional Effects ===")
        for effect in generator.generate_regional_effects(args.theme):
            print(f"  • {effect}")


if __name__ == "__main__":
    main()
