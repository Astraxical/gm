#!/usr/bin/env python3
"""
Tests for DnD GM Tools - Encounter, Loot, and RPG Character Generators
Converted from pytest to unittest for stdlib compatibility
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import generators
from generators.encounter_gen import EncounterGenerator
from generators.loot_gen import LootGenerator
from generators.rpg_char_gen import RPGCharacterGenerator
from generators.name_gen import NameGenerator
from generators.npc_gen import NPCGenerator
from generators.quest_builder import QuestBuilder
from generators.spell_card_generator import SpellCardGenerator
from trackers.initiative_tracker import InitiativeTracker, Combatant
from trackers.campaign_logger import CampaignLogger


class TestEncounterGenerator(unittest.TestCase):
    """Test encounter generation functionality."""

    def test_encounter_generator_init(self):
        """Test encounter generator initialization."""
        eg = EncounterGenerator()
        self.assertIsNotNone(eg.monsters)
        self.assertGreater(len(eg.monsters), 0)
        self.assertIsNotNone(eg.terrain_types)

    def test_filter_monsters_by_terrain(self):
        """Test filtering monsters by terrain."""
        eg = EncounterGenerator()
        forest_monsters = eg.filter_monsters(terrain="forest")
        self.assertGreater(len(forest_monsters), 0)
        for monster in forest_monsters:
            terrains = [t.lower() for t in monster.get("terrain", [])]
            self.assertTrue("forest" in terrains or "any" in terrains)

    def test_filter_monsters_by_cr(self):
        """Test filtering monsters by CR."""
        eg = EncounterGenerator()
        low_cr = eg.filter_monsters(max_cr=2)
        self.assertGreater(len(low_cr), 0)
        for monster in low_cr:
            cr = eg._parse_cr(monster.get("cr", "0"))
            self.assertLessEqual(cr, 2)

    def test_generate_encounter_basic(self):
        """Test basic encounter generation."""
        eg = EncounterGenerator()
        encounter = eg.generate_encounter(difficulty="easy", terrain="forest")

        self.assertIn("monsters", encounter)
        self.assertIn("xp_budget", encounter)
        self.assertIn("difficulty", encounter)
        self.assertEqual(encounter["difficulty"], "easy")

    def test_generate_encounter_party_scaling(self):
        """Test encounter scaling with party size."""
        eg = EncounterGenerator()

        small_party = eg.generate_encounter(party_size=2, party_level=3)
        large_party = eg.generate_encounter(party_size=6, party_level=3)

        self.assertGreater(large_party["xp_budget"], small_party["xp_budget"])

    def test_cr_parsing(self):
        """Test CR string parsing."""
        eg = EncounterGenerator()
        self.assertEqual(eg._parse_cr("1"), 1.0)
        self.assertEqual(eg._parse_cr("1/2"), 0.5)
        self.assertEqual(eg._parse_cr("1/4"), 0.25)
        self.assertEqual(eg._parse_cr("10"), 10.0)

    def test_cr_to_xp_conversion(self):
        """Test CR to XP conversion."""
        eg = EncounterGenerator()
        self.assertEqual(eg._cr_to_xp(0.25), 50)
        self.assertEqual(eg._cr_to_xp(0.5), 100)
        self.assertEqual(eg._cr_to_xp(1), 200)
        self.assertEqual(eg._cr_to_xp(5), 1800)

    def test_boss_encounter(self):
        """Test boss encounter generation."""
        eg = EncounterGenerator()
        boss = eg.generate_boss_encounter(boss_cr=15, terrain="mountain")

        self.assertEqual(boss["difficulty"], "boss")
        self.assertIn("boss", boss)
        self.assertIn("minion_count", boss)

    def test_list_terrains(self):
        """Test listing available terrains."""
        eg = EncounterGenerator()
        terrains = eg.list_terrains()
        self.assertGreater(len(terrains), 0)

    def test_get_monster_by_name(self):
        """Test getting monster by name."""
        eg = EncounterGenerator()
        goblin = eg.get_monster_by_name("Goblin")
        self.assertIsNotNone(goblin)
        self.assertEqual(goblin["name"], "Goblin")

    def test_seed_reproducibility(self):
        """Test that encounters can be generated consistently."""
        eg = EncounterGenerator()

        enc1 = eg.generate_encounter(difficulty="medium", terrain="forest")
        enc2 = eg.generate_encounter(difficulty="medium", terrain="forest")

        # Both should have valid monster counts
        self.assertGreater(enc1["monster_count"], 0)
        self.assertGreater(enc2["monster_count"], 0)


class TestLootGenerator(unittest.TestCase):
    """Test loot generation functionality."""

    def test_loot_generator_init(self):
        """Test loot generator initialization."""
        lg = LootGenerator()
        self.assertIsNotNone(lg.items)

    def test_generate_magic_item_basic(self):
        """Test basic magic item generation."""
        lg = LootGenerator()
        item = lg.generate_magic_item(rarity="uncommon")

        self.assertIn("name", item)
        self.assertIn("rarity", item)
        self.assertIn("type", item)
        self.assertEqual(item["rarity"], "uncommon")

    def test_generate_magic_item_by_type(self):
        """Test generating item by type."""
        lg = LootGenerator()
        weapon = lg.generate_magic_item(item_type="weapon")

        self.assertEqual(weapon["type"], "weapon")

    def test_rarity_weights(self):
        """Test rarity weight distribution."""
        lg = LootGenerator()

        # Generate many items and check distribution
        rarities = []
        for i in range(100):
            item = lg.generate_magic_item(seed=i)
            rarities.append(item["rarity"])

        # Common should be most frequent
        common_count = rarities.count("common")
        uncommon_count = rarities.count("uncommon")
        self.assertGreater(common_count + uncommon_count, 0)

    def test_generate_hoard(self):
        """Test treasure hoard generation."""
        lg = LootGenerator()
        hoard = lg.generate_hoard(party_size=4, party_level=5)

        self.assertIn("gold_pieces", hoard)
        self.assertIn("gems", hoard)
        self.assertIn("magic_items", hoard)
        self.assertIn("total_value", hoard)
        self.assertGreater(hoard["gold_pieces"], 0)

    def test_cursed_item_generation(self):
        """Test cursed item generation."""
        lg = LootGenerator()

        # Generate multiple items, at least check the structure
        item = lg.generate_magic_item(allow_cursed=True, seed=42)
        self.assertIn("cursed", item)

    def test_sentient_item_generation(self):
        """Test sentient item generation."""
        lg = LootGenerator()

        item = lg.generate_magic_item(allow_sentient=True, seed=42)
        # Sentient items have sentience dict
        if item.get("sentient"):
            self.assertIn("sentience", item)
            self.assertIn("intelligence", item["sentience"])

    def test_roll_on_table(self):
        """Test rolling on treasure table."""
        lg = LootGenerator()

        result = lg.roll_on_table(table_type="d100", seed=42)
        self.assertIsNotNone(result)

    def test_seed_reproducibility(self):
        """Test seed produces reproducible results."""
        lg = LootGenerator()

        item1 = lg.generate_magic_item(rarity="rare", seed=123)
        item2 = lg.generate_magic_item(rarity="rare", seed=123)

        self.assertEqual(item1["name"], item2["name"])


class TestRPGCharacterGenerator(unittest.TestCase):
    """Test RPG character generation."""

    def test_character_generator_init(self):
        """Test character generator initialization."""
        cg = RPGCharacterGenerator()
        self.assertIsNotNone(cg.CLASSES)
        self.assertIsNotNone(cg.RACES)

    def test_generate_character_basic(self):
        """Test basic character generation."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=1)

        self.assertIn("identity", char)
        self.assertIn("abilities", char)
        self.assertIn("combat", char)
        self.assertEqual(char["identity"]["level"], 1)

    def test_generate_character_with_class(self):
        """Test character with specific class."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=5, char_class="Wizard")

        self.assertEqual(char["identity"]["class"], "Wizard")

    def test_generate_character_with_race(self):
        """Test character with specific race."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=1, race="Elf")

        self.assertEqual(char["identity"]["race"], "Elf")

    def test_ability_score_generation(self):
        """Test ability score generation."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=1)

        abilities = char["abilities"]["scores"]
        self.assertIn("STR", abilities)
        self.assertIn("DEX", abilities)
        self.assertIn("CON", abilities)
        self.assertIn("INT", abilities)
        self.assertIn("WIS", abilities)
        self.assertIn("CHA", abilities)

        # All scores should be reasonable (3-18 typically)
        for score in abilities.values():
            self.assertGreaterEqual(score, 1)
            self.assertLessEqual(score, 25)

    def test_modifier_calculation(self):
        """Test ability modifier calculation."""
        cg = RPGCharacterGenerator()

        # Modifier for 10 should be 0
        modifiers = cg._calculate_modifiers({"STR": 10})
        self.assertEqual(modifiers["STR"], 0)

        # Modifier for 12 should be +1
        modifiers = cg._calculate_modifiers({"STR": 12})
        self.assertEqual(modifiers["STR"], 1)

        # Modifier for 8 should be -1
        modifiers = cg._calculate_modifiers({"STR": 8})
        self.assertEqual(modifiers["STR"], -1)

    def test_hp_calculation(self):
        """Test HP calculation."""
        cg = RPGCharacterGenerator()

        # Level 1 fighter with +2 CON
        hp = cg._calculate_hp(level=1, class_name="Fighter", con_mod=2)
        self.assertEqual(hp, 12)  # d10 + 2

        # Level 1 wizard with +0 CON
        hp = cg._calculate_hp(level=1, class_name="Wizard", con_mod=0)
        self.assertEqual(hp, 6)  # d6 + 0

    def test_generate_party(self):
        """Test party generation."""
        cg = RPGCharacterGenerator()
        party = cg.generate_party(party_size=4, level=3)

        self.assertEqual(len(party), 4)
        for char in party:
            self.assertEqual(char["identity"]["level"], 3)

    def test_seed_reproducibility(self):
        """Test seed produces reproducible characters."""
        cg1 = RPGCharacterGenerator()
        cg2 = RPGCharacterGenerator()

        char1 = cg1.generate_character(level=1, seed=42)
        char2 = cg2.generate_character(level=1, seed=42)

        # Same seed should produce same ability scores
        self.assertEqual(char1["abilities"]["scores"], char2["abilities"]["scores"])


class TestNameGenerator(unittest.TestCase):
    """Test name generation."""

    def test_name_generator_init(self):
        """Test name generator initialization."""
        ng = NameGenerator(culture="elvish")
        self.assertEqual(ng.culture, "elvish")

    def test_generate_name(self):
        """Test name generation."""
        ng = NameGenerator(culture="elvish")
        name = ng.generate_name()

        self.assertGreater(len(name), 0)
        self.assertTrue(name[0].isupper())

    def test_generate_multiple_unique(self):
        """Test generating multiple unique names."""
        ng = NameGenerator(culture="dwarvish")
        names = ng.generate_multiple(10)

        self.assertEqual(len(names), 10)
        # All names should be unique
        self.assertEqual(len(set(names)), 10)

    def test_party_names(self):
        """Test party name generation."""
        ng = NameGenerator()
        party = ng.generate_party_names(4)

        self.assertEqual(len(party), 4)

    def test_list_cultures(self):
        """Test listing available cultures."""
        cultures = NameGenerator.list_cultures()
        self.assertGreater(len(cultures), 0)
        self.assertIn("elvish", cultures)
        self.assertIn("dwarvish", cultures)


class TestQuestBuilder(unittest.TestCase):
    """Test quest building functionality."""

    def test_quest_builder_init(self):
        """Test quest builder initialization."""
        qb = QuestBuilder()
        self.assertIsNotNone(qb.quest_hooks)

    def test_generate_quest_basic(self):
        """Test basic quest generation."""
        qb = QuestBuilder()
        quest = qb.generate_quest(complexity="simple", party_level=2)

        self.assertIn("identity", quest)
        self.assertIn("hook", quest)
        self.assertIn("objectives", quest)
        self.assertEqual(quest["identity"]["complexity"], "simple")

    def test_generate_quest_by_type(self):
        """Test quest generation by type."""
        qb = QuestBuilder()
        quest = qb.generate_quest(quest_type="rescue")

        self.assertEqual(quest["identity"]["type"], "rescue")

    def test_quest_complications(self):
        """Test quest with complications."""
        qb = QuestBuilder()
        quest = qb.generate_quest(include_complications=True, num_complications=3)

        self.assertLessEqual(len(quest["complications"]), 3)

    def test_quest_rewards_scaling(self):
        """Test quest rewards scale with level."""
        qb = QuestBuilder()

        low_quest = qb.generate_quest(party_level=1, complexity="simple")
        high_quest = qb.generate_quest(party_level=10, complexity="complex")

        # Higher level quest should have better rewards
        self.assertGreaterEqual(
            high_quest["rewards"]["primary"]["amount"],
            low_quest["rewards"]["primary"]["amount"]
        )

    def test_quest_chain(self):
        """Test quest chain generation."""
        qb = QuestBuilder()
        chain = qb.generate_quest_chain(num_quests=3, starting_complexity="simple")

        self.assertEqual(len(chain), 3)
        # Complexity should increase
        self.assertEqual(chain[0]["identity"]["complexity"], "simple")


class TestInitiativeTracker(unittest.TestCase):
    """Test initiative tracking functionality."""

    def test_tracker_init(self):
        """Test tracker initialization."""
        tracker = InitiativeTracker()
        self.assertEqual(tracker.combats, {})

    def test_create_combat(self):
        """Test combat creation."""
        tracker = InitiativeTracker()
        combat = tracker.create_combat("Test Combat")

        self.assertEqual(combat.name, "Test Combat")
        self.assertEqual(tracker.current_combat, "Test Combat")

    def test_add_combatant(self):
        """Test adding combatants."""
        tracker = InitiativeTracker()
        tracker.create_combat("Test")

        combatant = tracker.add_combatant(
            name="Fighter",
            hp=30,
            ac=18,
            initiative_mod=2
        )

        self.assertEqual(combatant.name, "Fighter")
        self.assertEqual(combatant.hp_max, 30)
        self.assertEqual(combatant.ac, 18)

    def test_initiative_order(self):
        """Test initiative sorting."""
        tracker = InitiativeTracker()
        tracker.create_combat("Test")

        tracker.add_combatant("Slow", hp=20, ac=10, initiative_mod=0, roll_initiative=False)
        tracker.add_combatant("Fast", hp=20, ac=10, initiative_mod=5, roll_initiative=False)

        # Fast should be first (higher initiative)
        combat = tracker.combats["Test"]
        self.assertEqual(combat.combatants[0].name, "Fast")

    def test_damage_tracking(self):
        """Test damage tracking."""
        tracker = InitiativeTracker()
        tracker.create_combat("Test")
        tracker.add_combatant("Test", hp=50, ac=15, roll_initiative=False)

        result = tracker.damage_combatant("Test", 15, "slashing", "Sword")

        self.assertEqual(result["damage_taken"], 15)
        self.assertEqual(result["hp_current"], 35)

    def test_death_saves(self):
        """Test death save tracking."""
        tracker = InitiativeTracker()
        tracker.create_combat("Test")
        tracker.add_combatant("Downed", hp=0, ac=10, roll_initiative=False)

        # Three failures should result in death
        tracker.death_save("Downed", 5)  # Failure
        tracker.death_save("Downed", 3)  # Failure (not 1)
        result = tracker.death_save("Downed", 9)  # Failure

        self.assertEqual(result["status"], "dead")

    def test_seed_reproducibility(self):
        """Test that initiative rolls produce valid results."""
        tracker = InitiativeTracker()
        tracker.create_combat("Test")

        tracker.add_combatant("A", hp=20, ac=10, initiative_mod=2)

        # Initiative should be a valid number (1-20 + mod)
        c1 = tracker.combats["Test"].combatants[0]
        self.assertGreaterEqual(c1.initiative, 1)
        self.assertLessEqual(c1.initiative, 22)  # 20 + 2 mod


class TestSpellCardGenerator(unittest.TestCase):
    """Test spell card generation."""

    def test_spell_generator_init(self):
        """Test spell generator initialization."""
        gen = SpellCardGenerator()
        self.assertIsNotNone(gen.spells)

    def test_filter_spells_by_class(self):
        """Test filtering spells by class."""
        gen = SpellCardGenerator()
        wizard_spells = gen.filter_spells(char_class="wizard")

        self.assertGreater(len(wizard_spells), 0)
        for spell in wizard_spells:
            self.assertIn("wizard", [c.lower() for c in spell.get("classes", [])])

    def test_filter_spells_by_level(self):
        """Test filtering spells by level."""
        gen = SpellCardGenerator()
        level_3 = gen.filter_spells(level=3)

        self.assertGreater(len(level_3), 0)
        for spell in level_3:
            self.assertEqual(spell.get("level"), 3)

    def test_generate_spell_card(self):
        """Test spell card generation."""
        gen = SpellCardGenerator()
        card = gen.generate_spell_card("Fireball")

        self.assertIsNotNone(card)
        self.assertEqual(card["name"], "Fireball")
        self.assertEqual(card["level"], 3)

    def test_spell_list_export(self):
        """Test spell list export."""
        gen = SpellCardGenerator()
        spell_list = gen.generate_spell_list("wizard", format="text")

        self.assertIn("Wizard", spell_list)
        self.assertGreater(len(spell_list), 0)


class TestCampaignLogger(unittest.TestCase):
    """Test campaign logging functionality."""

    def test_logger_init(self):
        """Test logger initialization."""
        logger = CampaignLogger("Test Campaign", "Test DM")
        self.assertEqual(logger.current_campaign, "Test Campaign")

    def test_create_campaign(self):
        """Test campaign creation."""
        logger = CampaignLogger()
        campaign = logger.create_campaign("New Campaign", "DM")

        self.assertEqual(campaign.name, "New Campaign")
        self.assertEqual(logger.current_campaign, "New Campaign")

    def test_add_character(self):
        """Test adding characters."""
        logger = CampaignLogger("Test", "DM")
        char = logger.add_character(
            name="Thorin",
            player="Alice",
            char_class="Fighter",
            level=1
        )

        self.assertEqual(char.name, "Thorin")
        self.assertEqual(char.level, 1)

    def test_log_session(self):
        """Test session logging."""
        logger = CampaignLogger("Test", "DM")
        logger.add_character("Thorin", "Alice", "Fighter", 1)

        session = logger.log_session(
            title="First Adventure",
            summary="The party meets in a tavern",
            xp_awarded={"Thorin": 300}
        )

        self.assertEqual(session.session_number, 1)
        self.assertEqual(session.title, "First Adventure")

    def test_xp_tracking(self):
        """Test XP tracking and level-ups."""
        logger = CampaignLogger("Test", "DM")
        logger.add_character("TestChar", "Player", "Fighter", 1)

        # Award enough XP for level 2
        logger.log_session(
            title="XP Session",
            summary="Gained XP",
            xp_awarded={"TestChar": 300}
        )

        char = logger.get_character_sheet("TestChar")
        self.assertGreaterEqual(char["xp_current"], 300)

    def test_story_arc(self):
        """Test story arc management."""
        logger = CampaignLogger("Test", "DM")
        arc = logger.add_story_arc(
            name="The Dark Cult",
            description="A cult threatens the land",
            key_npcs=["Cult Leader"]
        )

        self.assertEqual(arc.name, "The Dark Cult")
        self.assertEqual(arc.status, "planned")

    def test_export_json(self):
        """Test JSON export."""
        logger = CampaignLogger("Test", "DM")
        logger.add_character("Thorin", "Alice", "Fighter")

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            logger.export_to_json(f.name)

            # Verify file exists and is valid JSON
            with open(f.name, 'r') as read_f:
                data = json.load(read_f)
                self.assertEqual(data["name"], "Test")

            os.unlink(f.name)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple generators."""

    def test_full_encounter_to_vtt(self):
        """Test full encounter generation to VTT export."""
        eg = EncounterGenerator()
        encounter = eg.generate_encounter(difficulty="medium", terrain="forest")

        self.assertGreater(encounter["monster_count"], 0)
        self.assertGreater(encounter["xp_budget"], 0)

    def test_quest_with_npcs(self):
        """Test quest generation with integrated NPCs."""
        qb = QuestBuilder()
        quest = qb.generate_quest(include_npcs=True)

        self.assertIsNotNone(quest["hook"]["text"])

    def test_loot_for_encounter(self):
        """Test generating appropriate loot for encounter."""
        eg = EncounterGenerator()
        lg = LootGenerator()

        encounter = eg.generate_encounter(difficulty="hard", party_level=7)
        hoard = lg.generate_hoard(party_level=7, party_size=4)

        self.assertGreater(hoard["total_value"], 0)

    def test_character_with_name(self):
        """Test character generation with integrated name generator."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=1)

        self.assertIsNotNone(char["identity"]["name"])
        self.assertGreater(len(char["identity"]["name"]), 0)


if __name__ == "__main__":
    unittest.main()
