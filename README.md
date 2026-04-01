# DnD GM Toolkit v3.0 - Complete RPG Generator Suite

A comprehensive collection of DnD/RPG content generators built with Python. Generate sentences, names, NPCs, encounters, loot, characters, quests, and export to VTT platforms.

**Now with DRY architecture** - Shared core utilities, unified CLI, and reusable components!

## Features

### Core Framework (NEW in v3.0)
- **gm_core.py**: Shared utilities, base classes, cached data loading
- **gm_data.py**: Centralized D&D 5e data structures and reference tables
- **gm_cli.py**: Unified command-line interface for all tools

### Core Generators
- **Sentence Forge**: Template-based text generation with conditionals and grammar transforms
- **Name Generator**: Fantasy names with 16+ cultural variants
- **NPC Generator**: Complete NPCs with appearance, personality, and secrets
- **Encounter Generator**: CR-balanced encounters with terrain filtering
- **Loot Generator**: Rarity-weighted magic items and treasure hoards
- **RPG Character Generator**: Full DnD 5e characters with stats and equipment
- **VTT Export**: Foundry VTT and Roll20 compatible JSON output

### New in v2.0+
- **Quest Builder**: Complete quest generation with hooks, complications, and rewards
- **Initiative Tracker**: Combat tracking with HP, conditions, and death saves
- **Spell Card Generator**: Generate spell cards and class spell lists
- **Campaign Logger**: Track sessions, XP, loot, and story arcs
- **Status Tracker**: Visual party dashboard with HP bars, conditions, and resources
- **Regional Treasure**: Location-specific loot tables (arctic, desert, forest, etc.)
- **Prefab Encounters**: 15+ pre-built encounters with tactics and maps

## Installation

No dependencies required beyond Python 3.10+. Uses only standard library.

```bash
cd /path/to/gm
```

## Quick Start

### Unified CLI (NEW!)

Use the single entry point for all tools:

```bash
# List all tools
python gm_cli.py --list

# Generate content
python gm_cli.py generate encounter -t forest -d medium
python gm_cli.py generate loot --rarity rare
python gm_cli.py generate character -l 5 -c Wizard

# Track game state
python gm_cli.py track initiative --demo
python gm_cli.py track campaign add "The Dragon's Lair" --type location

# Utilities
python gm_cli.py utility tavern
python gm_cli.py utility trap -l 5
python gm_cli.py utility villain
```

### Legacy Individual Scripts

All individual scripts still work:

### Sentence Forge

```bash
# Basic usage
python sentence_forge.py -t "{USER} is {STATUS}" -v USER=Alice -v STATUS=happy

# With conditionals
python sentence_forge.py -t "{if:CLASS:mage:The wizard|The warrior} enters" -v CLASS=mage

# Grammar transforms
python sentence_forge.py -t "The {CREATURE|plural} {ACTION|verb_ing}" -v CREATURE=wolf -v ACTION=approach
```

### Name Generator

```bash
# Generate elvish names
python name_gen.py -c elvish -n 5

# Generate party names
python name_gen.py --party

# With titles
python name_gen.py -c dwarvish --title --class warrior
```

### NPC Generator

```bash
# Generate an elf NPC
python npc_gen.py -r elf

# Generate multiple NPCs in table format
python npc_gen.py -n 5 --list

# Generate party contacts
python npc_gen.py --contacts --party-level 5
```

### Encounter Generator

```bash
# Forest encounter
python encounter_gen.py -t forest -d medium

# For specific party
python encounter_gen.py -t dungeon --party-level 3 --party-size 5

# Random encounter
python encounter_gen.py --random
```

### Loot Generator

```bash
# Single magic item
python loot_gen.py -r rare

# Treasure hoard
python loot_gen.py --hoard --party-level 7 --party-size 5

# Roll on treasure table
python loot_gen.py --roll major
```

### RPG Character Generator

```bash
# Single character
python rpg_char_gen.py -l 5 -c Wizard -r Human

# Full party
python rpg_char_gen.py --party 4 -l 3 -o party.json

# List options
python rpg_char_gen.py --list-classes
python rpg_char_gen.py --list-races
```

### VTT Export

