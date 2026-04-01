#!/usr/bin/env python3
"""
DnD Tools - Unified CLI

A single command-line interface for all DnD generator tools.
"""

import argparse
import json
import sys
from pathlib import Path

# Import all generators
try:
    from utilities.sentence_forge import SentenceGenerator
    from generators.name_gen import NameGenerator
    from generators.npc_gen import NPCGenerator
    from generators.encounter_gen import EncounterGenerator
    from generators.loot_gen import LootGenerator
    from generators.rpg_char_gen import RPGCharacterGenerator
    from utilities.vtt_export import VTTExporter
    from generators.quest_builder import QuestBuilder
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def cmd_sentence(args):
    """Handle sentence_forge commands."""
    gen = SentenceGenerator(args.template if args.template else ["{USER} is here"])
    
    if args.values:
        for item in args.values:
            if '=' in item:
                key, value = item.split('=', 1)
                values = [v.strip() for v in value.split(',') if v.strip()]
                gen.set_values(key.upper(), values)
    
    if args.defaults:
        defaults = {}
        for item in args.defaults:
            if '=' in item:
                key, value = item.split('=', 1)
                defaults[key.upper()] = value.strip()
        gen.default_values = defaults
    
    if args.all:
        results = gen.generate_all()
        for r in results:
            print(r)
    else:
        results = gen.generate_multiple(args.count, seed=args.seed)
        for r in results:
            print(r)


def cmd_name(args):
    """Handle name_gen commands."""
    ng = NameGenerator(culture=args.culture, seed=args.seed)
    
    if args.list_cultures:
        print("Available cultures:", ", ".join(ng.list_cultures()))
        return
    
    if args.party:
        party = ng.generate_party_names(args.count)
        for role, name in party.items():
            print(f"{role}: {name}")
    elif args.meaning:
        for _ in range(args.count):
            name, meaning = ng.generate_name_with_meaning()
            print(f"{name}: {meaning}")
    elif args.dynasty:
        base = ng.generate_name()
        dynasty = ng.generate_dynasty_name(base)
        print(f"{base} of {dynasty}")
    else:
        names = ng.generate_multiple(args.count, include_title=args.title)
        for name in names:
            print(name)


def cmd_npc(args):
    """Handle npc_gen commands."""
    ng = NPCGenerator(seed=args.seed)
    
    if args.list_races:
        print("Available races:", ", ".join(ng.RACES.keys()))
        return
    
    if args.list_classes:
        print("Available classes:", ", ".join(ng.CLASSES.keys()))
        return
    
    if args.contacts:
        contacts = ng.generate_party_contacts(party_level=args.level)
        for role, npc in contacts.items():
            print(f"{role}: {npc['identity']['name']} ({npc['identity']['race']} {npc['identity']['class']})")
    else:
        npc = ng.generate_npc(
            race=args.race or "human",
            class_name=args.char_class or "commoner",
            level=args.level,
            include_stat_block=not args.no_stats,
            include_inventory=not args.no_inventory,
            seed=args.seed
        )
        
        if args.json:
            print(json.dumps(npc, indent=2, default=str))
        else:
            print(f"{npc['identity']['name']} - {npc['identity']['race']} {npc['identity']['class']} {npc['identity']['level']}")
            if npc.get('stat_block'):
                sb = npc['stat_block']
                print(f"  HP: {sb['hit_points']}, AC: {sb['armor_class']}")


def cmd_encounter(args):
    """Handle encounter_gen commands."""
    eg = EncounterGenerator()
    
    if args.list_terrains:
        print("Available terrains:", ", ".join(eg.list_terrains()))
        return
    
    if args.list_types:
        print("Available types:", ", ".join(eg.list_monster_types()))
        return
    
    if args.monster:
        monster = eg.get_monster_by_name(args.monster)
        if monster:
            print(f"{monster['name']}: CR {monster['cr']}, AC {monster['ac']}, HP {monster['hp']}")
        else:
            print(f"Monster '{args.monster}' not found")
        return
    
    if args.boss:
        enc = eg.generate_boss_encounter(
            boss_cr=args.boss_cr,
            party_level=args.level,
            party_size=args.size,
            terrain=args.terrain
        )
    else:
        enc = eg.generate_encounter(
            difficulty=args.difficulty,
            terrain=args.terrain,
            party_level=args.level,
            party_size=args.size,
            include_lair_actions=args.lair,
            include_hazards=args.hazards
        )
    
    if args.json:
        print(json.dumps(enc, indent=2))
    else:
        print(f"{enc['difficulty'].capitalize()} Encounter (XP: {enc['xp_budget']})")
        for m in enc['monsters']:
            print(f"  {m['name']} (CR {m['cr']}, HP {m['hp']})")


