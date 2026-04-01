#!/usr/bin/env python3
"""
VTT Export Module

Export encounters, NPCs, and loot in formats compatible with
Foundry VTT, Roll20, and other virtual tabletops.
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime


class VTTExporter:
    """Export DnD content to VTT-compatible formats."""

    # Foundry VTT actor template
    FOUNDRY_ACTOR_TEMPLATE = {
        "name": "",
        "type": "npc",
        "img": "icons/svg/mystery-man.svg",
        "system": {
            "attributes": {
                "hp": {"value": 0, "max": 0},
                "ac": {"value": 10}
            },
            "details": {
                "cr": 0,
                "type": ""
            }
        },
        "token": {
            "name": "",
            "disposition": -1,  # Hostile
            "actorLink": False
        }
    }

    # Roll20 character template
    ROLL20_CHARACTER_TEMPLATE = {
        "charactername": "",
        "attributes": {}
    }

    def __init__(self, platform: str = "foundry"):
        """
        Initialize the VTT exporter.

        Args:
            platform: Target VTT platform ("foundry", "roll20", "generic")
        """
        self.platform = platform.lower()

    def export_encounter(self, encounter: Dict[str, Any],
                       encounter_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Export an encounter to VTT format.

        Args:
            encounter: Encounter dict from EncounterGenerator
            encounter_name: Optional name for the encounter

        Returns:
            VTT-compatible encounter dict
        """
        if self.platform == "foundry":
            return self._export_foundry_encounter(encounter, encounter_name)
        elif self.platform == "roll20":
            return self._export_roll20_encounter(encounter, encounter_name)
        else:
            return self._export_generic_encounter(encounter, encounter_name)

    def _export_foundry_encounter(self, encounter: Dict[str, Any],
                                   name: Optional[str] = None) -> Dict[str, Any]:
        """Export to Foundry VTT format."""
        export = {
            "name": name or f"Encounter {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "combatants": [],
            "metadata": {
                "difficulty": encounter.get("difficulty", "medium"),
                "xp_budget": encounter.get("xp_budget", 0),
                "adjusted_xp": encounter.get("adjusted_xp", 0)
            }
        }

        for monster in encounter.get("monsters", []):
            count = monster.get("count", 1)
            for i in range(count):
                combatant = {
                    "id": str(uuid.uuid4()),
                    "name": f"{monster['name']} {i+1}" if count > 1 else monster["name"],
                    "img": "icons/svg/mystery-man.svg",
                    "actor": {
                        "name": monster["name"],
                        "type": "npc",
                        "system": {
                            "attributes": {
                                "hp": {"value": monster.get("hp", 10), "max": monster.get("hp", 10)},
                                "ac": {"value": monster.get("ac", 10)}
                            },
                            "details": {
                                "cr": self._parse_cr(monster.get("cr", "0.25")),
                                "type": monster.get("type", "humanoid")
                            }
                        }
                    },
                    "token": {
                        "name": f"{monster['name']} {i+1}" if count > 1 else monster["name"],
                        "disposition": -1,
                        "bar1": {"attribute": "attributes.hp"},
                        "bar2": {"attribute": "attributes.ac"}
                    },
                    "initiative": None,
                    "hidden": False
                }
                export["combatants"].append(combatant)

        return export

    def _export_roll20_encounter(self, encounter: Dict[str, Any],
                                  name: Optional[str] = None) -> Dict[str, Any]:
        """Export to Roll20 format."""
        export = {
            "encounter_name": name or f"Encounter {datetime.now().strftime('%Y-%m-%d')}",
            "turn_order": [],
            "npcs": []
        }

        for monster in encounter.get("monsters", []):
            count = monster.get("count", 1)
            for i in range(count):
                npc = {
                    "name": f"{monster['name']} {i+1}" if count > 1 else monster["name"],
                    "hp": monster.get("hp", 10),
                    "ac": monster.get("ac", 10),
                    "cr": self._parse_cr(monster.get("cr", "0.25")),
                    "type": monster.get("type", "humanoid"),
                    "controlled_by": "",
                    "represents": ""
                }
                export["npcs"].append(npc)
                export["turn_order"].append({
                    "id": str(uuid.uuid4()),
                    "name": npc["name"],
                    "initiative": 0
                })

        return export

    def _export_generic_encounter(self, encounter: Dict[str, Any],
                                   name: Optional[str] = None) -> Dict[str, Any]:
        """Export to generic JSON format."""
        return {
            "name": name or "Encounter",
            "difficulty": encounter.get("difficulty", "medium"),
            "xp_budget": encounter.get("xp_budget", 0),
            "monsters": encounter.get("monsters", []),
            "total_xp": encounter.get("total_xp", 0),
            "adjusted_xp": encounter.get("adjusted_xp", 0)
        }

    def export_npc(self, npc: Dict[str, Any],
                   stat_block: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Export an NPC to VTT format.

        Args:
            npc: NPC dict from NPCGenerator
            stat_block: Optional DnD stat block

        Returns:
            VTT-compatible actor dict
        """
        if self.platform == "foundry":
            return self._export_foundry_npc(npc, stat_block)
        elif self.platform == "roll20":
            return self._export_roll20_npc(npc, stat_block)
        else:
            return self._export_generic_npc(npc, stat_block)

    def _export_foundry_npc(self, npc: Dict[str, Any],
                            stat_block: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export NPC to Foundry format."""
        actor = json.loads(json.dumps(self.FOUNDRY_ACTOR_TEMPLATE))  # Deep copy

        # Use first name from full name
        full_name = npc.get("name", "Unknown")
        actor["name"] = full_name
        actor["token"]["name"] = full_name

        # Add stat block data if provided
        if stat_block:
            actor["system"]["attributes"]["hp"]["max"] = stat_block.get("hp", 10)
            actor["system"]["attributes"]["hp"]["value"] = stat_block.get("hp", 10)
            actor["system"]["attributes"]["ac"]["value"] = stat_block.get("ac", 10)
            actor["system"]["details"]["cr"] = self._parse_cr(stat_block.get("cr", "0"))
            actor["system"]["details"]["type"] = stat_block.get("type", "humanoid")

        # Add description
        actor["system"]["details"]["description"] = npc.get("description", "")
        actor["system"]["details"]["personality"] = npc.get("personality", {})
        actor["system"]["details"]["appearance"] = npc.get("appearance", {})

        return actor

    def _export_roll20_npc(self, npc: Dict[str, Any],
                           stat_block: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export NPC to Roll20 format."""
        character = {
            "charactername": npc.get("name", "Unknown"),
            "attributes": {
                "npc_name": npc.get("name", "Unknown"),
                "npc_type": npc.get("race", "human"),
                "npc_class": npc.get("occupation", "commoner"),
                "description": npc.get("description", ""),
                "personality_trait": npc.get("personality", {}).get("trait", ""),
                "ideal": npc.get("personality", {}).get("ideal", ""),
                "bond": "",
                "flaw": npc.get("personality", {}).get("flaw", "")
            }
        }

        if stat_block:
            character["attributes"]["hp"] = stat_block.get("hp", 10)
            character["attributes"]["ac"] = stat_block.get("ac", 10)
            character["attributes"]["cr"] = self._parse_cr(stat_block.get("cr", "0"))

        return character

    def _export_generic_npc(self, npc: Dict[str, Any],
                            stat_block: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export NPC to generic format."""
        export = {
            "name": npc.get("name", "Unknown"),
            "race": npc.get("race", "human"),
            "occupation": npc.get("occupation", "commoner"),
            "description": npc.get("description", ""),
            "personality": npc.get("personality", {}),
            "appearance": npc.get("appearance", {}),
            "voice": npc.get("voice", {}),
            "secret": npc.get("secret", {})
        }

        if stat_block:
            export["stat_block"] = stat_block

        return export

    def export_loot(self, loot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export loot to VTT format.

        Args:
            loot: Loot dict from LootGenerator

        Returns:
            VTT-compatible loot dict
        """
        if self.platform == "foundry":
            return self._export_foundry_loot(loot)
        elif self.platform == "roll20":
            return self._export_roll20_loot(loot)
        else:
            return self._export_generic_loot(loot)

    def _export_foundry_loot(self, loot: Dict[str, Any]) -> Dict[str, Any]:
        """Export loot to Foundry format."""
        items = []

        # Add magic items
        for item in loot.get("magic_items", []):
            foundry_item = {
                "name": item.get("name", "Unknown Item"),
                "type": "equipment",
                "img": "icons/svg/treasure.svg",
                "system": {
                    "description": {
                        "value": item.get("description", "")
                    },
                    "rarity": item.get("rarity", "common"),
                    "properties": [item.get("property", "")]
                }
            }
            items.append(foundry_item)

        # Add currency
        if loot.get("gold_pieces", 0) > 0:
            items.append({
                "name": "Gold Pieces",
                "type": "currency",
                "img": "icons/svg/coins.svg",
                "system": {
                    "quantity": loot.get("gold_pieces", 0)
                }
            })

        return {
            "name": f"Treasure Hoard",
            "items": items,
            "total_value": loot.get("total_value", 0)
        }

    def _export_roll20_loot(self, loot: Dict[str, Any]) -> Dict[str, Any]:
        """Export loot to Roll20 format."""
        return {
            "treasure_name": "Treasure Hoard",
            "gold": loot.get("gold_pieces", 0),
            "gems": loot.get("gems", {}),
            "art_objects": loot.get("art_objects", {}),
            "magic_items": [
                {
                    "name": item.get("name", "Unknown"),
                    "rarity": item.get("rarity", "common"),
                    "description": item.get("property", "")
                }
                for item in loot.get("magic_items", [])
            ]
        }

    def _export_generic_loot(self, loot: Dict[str, Any]) -> Dict[str, Any]:
        """Export loot to generic format."""
        return loot

    def _parse_cr(self, cr: str) -> float:
        """Parse CR string to float."""
        if isinstance(cr, (int, float)):
            return float(cr)
        if "/" in str(cr):
            parts = str(cr).split("/")
            return int(parts[0]) / int(parts[1])
        return float(cr or 0)

    def to_json(self, data: Dict[str, Any], indent: int = 2) -> str:
        """
        Convert data to JSON string.

        Args:
            data: Data dict to convert
            indent: JSON indentation level

        Returns:
            JSON string
        """
        return json.dumps(data, indent=indent)

    def export_to_file(self, data: Dict[str, Any], filepath: str) -> None:
        """
        Export data to a JSON file.

        Args:
            data: Data dict to export
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


def main():
    """CLI for VTT exporter."""
    import argparse
    from encounter_gen import EncounterGenerator
    from npc_gen import NPCGenerator
    from loot_gen import LootGenerator

    parser = argparse.ArgumentParser(
        description="VTT Export Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vtt_export.py --encounter -t forest -o encounter.json
  python vtt_export.py --npc -r elf -o npc.json
  python vtt_export.py --loot --hoard -o treasure.json
  python vtt_export.py --platform roll20 --encounter -o roll20_encounter.json
        """
    )

    parser.add_argument("--platform", default="foundry",
                        choices=["foundry", "roll20", "generic"],
                        help="Target VTT platform")
    parser.add_argument("--encounter", action="store_true",
                        help="Generate and export an encounter")
    parser.add_argument("--npc", action="store_true",
                        help="Generate and export an NPC")
    parser.add_argument("--loot", action="store_true",
                        help="Generate and export loot")
    parser.add_argument("-t", "--terrain", help="Encounter terrain")
    parser.add_argument("-d", "--difficulty", default="medium",
                        choices=["easy", "medium", "hard", "deadly"])
    parser.add_argument("-r", "--race", help="NPC race")
    parser.add_argument("--hoard", action="store_true",
                        help="Generate treasure hoard")
    parser.add_argument("-o", "--output", required=True,
                        help="Output file path")

    args = parser.parse_args()

    exporter = VTTExporter(platform=args.platform)

    if args.encounter:
        enc_gen = EncounterGenerator()
        encounter = enc_gen.generate_encounter(
            difficulty=args.difficulty,
            terrain=args.terrain
        )
        export_data = exporter.export_encounter(encounter)
        exporter.export_to_file(export_data, args.output)
        print(f"Encounter exported to {args.output}")

    elif args.npc:
        npc_gen = NPCGenerator()
        npc = npc_gen.generate_npc(race=args.race or "human")
        export_data = exporter.export_npc(npc)
        exporter.export_to_file(export_data, args.output)
        print(f"NPC exported to {args.output}")

    elif args.loot:
        loot_gen = LootGenerator()
        if args.hoard:
            loot = loot_gen.generate_hoard()
        else:
            loot = loot_gen.generate_magic_item()
        export_data = exporter.export_loot(loot)
        exporter.export_to_file(export_data, args.output)
        print(f"Loot exported to {args.output}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