```bash
# Export encounter to Foundry
python vtt_export.py --encounter -t forest -o encounter.json

# Export NPC
python vtt_export.py --npc -r dwarf -o npc.json

# For Roll20
python vtt_export.py --platform roll20 --encounter -o roll20_enc.json
```

### Quest Builder (NEW)

```bash
# Generate a rescue quest
python quest_builder.py -t rescue -c moderate -l 5

# Generate quest chain
python quest_builder.py --chain 3 --starting simple -l 3

# Export to JSON
python quest_builder.py -t retrieve -o quest.json
```

### Initiative Tracker (NEW)

```bash
# Run demo combat
python initiative_tracker.py --demo

# Create named combat and export
python initiative_tracker.py --combat "Goblin Ambush" -o combat.json

# Export to Foundry VTT
python initiative_tracker.py --export-foundry foundry.json
```

### Spell Card Generator (NEW)

```bash
# List wizard spells
python spell_card_generator.py --class wizard --level 3

# Generate spell card
python spell_card_generator.py --spell Fireball --format markdown

# Export spell list
python spell_card_generator.py --list wizard -o wizard_spells.md

# Quick reference
python spell_card_generator.py --quick-ref wizard --levels 1 2 3
```

### Campaign Logger (NEW)

```bash
# Create new campaign
python campaign_logger.py new "Rise of Tiamat" --dm "John"

# Log session
python campaign_logger.py session "The Goblin Cave" --summary "Party explores..." --xp "Thorin:300"

# Add character
python campaign_logger.py add-char "Thorin" --player "Alice" --class Fighter

# Export campaign
python campaign_logger.py export campaign.md --format markdown
```

### Status Tracker (NEW)

```bash
# Run demo with sample party
python status_tracker.py --demo

# Create named party
python status_tracker.py --party "The Dragon Slayers"

# Quick view
python status_tracker.py --quick-view

# Export to JSON
python status_tracker.py --export party_status.json

# Export to Markdown
python status_tracker.py --export-md party_status.md
```

## Syntax Reference

### Sentence Forge

| Syntax | Description | Example |
|--------|-------------|---------|
| `{PLACEHOLDER}` | Variable | `{USER}` |
| `{word1\|word2}` | Inline alternatives | `{killed\|eliminated}` |
| `{word:3\|other:1}` | Weighted alternatives | `{common:10\|rare:1}` |
| `{USER\|upper}` | Uppercase transform | `ALICE` |
| `{ITEM\|plural}` | Pluralization | `cats`, `children` |
| `{ANIMAL\|a}` | Add article | `a cat`, `an elephant` |
| `{VERB\|verb_s}` | 3rd person singular | `fights`, `goes` |
| `{VERB\|verb_ing}` | Present participle | `fighting`, `running` |
| `{VERB\|verb_ed}` | Past tense | `fought`, `ran` |
| `{NAME\|possessive}` | Possessive form | `Arthur's`, `James'` |
| `{if:VAR:value:then\|else}` | Conditional | `{if:CLASS:mage:wizard\|warrior}` |

### Available Transforms

- **Case**: `upper`, `lower`, `title`, `capitalize`
- **Grammar**: `plural`, `verb_s`, `verb_ing`, `verb_ed`, `possessive`
- **Articles**: `a`, `an`
- **String**: `truncate:N`, `default:VALUE`, `reverse`, `first`, `last`

## Data Files

The `data/` directory contains JSON files for templates and SRD data:

| File | Contents |
|------|----------|
| `quest_hooks.json` | 8 quest template variations |
| `npc_descriptions.json` | NPC description templates |
| `combat_descriptions.json` | Combat narration templates |
| `loot_descriptions.json` | Treasure description templates |
| `srd_monsters.json` | 32 SRD monsters with CR/terrain |
| `srd_spells.json` | 40 SRD spells by class/school |
| `srd_items.json` | 45 magic items by rarity |

## API Usage

### Sentence Generator

```python
from sentence_forge import SentenceGenerator

# Basic
gen = SentenceGenerator("{USER} {killed|eliminated} {TARGET}")
gen.set_values("USER", ["Alice"])
gen.set_values("TARGET", ["Bob"])
print(gen.generate())  # "Alice killed Bob"

# Conditionals
gen = SentenceGenerator("{if:ALIGNMENT:good:holy|unholy} symbol")
gen.set_values("ALIGNMENT", ["good"])
print(gen.generate())  # "holy symbol"

# Grammar
gen = SentenceGenerator("The {CREATURE|plural} {ACTION|verb_ing}")
gen.set_values("CREATURE", ["mouse"])
gen.set_values("ACTION", ["approach"])
print(gen.generate())  # "The mice approaching"
```