def cmd_loot(args):
    """Handle loot_gen commands."""
    lg = LootGenerator()
    
    if args.hoard:
        hoard = lg.generate_hoard(
            party_level=args.level,
            party_size=args.size,
            include_magic_items=args.count,
            allow_cursed=args.cursed,
            allow_sentient=args.sentient
        )
        if args.json:
            print(json.dumps(hoard, indent=2))
        else:
            print(f"Treasure Hoard: {hoard['gold_pieces']} gp, {len(hoard['magic_items'])} items")
            for item in hoard['magic_items']:
                curse = " ⚠️ CURSED" if item.get('cursed') else ""
                sentient = " 🧠" if item.get('sentient') else ""
                print(f"  {item['name']} ({item['rarity']}){curse}{sentient}")
    else:
        item = lg.generate_magic_item(
            rarity=args.rarity,
            item_type=args.type,
            allow_cursed=args.cursed,
            allow_sentient=args.sentient,
            seed=args.seed
        )
        if args.json:
            print(json.dumps(item, indent=2))
        else:
            curse = " ⚠️ CURSED" if item.get('cursed') else ""
            sentient = " 🧠" if item.get('sentient') else ""
            print(f"{item['name']} ({item['rarity']}){curse}{sentient}")
            print(f"  {item['property']}")


def cmd_char(args):
    """Handle rpg_char_gen commands."""
    cg = RPGCharacterGenerator(seed=args.seed)
    
    if args.list_classes:
        print("Available classes:", ", ".join(cg.CLASSES.keys()))
        return
    
    if args.party:
        party = cg.generate_party(party_size=args.count, level=args.level)
        for char in party:
            c = char['identity']
            print(f"{c['name']}: {c['race']} {c['class']} {c['level']} (HP: {char['combat']['hp']['maximum']})")
    else:
        char = cg.generate_character(
            level=args.level,
            char_class=args.char_class,
            race=args.race,
            seed=args.seed
        )
        if args.json:
            print(json.dumps(char, indent=2))
        else:
            c = char['identity']
            print(f"{c['name']} - {c['race']} {c['class']} {c['level']}")
            print(f"  HP: {char['combat']['hp']['maximum']}, AC: {char['combat']['ac']}")


def cmd_quest(args):
    """Handle quest_builder commands."""
    qb = QuestBuilder(seed=args.seed)
    
    if args.campaign:
        campaign = qb.build_campaign(
            num_quests=args.num_quests,
            starting_level=args.level,
            seed=args.seed
        )
        if args.json:
            print(json.dumps(campaign, indent=2, default=str))
        else:
            print(f"Campaign: {campaign['title']}")
            print(f"  Levels {campaign['starting_level']}-{campaign['ending_level']}")
            for q in campaign['quests']:
                print(f"  {q['chapter']}. {q['title']} (Level {q['recommended_level']})")
    else:
        quest = qb.build_quest(
            quest_type=args.type,
            party_level=args.level,
            party_size=args.size,
            include_complications=args.complications,
            seed=args.seed
        )
        if args.json:
            print(json.dumps(quest, indent=2, default=str))
        else:
            print(f"Quest: {quest['title']}")
            print(f"  Type: {quest['type_name']} (Level {quest['recommended_level']})")
            print(f"  Hook: {quest['hook']}")
            print(f"  Stages: {len(quest['stages'])}")


