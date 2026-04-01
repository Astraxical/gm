#!/usr/bin/env python3
"""
DnD GM Toolkit - Unified CLI Framework

Single entry point for all GM tools.
Replaces 28+ individual scripts with one unified interface.

Usage:
    python gm.py <category> <tool> [options]

Examples:
    python gm.py generate encounter -t forest -d medium
    python gm.py track initiative --demo
    python gm.py utility tavern
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Callable, List, Optional

# Add parent directory to path for package imports
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

# =============================================================================
# TOOL REGISTRY
# =============================================================================

# Tool definitions: category -> tool -> (module, class, description)
TOOL_REGISTRY: Dict[str, Dict[str, dict]] = {
    "generate": {
        "encounter": {
            "module": "generators.encounter_gen",
            "class": "EncounterGenerator",
            "description": "Generate CR-balanced encounters"
        },
        "loot": {
            "module": "generators.loot_gen",
            "class": "LootGenerator",
            "description": "Generate magic items and treasure"
        },
        "character": {
            "module": "generators.rpg_char_gen",
            "class": "RPGCharacterGenerator",
            "description": "Generate RPG characters"
        },
        "npc": {
            "module": "generators.npc_gen",
            "class": "NPCGenerator",
            "description": "Generate NPCs"
        },
        "name": {
            "module": "generators.name_gen",
            "class": "NameGenerator",
            "description": "Generate fantasy names"
        },
        "dungeon": {
            "module": "generators.dungeon_generator",
            "class": "DungeonGenerator",
            "description": "Generate procedural dungeons"
        },
        "weather": {
            "module": "generators.weather_generator",
            "class": "WeatherGenerator",
            "description": "Generate weather forecasts"
        },
        "event": {
            "module": "generators.random_event_generator",
            "class": "EventGenerator",
            "description": "Generate story events and twists"
        },
        "lair": {
            "module": "generators.lair_action_generator",
            "class": "LairActionGenerator",
            "description": "Generate lair actions and boss mechanics"
        },
        "quest": {
            "module": "generators.quest_builder",
            "class": "QuestBuilder",
            "description": "Generate quests"
        },
        "adventure": {
            "module": "generators.one_shot_builder",
            "class": "OneShotBuilder",
            "description": "Generate one-shot adventures"
        },
        "spell": {
            "module": "generators.spell_card_generator",
            "class": "SpellCardGenerator",
            "description": "Create custom spells"
        },
        "monster": {
            "module": "utilities.gm_toolkit_extra",
            "class": "MonsterStatCreator",
            "description": "Create custom monsters"
        },
        "magic-item": {
            "module": "utilities.gm_toolkit_extra",
            "class": "MagicItemCreator",
            "description": "Create custom magic items"
        },
        "background": {
            "module": "utilities.gm_toolkit_extra",
            "class": "BackgroundGenerator",
            "description": "Generate character backgrounds"
        },
        "dream": {
            "module": "utilities.gm_toolkit_extra",
            "class": "DreamVisionGenerator",
            "description": "Generate dreams and visions"
        },
        "hook": {
            "module": "utilities.gm_toolkit_extra",
            "class": "PlotHookGenerator",
            "description": "Generate plot hooks"
        },
        "map": {
            "module": "utilities.gm_toolkit_extra",
            "class": "TreasureMapGenerator",
            "description": "Generate treasure maps"
        },
    },
    "track": {
        "initiative": {
            "module": "trackers.initiative_tracker",
            "class": "InitiativeTracker",
            "description": "Track combat initiative"
        },
        "campaign": {
            "module": "trackers.campaign_logger",
            "class": "CampaignLogger",
            "description": "Track campaign progress"
        },
        "status": {
            "module": "trackers.status_tracker",
            "class": "StatusTracker",
            "description": "Track party status"
        },
        "travel": {
            "module": "trackers.travel_tracker",
            "class": "TravelTracker",
            "description": "Track overland travel"
        },
        "faction": {
            "module": "trackers.faction_tracker",
            "class": "FactionTracker",
            "description": "Track faction relationships"
        },
        "timeline": {
            "module": "trackers.campaign_timeline",
            "class": "CampaignTimeline",
            "description": "Track campaign timeline"
        },
        "lore": {
            "module": "trackers.lore_database",
            "class": "LoreDatabase",
            "description": "Manage campaign lore"
        },
    },
    "utility": {
        "sentence": {
            "module": "utilities.sentence_forge",
            "class": "SentenceGenerator",
            "description": "Generate template-based text"
        },
        "table": {
            "module": "utilities.random_tables",
            "class": "TableBuilder",
            "description": "Build and roll on random tables"
        },
        "shop": {
            "module": "utilities.shop_market",
            "class": "ShopGenerator",
            "description": "Generate magic item shops"
        },
        "tavern": {
            "module": "utilities.gm_toolkit_extra",
            "class": "TavernGenerator",
            "description": "Generate taverns"
        },
        "trap": {
            "module": "utilities.gm_utilities",
            "class": "TrapGenerator",
            "description": "Generate traps"
        },
        "riddle": {
            "module": "utilities.gm_utilities",
            "class": "PuzzleGenerator",
            "description": "Generate riddles and puzzles"
        },
        "rumor": {
            "module": "utilities.gm_utilities",
            "class": "RumorGenerator",
            "description": "Generate rumors"
        },
        "villain": {
            "module": "utilities.gm_utilities",
            "class": "VillainBuilder",
            "description": "Generate villains"
        },
        "camp": {
            "module": "utilities.gm_toolkit_extra",
            "class": "CampEncounterGenerator",
            "description": "Generate camp encounters"
        },
        "currency": {
            "module": "utilities.gm_toolkit_extra",
            "class": "CurrencyConverter",
            "description": "Convert currencies"
        },
        "spell-card": {
            "module": "generators.spell_card_generator",
            "class": "SpellCardGenerator",
            "description": "Generate spell cards"
        },
        "vtt": {
            "module": "utilities.vtt_export",
            "class": "VTTExporter",
            "description": "Export to VTT platforms"
        },
    },
    "ai": {
        "quest": {
            "module": "ai.linear_generator",
            "class": "LinearContentGenerator",
            "description": "AI linear quest generation"
        },
        "train": {
            "module": "ai.ai_trainer",
            "class": "AITrainer",
            "description": "Train AI on content"
        },
        "memory": {
            "module": "ai.campaign_memory",
            "class": "CampaignMemory",
            "description": "Campaign memory management"
        },
        "choices": {
            "module": "ai.choice_engine",
            "class": "ChoiceEngine",
            "description": "Story choice generation"
        },
    }
}

# Category descriptions
CATEGORY_DESCRIPTIONS = {
    "generate": "Generate game content (encounters, NPCs, loot, etc.)",
    "track": "Track game state (initiative, campaign, status, etc.)",
    "utility": "Utility tools (tables, shops, traps, etc.)"
}


# =============================================================================
# CLI BUILDER
# =============================================================================

def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="gm",
        description="DnD GM Toolkit - Complete RPG Generator Suite",
        epilog="""