### Name Generator

```python
from name_gen import NameGenerator

ng = NameGenerator(culture="elvish")
print(ng.generate_name())  # "Aelvrthien"
print(ng.generate_full_name(include_title=True))  # "Elwen Aranwyn the Wise"
print(ng.generate_party_names(4))  # Party of 4 adventurers
```

### Encounter Generator

```python
from encounter_gen import EncounterGenerator

eg = EncounterGenerator()
enc = eg.generate_encounter(
    difficulty="medium",
    terrain="forest",
    party_size=4,
    party_level=5
)
print(enc["monsters"])  # List of monsters
print(enc["xp_budget"])  # XP budget
```

### Loot Generator

```python
from loot_gen import LootGenerator

lg = LootGenerator()
item = lg.generate_magic_item(rarity="rare")
print(item["name"])  # "Ring of Protection"
print(item["property"])  # "+1 to AC and saving throws"

hoard = lg.generate_hoard(party_size=4, party_level=5)
print(hoard["total_value"])  # Total GP value
```

### NPC Generator

```python
from npc_gen import NPCGenerator

npcg = NPCGenerator()
npc = npcg.generate_npc(race="dwarf")
print(npc["name"])  # "Thorin Ironforge the Bold"
print(npc["personality"]["trait"])  # "brave to a fault"
print(npc["secret"]["secret"])  # "owes money to dangerous people"
```

### Character Generator

```python
from rpg_char_gen import RPGCharacterGenerator

cg = RPGCharacterGenerator()
char = cg.generate_character(level=5, char_class="Wizard", race="Elf")
print(char["identity"]["name"])  # "Aerion"
print(char["abilities"]["scores"])  # {"STR": 8, "DEX": 14, ...}
print(char["combat"]["hp"]["maximum"])  # 27
```

### VTT Export

```python
from vtt_export import VTTExporter
from encounter_gen import EncounterGenerator

eg = EncounterGenerator()
enc = eg.generate_encounter(difficulty="medium", terrain="forest")

exporter = VTTExporter(platform="foundry")
export_data = exporter.export_encounter(enc, "Forest Encounter")
exporter.export_to_file(export_data, "encounter.json")
```

## Project Structure

### v3.0 DRY Architecture

```
gm/
├── gm_core.py              # Core utilities & base classes (SHARED)
├── gm_data.py              # Shared data structures & tables (SHARED)
├── gm_cli.py               # Unified CLI framework (SHARED)
│
├── generators/             # All generators (use BaseGenerator)
│   ├── encounter_gen.py
│   ├── loot_gen.py
│   ├── rpg_char_gen.py
│   ├── npc_gen.py
│   ├── name_gen.py
│   ├── dungeon_generator.py
│   ├── weather_generator.py
│   ├── random_event_generator.py
│   ├── lair_action_generator.py
│   ├── quest_builder.py
│   └── one_shot_builder.py
│
├── trackers/               # All trackers (use BaseTracker)
│   ├── initiative_tracker.py
│   ├── campaign_logger.py
│   ├── status_tracker.py
│   ├── travel_tracker.py
│   ├── faction_tracker.py
│   ├── campaign_timeline.py
│   └── lore_database.py
│
├── utilities/              # Utility tools
│   ├── sentence_forge.py
│   ├── vtt_export.py
│   ├── spell_card_generator.py
│   ├── random_tables.py
│   ├── shop_market.py
│   ├── gm_utilities.py     # Traps, puzzles, rumors, villains
│   └── gm_toolkit_extra.py # Tavern, background, items, etc.
│
└── data/                   # JSON data files
    ├── srd_monsters.json
    ├── srd_items.json
    ├── srd_spells.json
    ├── prefab_encounters.json
    ├── regional_treasure.json
    └── ...
```

### Legacy Flat Structure

All modules also work in the root directory for backward compatibility.

## Testing

Run tests with pytest:

```bash
python -m pytest test_gm.py -v
```

## License

MIT License