def cmd_vtt(args):
    """Handle vtt_export commands."""
    exporter = VTTExporter(platform=args.platform)
    
    if args.encounter:
        eg = EncounterGenerator()
        enc = eg.generate_encounter(
            difficulty=args.difficulty or "medium",
            terrain=args.terrain
        )
        export_data = exporter.export_encounter(enc, "Exported Encounter")
    elif args.npc:
        ng = NPCGenerator()
        npc = ng.generate_npc(race=args.race or "human", level=args.level or 5)
        export_data = exporter.export_npc(npc)
    elif args.loot:
        lg = LootGenerator()
        loot = lg.generate_hoard() if args.hoard else lg.generate_magic_item()
        export_data = exporter.export_loot(loot)
    else:
        print("Specify --encounter, --npc, or --loot")
        return
    
    if args.output:
        exporter.export_to_file(export_data, args.output)
        print(f"Exported to {args.output}")
    else:
        print(json.dumps(export_data, indent=2))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="dnd-tools",
        description="DnD Tools - Unified Generator Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dnd-tools sentence -t "{USER} {killed|eliminated} {TARGET}" -v USER=Alice -v TARGET=Bob
  dnd-tools name -c elvish -n 5
  dnd-tools npc -r elf -c wizard -l 10
  dnd-tools encounter -t forest -d hard --lair
  dnd-tools loot --hoard -l 10 --cursed --sentient
  dnd-tools char --party -l 5 -n 4
  dnd-tools quest -t rescue -l 5 --complications
  dnd-tools vtt --encounter -o encounter.json
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sentence command
    sent_parser = subparsers.add_parser("sentence", help="Generate sentences from templates")
    sent_parser.add_argument("-t", "--template", action="append", help="Template string")
    sent_parser.add_argument("-v", "--values", action="append", help="PLACEHOLDER=value")
    sent_parser.add_argument("-d", "--defaults", action="append", help="PLACEHOLDER=default")
    sent_parser.add_argument("-c", "--count", type=int, default=1, help="Number to generate")
    sent_parser.add_argument("--all", action="store_true", help="Generate all combinations")
    sent_parser.add_argument("--seed", type=int, help="Random seed")
    sent_parser.set_defaults(func=cmd_sentence)
    
    # Name command
    name_parser = subparsers.add_parser("name", help="Generate fantasy names")
    name_parser.add_argument("-c", "--culture", default="human", help="Cultural style")
    name_parser.add_argument("-n", "--count", type=int, default=1, help="Number to generate")
    name_parser.add_argument("--title", action="store_true", help="Include titles")
    name_parser.add_argument("--meaning", action="store_true", help="Show name meanings")
    name_parser.add_argument("--dynasty", action="store_true", help="Generate dynasty name")
    name_parser.add_argument("--party", action="store_true", help="Generate party names")
    name_parser.add_argument("--list-cultures", action="store_true", help="List cultures")
    name_parser.add_argument("--seed", type=int, help="Random seed")
    name_parser.set_defaults(func=cmd_name)
    
    # NPC command
    npc_parser = subparsers.add_parser("npc", help="Generate NPCs")
    npc_parser.add_argument("-r", "--race", help="Character race")
    npc_parser.add_argument("-c", "--char-class", help="Character class")
    npc_parser.add_argument("-l", "--level", type=int, default=1, help="Character level")
    npc_parser.add_argument("--contacts", action="store_true", help="Generate party contacts")
    npc_parser.add_argument("--list-races", action="store_true", help="List races")
    npc_parser.add_argument("--list-classes", action="store_true", help="List classes")
    npc_parser.add_argument("--no-stats", action="store_true", help="Exclude stat block")
    npc_parser.add_argument("--no-inventory", action="store_true", help="Exclude inventory")
    npc_parser.add_argument("--json", action="store_true", help="JSON output")
    npc_parser.add_argument("--seed", type=int, help="Random seed")
    npc_parser.set_defaults(func=cmd_npc)
    
    # Encounter command
    enc_parser = subparsers.add_parser("encounter", help="Generate encounters")
    enc_parser.add_argument("-t", "--terrain", help="Terrain type")
    enc_parser.add_argument("-d", "--difficulty", default="medium", help="Difficulty")
    enc_parser.add_argument("-l", "--level", type=int, default=5, help="Party level")
    enc_parser.add_argument("-s", "--size", type=int, default=4, help="Party size")
    enc_parser.add_argument("--boss", action="store_true", help="Boss encounter")
    enc_parser.add_argument("--boss-cr", type=int, default=15, help="Boss CR")
    enc_parser.add_argument("--lair", action="store_true", help="Include lair actions")
    enc_parser.add_argument("--hazards", action="store_true", help="Include hazards")
    enc_parser.add_argument("--list-terrains", action="store_true", help="List terrains")
    enc_parser.add_argument("--list-types", action="store_true", help="List monster types")
    enc_parser.add_argument("--monster", help="Get monster info")
    enc_parser.add_argument("--json", action="store_true", help="JSON output")
    enc_parser.set_defaults(func=cmd_encounter)
    
    # Loot command
    loot_parser = subparsers.add_parser("loot", help="Generate loot")
    loot_parser.add_argument("-r", "--rarity", help="Item rarity")
    loot_parser.add_argument("-t", "--type", help="Item type")
    loot_parser.add_argument("-n", "--count", type=int, default=1, help="Number of items")
    loot_parser.add_argument("--hoard", action="store_true", help="Generate hoard")
    loot_parser.add_argument("-l", "--level", type=int, default=5, help="Party level")
    loot_parser.add_argument("-s", "--size", type=int, default=4, help="Party size")
    loot_parser.add_argument("--cursed", action="store_true", help="Allow cursed items")
    loot_parser.add_argument("--sentient", action="store_true", help="Allow sentient items")
    loot_parser.add_argument("--json", action="store_true", help="JSON output")
    loot_parser.set_defaults(func=cmd_loot)
    
    # Character command
    char_parser = subparsers.add_parser("char", help="Generate characters")
    char_parser.add_argument("-r", "--race", help="Character race")
    char_parser.add_argument("-c", "--char-class", help="Character class")
    char_parser.add_argument("-l", "--level", type=int, default=1, help="Character level")
    char_parser.add_argument("-n", "--count", type=int, default=1, help="Number to generate")
    char_parser.add_argument("--party", action="store_true", help="Generate party")
    char_parser.add_argument("--list-classes", action="store_true", help="List classes")
    char_parser.add_argument("--json", action="store_true", help="JSON output")
    char_parser.add_argument("--seed", type=int, help="Random seed")
    char_parser.set_defaults(func=cmd_char)
    
    # Quest command
    quest_parser = subparsers.add_parser("quest", help="Generate quests")
    quest_parser.add_argument("-t", "--type", default="rescue", help="Quest type")
    quest_parser.add_argument("-l", "--level", type=int, default=5, help="Party level")
    quest_parser.add_argument("-s", "--size", type=int, default=4, help="Party size")
    quest_parser.add_argument("--complications", action="store_true", help="Add complications")
    quest_parser.add_argument("--campaign", action="store_true", help="Generate campaign")
    quest_parser.add_argument("--num-quests", type=int, default=5, help="Quests in campaign")
    quest_parser.add_argument("--json", action="store_true", help="JSON output")
    quest_parser.add_argument("--seed", type=int, help="Random seed")
    quest_parser.set_defaults(func=cmd_quest)
    
    # VTT command
    vtt_parser = subparsers.add_parser("vtt", help="Export to VTT formats")
    vtt_parser.add_argument("--platform", default="foundry", choices=["foundry", "roll20", "generic"])
    vtt_parser.add_argument("--encounter", action="store_true", help="Export encounter")
    vtt_parser.add_argument("--npc", action="store_true", help="Export NPC")
    vtt_parser.add_argument("--loot", action="store_true", help="Export loot")
    vtt_parser.add_argument("--hoard", action="store_true", help="Export hoard")
    vtt_parser.add_argument("-t", "--terrain", help="Terrain for encounter")
    vtt_parser.add_argument("-d", "--difficulty", help="Difficulty for encounter")
    vtt_parser.add_argument("-r", "--race", help="Race for NPC")
    vtt_parser.add_argument("-l", "--level", type=int, help="Level")
    vtt_parser.add_argument("-o", "--output", help="Output file")
    vtt_parser.set_defaults(func=cmd_vtt)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