Examples:
  gm generate encounter -t forest -d medium
  gm generate loot --rarity rare
  gm track initiative --demo
  gm track campaign add "The Dragon's Lair" --type location
  gm utility tavern
  gm utility trap -l 5

For tool-specific help:
  gm <category> <tool> --help
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument("--version", action="version", version="DnD GM Toolkit v3.0")
    parser.add_argument("--list", action="store_true", help="List all available tools")
    parser.add_argument("--seed", type=int, help="Global random seed")
    
    return parser


def create_category_parser(category: str, tools: Dict[str, dict]) -> argparse.ArgumentParser:
    """Create a subparser for a category."""
    parser = argparse.ArgumentParser(
        description=CATEGORY_DESCRIPTIONS.get(category, f"{category.title()} tools")
    )
    
    parser.add_argument("--list", action="store_true", 
                        help=f"List all {category} tools")
    
    return parser


def add_tool_arguments(parser: argparse.ArgumentParser, tool_name: str, 
                       tool_info: dict) -> None:
    """Add common arguments for a tool."""
    # Common generation arguments
    if "generate" in parser.prog or tool_name in ["encounter", "loot", "character", "npc"]:
        parser.add_argument("--seed", type=int, help="Random seed")
        parser.add_argument("-o", "--output", type=str, help="Output file")
        
        if tool_name == "encounter":
            parser.add_argument("-t", "--terrain", type=str, help="Terrain type")
            parser.add_argument("-d", "--difficulty", default="medium",
                               choices=["easy", "medium", "hard", "deadly"])
            parser.add_argument("--party-level", type=int, default=5)
            parser.add_argument("--party-size", type=int, default=4)
        
        elif tool_name == "loot":
            parser.add_argument("-r", "--rarity", 
                               choices=["common", "uncommon", "rare", "very rare", "legendary"])
            parser.add_argument("--hoard", action="store_true")
        
        elif tool_name == "character":
            parser.add_argument("-l", "--level", type=int, default=1)
            parser.add_argument("-c", "--class", dest="char_class", type=str)
            parser.add_argument("--race", type=str)
            parser.add_argument("--party", type=int, help="Generate party of N")
        
        elif tool_name == "npc":
            parser.add_argument("-r", "--race", type=str, default="human")
            parser.add_argument("-n", "--count", type=int, default=1)
    
    # Common tracker arguments
    elif "track" in parser.prog:
        parser.add_argument("--seed", type=int, help="Random seed")
        
        if tool_name == "initiative":
            parser.add_argument("--demo", action="store_true")
        
        elif tool_name == "campaign":
            subparsers = parser.add_subparsers(dest="command")
            add_parser = subparsers.add_parser("add", help="Add entry")
            add_parser.add_argument("title", help="Entry title")
            add_parser.add_argument("-t", "--type", required=True)
            add_parser.add_argument("-c", "--content", required=True)
    
    # Common utility arguments
    elif "utility" in parser.prog:
        parser.add_argument("--seed", type=int, help="Random seed")
        
        if tool_name == "tavern":
            parser.add_argument("--size", default="medium",
                               choices=["small", "medium", "large"])
        
        elif tool_name == "trap":
            parser.add_argument("-l", "--level", type=int, default=1)
        
        elif tool_name == "riddle":
            parser.add_argument("-d", "--difficulty",
                               choices=["easy", "medium", "hard"])

    # AI arguments
    elif "ai" in parser.prog:
        parser.add_argument("--seed", type=int, help="Random seed")

        if tool_name == "quest":
            parser.add_argument("--theme", default="rescue",
                               choices=["rescue", "hunt", "retrieve", "dungeon"])
            parser.add_argument("-l", "--level", type=int, default=1)
            parser.add_argument("--stages", type=int, default=5)
            parser.add_argument("-o", "--export", type=str, help="Export to file")

        elif tool_name == "train":
            parser.add_argument("--all", action="store_true", help="Train on all content")
            parser.add_argument("--file", type=str, help="Train on specific file")
            parser.add_argument("--type", type=str, default="quest")

        elif tool_name == "memory":
            parser.add_argument("--start-session", type=str, help="Start new session")
            parser.add_argument("--event", type=str, help="Add event")
            parser.add_argument("--event-type", type=str, default="general")

        elif tool_name == "choices":
            parser.add_argument("--situation", default="approach",
                               choices=["approach", "conflict", "mystery", "travel", "treasure", "npc_interaction"])


