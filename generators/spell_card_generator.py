#!/usr/bin/env python3
"""
DnD Spell Card Generator v1.0

Generate printable spell cards from SRD spell data.
Supports filtering by class, level, and school.
Exports to JSON, text, and markdown formats.

Features:
- Filter spells by class, level, and school
- Generate compact spell cards for printing
- Export to multiple formats (JSON, Markdown, Text)
- Spell list summaries by class
- Quick reference cards
"""

import json
import logging
from typing import Dict, List, Optional, Any, TypedDict
from pathlib import Path
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class Spell(TypedDict):
    """Type definition for spell data."""
    name: str
    level: int
    school: str
    classes: List[str]


class SpellCard(TypedDict):
    """Type definition for generated spell card."""
    name: str
    level: int
    school: str
    classes: List[str]
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    higher_levels: str


class SpellCardGenerator:
    """Generate spell cards from SRD data."""

    # Spell descriptions (expanded from basic SRD data)
    SPELL_DESCRIPTIONS = {
        "Fireball": {
            "casting_time": "1 action",
            "range": "150 feet",
            "components": "V, S, M (bat fur and sulfur)",
            "duration": "Instantaneous",
            "description": "A bright streak flashes from your finger to a point you choose within range and bursts into a low roar with an explosion of flame. Each creature in a 20-foot-radius sphere must make a Dexterity saving throw. A target takes 8d6 fire damage on a failed save, or half as much on a successful one.",
            "higher_levels": "When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd."
        },
        "Magic Missile": {
            "casting_time": "1 action",
            "range": "120 feet",
            "components": "V, S",
            "duration": "Instantaneous",
            "description": "You create three glowing darts of magical force. Each dart hits a creature of your choice that you can see within range. A dart deals 1d4+1 force damage to its target.",
            "higher_levels": "When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st."
        },
        "Cure Wounds": {
            "casting_time": "1 action",
            "range": "Touch",
            "components": "V, S",
            "duration": "Instantaneous",
            "description": "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier.",
            "higher_levels": "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st."
        },
        "Healing Word": {
            "casting_time": "1 bonus action",
            "range": "60 feet",
            "components": "V",
            "duration": "Instantaneous",
            "description": "A creature of your choice that you can see within range regains hit points equal to 1d4 + your spellcasting ability modifier.",
            "higher_levels": "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d4 for each slot level above 1st."
        },
        "Shield": {
            "casting_time": "1 reaction",
            "range": "Self",
            "components": "V, S",
            "duration": "1 round",
            "description": "An invisible barrier of magical force appears and protects you. Until the start of your next turn, you have a +5 bonus to AC, including against the triggering attack, and you take no damage from magic missile.",
            "higher_levels": ""
        },
        "Counterspell": {
            "casting_time": "1 reaction",
            "range": "60 feet",
            "components": "S",
            "duration": "Instantaneous",
            "description": "You attempt to interrupt a creature in the process of casting a spell. If the creature is casting a spell of 3rd level or lower, its spell fails. If higher, make an ability check with your spellcasting ability.",
            "higher_levels": "When you cast this spell using a spell slot of 4th level or higher, the interrupted spell has no effect if its level is less than or equal to the level of the spell slot you used."
        },
        "Fly": {
            "casting_time": "1 action",
            "range": "Touch",
            "components": "V, S, M (wing feather)",
            "duration": "Concentration, up to 10 minutes",
            "description": "You touch a willing creature. The target gains a flying speed of 60 feet for the duration.",
            "higher_levels": "When you cast this spell using a spell slot of 4th level or higher, you can target one additional creature for each slot level above 3rd."
        },
        "Haste": {
            "casting_time": "1 action",
            "range": "30 feet",
            "components": "V, S, M (shaving of licorice root)",
            "duration": "Concentration, up to 1 minute",
            "description": "Choose a willing creature. Until the spell ends, the target's speed is doubled, it gains a +2 bonus to AC, it has advantage on Dexterity saving throws, and it gains an additional action on each turn.",
            "higher_levels": ""
        },
        "Polymorph": {
            "casting_time": "1 action",
            "range": "60 feet",
            "components": "V, S, M (caterpillar cocoon)",
            "duration": "Concentration, up to 1 hour",
            "description": "Transform a creature into a different creature. The new form can be any beast with CR equal to or less than the target's. The target assumes the beast's HP and game statistics.",
            "higher_levels": ""
        },
        "Dimension Door": {
            "casting_time": "1 action",
            "range": "500 feet",
            "components": "V",
            "duration": "Instantaneous",
            "description": "You teleport yourself to a destination within range. You can bring one willing creature of your size or smaller.",
            "higher_levels": ""
        },
        "Invisibility": {
            "casting_time": "1 action",
            "range": "Touch",
            "components": "V, S, M (eyelash in gum arabic)",
            "duration": "Concentration, up to 1 hour",
            "description": "A creature you touch becomes invisible until the spell ends. Anything the target is wearing or carrying is invisible as long as it is on the target's person.",
            "higher_levels": "When you cast this spell using a spell slot of 3rd level or higher, you can target one additional creature for each slot level above 2nd."
        },
        "Misty Step": {
            "casting_time": "1 bonus action",
            "range": "Self",
            "components": "V",
            "duration": "Instantaneous",
            "description": "You teleport up to 30 feet to an unoccupied space that you can see.",
            "higher_levels": ""
        },
        "Lightning Bolt": {
            "casting_time": "1 action",
            "range": "Self (100-foot line)",
            "components": "V, S, M (fur and amber rod)",
            "duration": "Instantaneous",
            "description": "A stroke of lightning forms a line 100 feet long and 5 feet wide. Each creature in that line must make a Dexterity saving throw, taking 8d6 lightning damage on a failed save.",
            "higher_levels": "When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd."
        },
        "Dispel Magic": {
            "casting_time": "1 action",
            "range": "120 feet",
            "components": "V, S",
            "duration": "Instantaneous",
            "description": "Choose one creature, object, or magical effect within range. Any spell of 3rd level or lower on the target ends. For higher spells, make an ability check.",
            "higher_levels": "When you cast this spell using a spell slot of 4th level or higher, you automatically end spells of that level or lower."
        },
        "Bless": {
            "casting_time": "1 action",
            "range": "30 feet",
            "components": "V, S, M (holy water)",
            "duration": "Concentration, up to 1 minute",
            "description": "You bless up to three creatures. Whenever a target makes an attack roll or saving throw before the spell ends, it can roll a d4 and add it to the roll.",
            "higher_levels": "When you cast this spell using a spell slot of 2nd level or higher, you can target one additional creature for each slot level above 1st."
        },
        "Hex": {
            "casting_time": "1 bonus action",
            "range": "90 feet",
            "components": "V, S, M (petrified eye)",
            "duration": "Concentration, up to 1 hour",
            "description": "Choose a creature. You have advantage on Wisdom checks to track it. When you hit it with an attack, it takes an extra 1d6 necrotic damage.",
            "higher_levels": "When you cast this spell using a spell slot of 3rd or 4th level, duration is 8 hours. 5th or higher: 24 hours."
        },
        "Eldritch Blast": {
            "casting_time": "1 action",
            "range": "120 feet",
            "components": "V, S",
            "duration": "Instantaneous",
            "description": "A beam of crackling energy streaks toward a creature. Make a ranged spell attack. On hit, target takes 1d10 force damage.",
            "higher_levels": "The spell creates more beams at higher levels: 2 at 5th, 3 at 11th, 4 at 17th level."
        },
        "Guidance": {
            "casting_time": "1 action",
            "range": "Touch",
            "components": "V, S",
            "duration": "Concentration, up to 1 minute",
            "description": "You touch one willing creature. It can roll a d4 and add it to one ability check of its choice.",
            "higher_levels": ""
        },
        "Detect Magic": {
            "casting_time": "1 action",
            "range": "Self",
            "components": "V, S",
            "duration": "Concentration, up to 10 minutes",
            "description": "You sense the presence of magic within 30 feet. You can use your action to see a faint aura around visible magical effects.",
            "higher_levels": ""
        },
        "Hold Person": {
            "casting_time": "1 action",
            "range": "60 feet",
            "components": "V, S, M (iron rod)",
            "duration": "Concentration, up to 1 minute",
            "description": "A humanoid you can see must make a Wisdom saving throw or be paralyzed. At the end of each turn, target makes another save.",
            "higher_levels": "When you cast this spell using a spell slot of 3rd level or higher, you can target one additional humanoid for each slot level above 2nd."
        }
    }

    # School icons/colors for visual reference
    SCHOOL_INFO = {
        "abjuration": {"color": "🔵", "description": "Protection"},
        "conjuration": {"color": "🟡", "description": "Transportation"},
        "divination": {"color": "🟣", "description": "Knowledge"},
        "enchantment": {"color": "🔴", "description": "Influence"},
        "evocation": {"color": "🟠", "description": "Energy"},
        "illusion": {"color": "🔷", "description": "Deception"},
        "necromancy": {"color": "🟢", "description": "Life/Death"},
        "transmutation": {"color": "⚪", "description": "Change"}
    }

    def __init__(self, data_dir: Optional[str] = None, seed: Optional[int] = None):
        """
        Initialize the spell card generator.
        
        Args:
            data_dir: Directory containing spell data files
            seed: Optional random seed
        """
        import random
        if seed is not None:
            random.seed(seed)

        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent / "data"
        self.spells: List[Spell] = []
        self._load_spells()

    def _load_spells(self):
        """Load spell data from SRD file."""
        spells_file = self.data_dir / "srd_spells.json"
        if spells_file.exists():
            with open(spells_file, 'r') as f:
                data = json.load(f)
                self.spells = data.get("spells", [])
                self.schools = data.get("schools", [])
                self.classes = data.get("classes", [])
            logger.debug(f"Loaded {len(self.spells)} spells")
        else:
            logger.warning(f"Spell data not found at {spells_file}")
            self.spells = []
            self.schools = []
            self.classes = []

    def filter_spells(
        self,
        char_class: Optional[str] = None,
        level: Optional[int] = None,
        school: Optional[str] = None,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None
    ) -> List[Spell]:
        """
        Filter spells by criteria.
        
        Args:
            char_class: Filter by character class
            level: Filter by exact spell level
            school: Filter by school of magic
            min_level: Minimum spell level
            max_level: Maximum spell level
            
        Returns:
            List of matching spells
        """
        filtered = self.spells
        
        if char_class:
            filtered = [s for s in filtered if char_class.lower() in [c.lower() for c in s.get("classes", [])]]
        
        if level is not None:
            filtered = [s for s in filtered if s.get("level") == level]
        
        if school:
            filtered = [s for s in filtered if s.get("school", "").lower() == school.lower()]
        
        if min_level is not None:
            filtered = [s for s in filtered if s.get("level", 0) >= min_level]
        
        if max_level is not None:
            filtered = [s for s in filtered if s.get("level", 0) <= max_level]
        
        return filtered

    def generate_spell_card(self, spell_name: str) -> Optional[SpellCard]:
        """
        Generate a detailed spell card for a specific spell.
        
        Args:
            spell_name: Name of the spell
            
        Returns:
            SpellCard dict or None if not found
        """
        spell = None
        for s in self.spells:
            if s["name"].lower() == spell_name.lower():
                spell = s
                break
        
        if not spell:
            return None
        
        # Get extended description
        desc = self.SPELL_DESCRIPTIONS.get(spell["name"], {})
        
        return {
            "name": spell["name"],
            "level": spell["level"],
            "school": spell.get("school", "unknown"),
            "classes": spell.get("classes", []),
            "casting_time": desc.get("casting_time", "1 action"),
            "range": desc.get("range", "Varies"),
            "components": desc.get("components", "V, S"),
            "duration": desc.get("duration", "Instantaneous"),
            "description": desc.get("description", "No description available."),
            "higher_levels": desc.get("higher_levels", "")
        }

    def generate_spell_list(
        self,
        char_class: str,
        format: str = "text"
    ) -> str:
        """
        Generate a spell list for a specific class.
        
        Args:
            char_class: Character class name
            format: Output format (text, markdown, json)
            
        Returns:
            Formatted spell list
        """
        spells = self.filter_spells(char_class=char_class)
        
        # Group by level
        by_level: Dict[int, List[Spell]] = {}
        for spell in spells:
            level = spell.get("level", 0)
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(spell)
        
        if format == "json":
            return json.dumps({
                "class": char_class,
                "total_spells": len(spells),
                "by_level": {str(k): [s["name"] for s in v] for k, v in by_level.items()}
            }, indent=2)
        
        elif format == "markdown":
            output = f"# {char_class.capitalize()} Spell List\n\n"
            output += f"**Total Spells:** {len(spells)}\n\n"
            
            for level in sorted(by_level.keys()):
                level_name = "Cantrips" if level == 0 else f"Level {level}"
                output += f"## {level_name}\n\n"
                for spell in sorted(by_level[level], key=lambda s: s["name"]):
                    school_icon = self.SCHOOL_INFO.get(spell.get("school", ""), {}).get("color", "⚪")
                    output += f"- {school_icon} **{spell['name']}** ({spell.get('school', 'unknown')})\n"
                output += "\n"
            
            return output
        
        else:  # text format
            output = f"=== {char_class.capitalize()} Spell List ===\n"
            output += f"Total Spells: {len(spells)}\n\n"
            
            for level in sorted(by_level.keys()):
                level_name = "Cantrips" if level == 0 else f"Level {level}"
                output += f"\n{level_name}:\n"
                output += "-" * 40 + "\n"
                for spell in sorted(by_level[level], key=lambda s: s["name"]):
                    output += f"  • {spell['name']} ({spell.get('school', 'unknown')})\n"
            
            return output

    def generate_quick_reference(self, char_class: str, levels: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Generate a quick reference card for a class.
        
        Args:
            char_class: Character class
            levels: Specific levels to include (None = all)
            
        Returns:
            Quick reference dict
        """
        spells = self.filter_spells(char_class=char_class)
        
        if levels:
            spells = [s for s in spells if s.get("level") in levels]
        
        # Create compact reference
        reference = {
            "class": char_class,
            "generated": datetime.now(timezone.utc).isoformat(),
            "spells": []
        }
        
        for spell in sorted(spells, key=lambda s: (s.get("level", 0), s["name"])):
            desc = self.SPELL_DESCRIPTIONS.get(spell["name"], {})
            reference["spells"].append({
                "name": spell["name"],
                "level": spell["level"],
                "school": spell.get("school", ""),
                "casting_time": desc.get("casting_time", ""),
                "range": desc.get("range", ""),
                "duration": desc.get("duration", "")
            })
        
        return reference

    def export_spell_cards(
        self,
        spells: Optional[List[str]] = None,
        char_class: Optional[str] = None,
        level: Optional[int] = None,
        format: str = "markdown",
        filepath: Optional[str] = None
    ) -> str:
        """
        Export spell cards to file or string.
        
        Args:
            spells: List of specific spell names
            char_class: Filter by class
            level: Filter by level
            format: Output format
            filepath: Output file path
            
        Returns:
            Generated content string
        """
        # Get spells to export
        if spells:
            spell_list = [self.generate_spell_card(name) for name in spells]
            spell_list = [s for s in spell_list if s is not None]
        else:
            filtered = self.filter_spells(char_class=char_class, level=level)
            spell_list = [self.generate_spell_card(s["name"]) for s in filtered]
            spell_list = [s for s in spell_list if s is not None]
        
        if format == "json":
            content = json.dumps(spell_list, indent=2)
        
        elif format == "markdown":
            content = "# Spell Cards\n\n"
            for card in spell_list:
                school_info = self.SCHOOL_INFO.get(card.get("school", ""), {})
                content += f"## {school_info.get('color', '')} {card['name']}\n"
                content += f"*{card['level']}{'st' if card['level'] == 1 else 'nd' if card['level'] == 2 else 'rd' if card['level'] == 3 else 'th'} level {card['school']}*\n\n"
                content += f"- **Casting Time:** {card['casting_time']}\n"
                content += f"- **Range:** {card['range']}\n"
                content += f"- **Components:** {card['components']}\n"
                content += f"- **Duration:** {card['duration']}\n\n"
                content += f"**Description:** {card['description']}\n\n"
                if card.get('higher_levels'):
                    content += f"**At Higher Levels:** {card['higher_levels']}\n\n"
                content += "---\n\n"
        
        else:  # text
            content = "=== Spell Cards ===\n\n"
            for card in spell_list:
                content += f"{card['name']}\n"
                content += f"Level: {card['level']} | School: {card['school']}\n"
                content += f"Casting: {card['casting_time']} | Range: {card['range']}\n"
                content += f"Components: {card['components']} | Duration: {card['duration']}\n"
                content += f"\n{card['description']}\n"
                if card.get('higher_levels'):
                    content += f"\nHigher Levels: {card['higher_levels']}\n"
                content += "\n" + "-" * 50 + "\n\n"
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(content)
            logger.info(f"Exported {len(spell_list)} spell cards to {filepath}")
        
        return content

    def list_spells_by_school(self) -> Dict[str, List[str]]:
        """Return spells grouped by school."""
        by_school: Dict[str, List[str]] = {}
        for spell in self.spells:
            school = spell.get("school", "unknown")
            if school not in by_school:
                by_school[school] = []
            by_school[school].append(spell["name"])
        return by_school

    def list_classes(self) -> List[str]:
        """Return list of available classes."""
        return self.classes

    def list_schools(self) -> List[str]:
        """Return list of available schools."""
        return self.schools


def main():
    """CLI for spell card generator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DnD Spell Card Generator v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python spell_card_generator.py --class wizard --level 3
  python spell_card_generator.py --spell Fireball --format markdown
  python spell_card_generator.py --list wizard -o wizard_spells.md
  python spell_card_generator.py --quick-ref wizard --levels 1 2 3
        """
    )
    
    parser.add_argument("--class", dest="char_class",
                        help="Filter by character class")
    parser.add_argument("--level", type=int,
                        help="Filter by spell level")
    parser.add_argument("--school",
                        help="Filter by school of magic")
    parser.add_argument("--spell", type=str,
                        help="Generate card for specific spell")
    parser.add_argument("--list", action="store_true",
                        help="List spells for a class")
    parser.add_argument("--quick-ref", action="store_true",
                        help="Generate quick reference card")
    parser.add_argument("--levels", type=int, nargs="+",
                        help="Specific levels for quick reference")
    parser.add_argument("--format", default="text",
                        choices=["text", "markdown", "json"],
                        help="Output format")
    parser.add_argument("-o", "--output",
                        help="Output file path")
    parser.add_argument("--list-classes", action="store_true",
                        help="List available classes")
    parser.add_argument("--list-schools", action="store_true",
                        help="List available schools")
    
    args = parser.parse_args()
    
    generator = SpellCardGenerator()
    
    if args.list_classes:
        print("Available Classes:")
        for cls in generator.list_classes():
            print(f"  • {cls.capitalize()}")
        return
    
    if args.list_schools:
        print("Available Schools:")
        for school in generator.list_schools():
            icon = generator.SCHOOL_INFO.get(school, {}).get("color", "")
            print(f"  {icon} {school.capitalize()}")
        return
    
    if args.spell:
        card = generator.generate_spell_card(args.spell)
        if card:
            content = generator.export_spell_cards(spells=[args.spell], format=args.format)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(content)
                print(f"Spell card exported to {args.output}")
            else:
                print(content)
        else:
            print(f"Spell '{args.spell}' not found")
        return
    
    if args.list:
        if not args.char_class:
            print("Error: --class required for --list")
            return
        content = generator.generate_spell_list(args.char_class, format=args.format)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(content)
            print(f"Spell list exported to {args.output}")
        else:
            print(content)
        return
    
    if args.quick_ref:
        if not args.char_class:
            print("Error: --class required for --quick-ref")
            return
        ref = generator.generate_quick_reference(args.char_class, args.levels)
        content = json.dumps(ref, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(content)
            print(f"Quick reference exported to {args.output}")
        else:
            print(content)
        return
    
    # Default: show filtered spells
    spells = generator.filter_spells(
        char_class=args.char_class,
        level=args.level,
        school=args.school
    )
    
    if not spells:
        print("No spells found matching criteria")
        return
    
    print(f"=== Spells Found ({len(spells)}) ===\n")
    for spell in sorted(spells, key=lambda s: (s.get("level", 0), s["name"])):
        level_str = "Cantrip" if spell["level"] == 0 else f"Level {spell['level']}"
        school = spell.get("school", "unknown")
        classes = ", ".join(spell.get("classes", []))
        print(f"• {spell['name']} - {level_str} {school}")
        print(f"  Classes: {classes}")


if __name__ == "__main__":
    main()