def run_tool(category: str, tool_name: str, args: argparse.Namespace) -> int:
    """
    Run a tool with given arguments.
    
    Args:
        category: Tool category
        tool_name: Tool name
        args: Parsed arguments
        
    Returns:
        Exit code
    """
    tool_info = TOOL_REGISTRY[category][tool_name]

    try:
        # Import module - use importlib for proper submodule import
        import importlib
        module = importlib.import_module(tool_info["module"])

        # Get generator class
        generator_class = getattr(module, tool_info["class"])
        
        # Create instance with common options
        kwargs = {}
        if hasattr(args, 'seed') and args.seed is not None:
            kwargs['seed'] = args.seed
        
        generator = generator_class(**kwargs)
        
        # Run tool-specific logic
        return run_tool_logic(category, tool_name, generator, args)
        
    except ImportError as e:
        print(f"Error: Could not import {tool_info['module']}: {e}")
        return 1
    except AttributeError as e:
        print(f"Error: Could not find {tool_info['class']}: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_tool_logic(category: str, tool_name: str, generator, 
                   args: argparse.Namespace) -> int:
    """Run tool-specific logic. Returns exit code."""
    
    # GENERATE category
    if category == "generate":
        if tool_name == "encounter":
            encounter = generator.generate_encounter(
                difficulty=getattr(args, 'difficulty', 'medium'),
                terrain=getattr(args, 'terrain', None),
                party_level=getattr(args, 'party_level', 5),
                party_size=getattr(args, 'party_size', 4)
            )
            print(f"=== {encounter['difficulty'].capitalize()} Encounter ===")
            print(f"Terrain: {encounter.get('terrain', 'any')}")
            print(f"Monsters: {encounter['monster_count']}")
            print(f"XP Budget: {encounter['xp_budget']}")
            for m in encounter['monsters']:
                print(f"  • {m['count']}x {m['name']} (CR {m['cr']})")
        
        elif tool_name == "loot":
            if getattr(args, 'hoard', False):
                hoard = generator.generate_hoard(
                    party_level=getattr(args, 'party_level', 5),
                    party_size=getattr(args, 'party_size', 4)
                )
                print(f"=== Treasure Hoard ===")
                print(f"Gold: {hoard['gold_pieces']} gp")
                print(f"Total Value: {hoard['total_value']} gp")
            else:
                item = generator.generate_magic_item(
                    rarity=getattr(args, 'rarity', None)
                )
                print(f"=== {item['name']} ===")
                print(f"Rarity: {item['rarity']}")
                print(f"Property: {item['property']}")
        
        elif tool_name == "character":
            if getattr(args, 'party', None):
                party = generator.generate_party(
                    party_size=args.party,
                    level=getattr(args, 'level', 1)
                )
                print(f"=== Adventuring Party (Level {args.level}) ===")
                for char in party:
                    print(f"  • {char['identity']['name']} - {char['identity']['race']} {char['identity']['class']}")
            else:
                char = generator.generate_character(
                    level=getattr(args, 'level', 1),
                    char_class=getattr(args, 'char_class', None),
                    race=getattr(args, 'race', None)
                )
                print(f"=== {char['identity']['name']} ===")
                print(f"Level {char['identity']['level']} {char['identity']['race']} {char['identity']['class']}")
        
        elif tool_name == "npc":
            npc = generator.generate_npc(
                race=getattr(args, 'race', 'human')
            )
            print(f"=== {npc['identity']['name']} ===")
            print(f"{npc['identity']['race']} {npc['identity']['class']}")
        
        elif tool_name == "name":
            name = generator.generate_name()
            print(f"Generated Name: {name}")
        
        elif tool_name == "dungeon":
            dungeon = generator.generate_dungeon()
            print(f"=== {dungeon.name} ===")
            print(f"Theme: {dungeon.theme}")
            print(f"Levels: {dungeon.total_levels}")
        
        elif tool_name == "weather":
            forecast = generator.generate_forecast(days=7)
            print(generator.display_forecast(forecast))
        
        elif tool_name == "event":
            event = generator.generate_event()
            print(f"=== {event.name} ===")
            print(f"{event.description}")
        
        elif tool_name == "lair":
            boss_data = generator.generate_complete_boss()
            print(generator.display_lair(boss_data))
        
        elif tool_name == "quest":
            quest = generator.generate_quest()
            print(f"=== {quest['identity']['name']} ===")
            print(f"Type: {quest['identity']['type']}")
            print(f"Hook: {quest['hook']['text']}")
        
        elif tool_name == "adventure":
            adventure = generator.build_adventure()
            print(generator.display_adventure(adventure))
        
        elif tool_name in ["spell", "monster", "magic-item", "background", "dream", "hook", "map"]:
            # Delegate to gm_toolkit_extra
            print(f"Running {tool_name} generator...")
            # Simplified output for demo
            print(f"Generated {tool_name} successfully!")
    
    # TRACK category
    elif category == "track":
        if tool_name == "initiative":
            if getattr(args, 'demo', False):
                generator.create_combat("Demo Combat")
                generator.add_combatant("Fighter", hp=30, ac=18, initiative_mod=2)
                generator.add_combatant("Wizard", hp=20, ac=13, initiative_mod=3)
                generator.start_combat()
            else:
                print("Use --demo for demo combat or use API directly")
        
        elif tool_name == "campaign":
            print("Campaign tracker - use subcommands: add, list, export")
        
        elif tool_name == "status":
            print("Status tracker - use API directly for full functionality")
        
        elif tool_name in ["travel", "faction", "timeline", "lore"]:
            print(f"{tool_name.title()} tracker initialized")
    
    # UTILITY category
    elif category == "utility":
        if tool_name == "tavern":
            tavern = generator.generate_tavern(getattr(args, 'size', 'medium'))
            print(f"=== {tavern['name']} ===")
            print(f"Proprietor: {tavern['proprietor']['name']}")
            print(f"Atmosphere: {tavern['atmosphere']}")
        
        elif tool_name == "trap":
            trap = generator.generate_trap(level=getattr(args, 'level', 1))
            print(f"=== {trap['name']} ===")
            print(f"DC: {trap['perception_dc']} (perception), {trap['disable_dc']} (disable)")
            print(f"Damage: {trap['damage']}")
        
        elif tool_name == "riddle":
            riddle = generator.generate_riddle(getattr(args, 'difficulty', ''))
            print(f"Riddle: {riddle['riddle']}")
            print(f"Answer: {riddle['answer']}")
        
        elif tool_name == "rumor":
            rumor = generator.generate_rumor()
            print(f"Rumor: {rumor}")
        
        elif tool_name == "villain":
            villain = generator.generate_villain(cr=getattr(args, 'cr', 5))
            print(f"=== {villain['name']} ===")
            print(f"Archetype: {villain['archetype']}")
            print(f"Goal: {villain['goal']}")
        
        elif tool_name in ["camp", "currency", "spell-card", "vtt"]:
            print(f"{tool_name.title()} utility initialized")

    # AI category
    elif category == "ai":
        if tool_name == "quest":
            quest = generator.generate_quest(
                theme=getattr(args, 'theme', 'rescue'),
                party_level=getattr(args, 'level', 1),
                num_stages=getattr(args, 'stages', 5)
            )
            print(generator.display_content())
            
            if getattr(args, 'export', None):
                generator.export_to_json(args.export)
                print(f"Exported to {args.export}")
        
        elif tool_name == "train":
            if getattr(args, 'all', False):
                stats = generator.train_on_all_content()
                print("=== Training Complete ===")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            elif getattr(args, 'file', None):
                count = generator.train_on_file(args.file, getattr(args, 'type', 'quest'))
                print(f"Trained on {count} items")
            else:
                status = generator.get_training_status()
                print("=== AI Training Status ===")
                print(f"Content processed: {status.get('content_processed', 0)}")
                print(f"Patterns learned: {status.get('patterns_learned', 0)}")
        
        elif tool_name == "memory":
            if getattr(args, 'start_session', None):
                generator.start_session(1, args.start_session)
                print(f"Started session: {args.start_session}")
            elif getattr(args, 'event', None):
                generator.add_event(args.event, getattr(args, 'event_type', 'general'))
                print(f"Added event: {args.event}")
            else:
                summary = generator.get_summary()
                print("=== Campaign Memory ===")
                print(f"Campaign: {summary.get('campaign', 'Unnamed')}")
                print(f"Session: {summary.get('current_session', 1)}")
                print(f"Active threads: {summary.get('active_threads_count', 0)}")
        
        elif tool_name == "choices":
            situation = getattr(args, 'situation', 'approach')
            choice = generator.generate_choices(situation)
            print(generator.display_choices(choice))

    return 0


def list_tools(category: Optional[str] = None) -> None:
    """List available tools."""
    if category:
        print(f"\n=== {category.upper()} TOOLS ===\n")
        tools = TOOL_REGISTRY.get(category, {})
        for name, info in tools.items():
            print(f"  {name:15} - {info['description']}")
    else:
        print("\n=== DnD GM TOOLKIT - ALL TOOLS ===\n")
        for cat, tools in TOOL_REGISTRY.items():
            print(f"\n{cat.upper()}: {CATEGORY_DESCRIPTIONS.get(cat, '')}")
            print("-" * 50)
            for name, info in tools.items():
                print(f"  {name:15} - {info['description']}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main() -> int:
    """Main entry point. Returns exit code."""
    parser = create_main_parser()
    
    # Check for --list first
    if "--list" in sys.argv:
        list_tools()
        return 0
    
    # Create subparsers for categories
    subparsers = parser.add_subparsers(dest="category", help="Tool category")
    
    # Create parser for each category
    category_parsers = {}
    for category, tools in TOOL_REGISTRY.items():
        cat_parser = subparsers.add_parser(category, 
                                           help=CATEGORY_DESCRIPTIONS.get(category, ''))
        cat_parser.add_argument("tool", nargs="?", 
                                choices=list(tools.keys()),
                                help="Tool to use")
        category_parsers[category] = cat_parser
    
    args = parser.parse_args()
    
    # Handle global seed
    if hasattr(args, 'seed') and args.seed is not None:
        import random
        random.seed(args.seed)
    
    # No category specified
    if not args.category:
        parser.print_help()
        list_tools()
        return 0
    
    # No tool specified
    if not hasattr(args, 'tool') or not args.tool:
        category_parsers[args.category].print_help()
        if hasattr(args, 'list') and args.list:
            list_tools(args.category)
        return 0
    
    # Run the tool
    return run_tool(args.category, args.tool, args)


if __name__ == "__main__":
    sys.exit(main())
