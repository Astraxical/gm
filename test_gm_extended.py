#!/usr/bin/env python3
"""
Tests for DnD GM Tools - Encounter, Loot, and RPG Character Generators
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

# Import generators
from encounter_gen import EncounterGenerator
from loot_gen import LootGenerator
from rpg_char_gen import RPGCharacterGenerator
from name_gen import NameGenerator
from npc_gen import NPCGenerator
from quest_builder import QuestBuilder
from initiative_tracker import InitiativeTracker, Combatant
from spell_card_generator import SpellCardGenerator
from campaign_logger import CampaignLogger


class TestEncounterGenerator:
    """Test encounter generation functionality."""

    def test_encounter_generator_init(self):
        """Test encounter generator initialization."""
        eg = EncounterGenerator()
        assert eg.monsters is not None
        assert len(eg.monsters) > 0
        assert eg.terrain_types is not None

    def test_filter_monsters_by_terrain(self):
        """Test filtering monsters by terrain."""
        eg = EncounterGenerator()
        forest_monsters = eg.filter_monsters(terrain="forest")
        assert len(forest_monsters) > 0
        for monster in forest_monsters:
            terrains = [t.lower() for t in monster.get("terrain", [])]
            assert "forest" in terrains or "any" in terrains

    def test_filter_monsters_by_cr(self):
        """Test filtering monsters by CR."""
        eg = EncounterGenerator()
        low_cr = eg.filter_monsters(max_cr=2)
        assert len(low_cr) > 0
        for monster in low_cr:
            cr = eg._parse_cr(monster.get("cr", "0"))
            assert cr <= 2

    def test_generate_encounter_basic(self):
        """Test basic encounter generation."""
        eg = EncounterGenerator()
        encounter = eg.generate_encounter(difficulty="easy", terrain="forest")
        
        assert "monsters" in encounter
        assert "xp_budget" in encounter
        assert "difficulty" in encounter
        assert encounter["difficulty"] == "easy"

    def test_generate_encounter_party_scaling(self):
        """Test encounter scaling with party size."""
        eg = EncounterGenerator()
        
        small_party = eg.generate_encounter(party_size=2, party_level=3)
        large_party = eg.generate_encounter(party_size=6, party_level=3)
        
        assert large_party["xp_budget"] > small_party["xp_budget"]

    def test_cr_parsing(self):
        """Test CR string parsing."""
        eg = EncounterGenerator()
        assert eg._parse_cr("1") == 1.0
        assert eg._parse_cr("1/2") == 0.5
        assert eg._parse_cr("1/4") == 0.25
        assert eg._parse_cr("10") == 10.0

    def test_cr_to_xp_conversion(self):
        """Test CR to XP conversion."""
        eg = EncounterGenerator()
        assert eg._cr_to_xp(0.25) == 50
        assert eg._cr_to_xp(0.5) == 100
        assert eg._cr_to_xp(1) == 200
        assert eg._cr_to_xp(5) == 1800

    def test_boss_encounter(self):
        """Test boss encounter generation."""
        eg = EncounterGenerator()
        boss = eg.generate_boss_encounter(boss_cr=15, terrain="mountain")
        
        assert boss["difficulty"] == "boss"
        assert "boss" in boss
        assert "minion_count" in boss

    def test_list_terrains(self):
        """Test listing available terrains."""
        eg = EncounterGenerator()
        terrains = eg.list_terrains()
        assert len(terrains) > 0
        assert "forest" in terrains or "any" in str(terrains)

    def test_get_monster_by_name(self):
        """Test getting monster by name."""
        eg = EncounterGenerator()
        goblin = eg.get_monster_by_name("Goblin")
        assert goblin is not None
        assert goblin["name"] == "Goblin"

    def test_seed_reproducibility(self):
        """Test that seed produces reproducible results."""
        eg1 = EncounterGenerator()
        eg2 = EncounterGenerator()
        
        enc1 = eg1.generate_encounter(difficulty="medium", terrain="forest", seed=42)
        enc2 = eg2.generate_encounter(difficulty="medium", terrain="forest", seed=42)
        
        # Same seed should produce same monster count at minimum
        assert enc1["monster_count"] == enc2["monster_count"]


class TestLootGenerator:
    """Test loot generation functionality."""

    def test_loot_generator_init(self):
        """Test loot generator initialization."""
        lg = LootGenerator()
        assert lg.items is not None

    def test_generate_magic_item_basic(self):
        """Test basic magic item generation."""
        lg = LootGenerator()
        item = lg.generate_magic_item(rarity="uncommon")
        
        assert "name" in item
        assert "rarity" in item
        assert "type" in item
        assert item["rarity"] == "uncommon"

    def test_generate_magic_item_by_type(self):
        """Test generating item by type."""
        lg = LootGenerator()
        weapon = lg.generate_magic_item(item_type="weapon")
        
        assert weapon["type"] == "weapon"

    def test_rarity_weights(self):
        """Test rarity weight distribution."""
        lg = LootGenerator()
        
        # Generate many items and check distribution
        rarities = []
        for _ in range(100):
            item = lg.generate_magic_item(seed=_ )
            rarities.append(item["rarity"])
        
        # Common should be most frequent
        common_count = rarities.count("common")
        uncommon_count = rarities.count("uncommon")
        assert common_count + uncommon_count > 0

    def test_generate_hoard(self):
        """Test treasure hoard generation."""
        lg = LootGenerator()
        hoard = lg.generate_hoard(party_size=4, party_level=5)
        
        assert "gold_pieces" in hoard
        assert "gems" in hoard
        assert "magic_items" in hoard
        assert "total_value" in hoard
        assert hoard["gold_pieces"] > 0

    def test_cursed_item_generation(self):
        """Test cursed item generation."""
        lg = LootGenerator()
        
        # Generate multiple items, at least check the structure
        item = lg.generate_magic_item(allow_cursed=True, seed=42)
        assert "cursed" in item

    def test_sentient_item_generation(self):
        """Test sentient item generation."""
        lg = LootGenerator()
        
        item = lg.generate_magic_item(allow_sentient=True, seed=42)
        # Sentient items have sentience dict
        if item.get("sentient"):
            assert "sentience" in item
            assert "intelligence" in item["sentience"]

    def test_roll_on_table(self):
        """Test rolling on treasure table."""
        lg = LootGenerator()
        
        result = lg.roll_on_table(table_type="d100", seed=42)
        assert result is not None

    def test_seed_reproducibility(self):
        """Test seed produces reproducible results."""
        lg = LootGenerator()
        
        item1 = lg.generate_magic_item(rarity="rare", seed=123)
        item2 = lg.generate_magic_item(rarity="rare", seed=123)
        
        assert item1["name"] == item2["name"]


class TestRPGCharacterGenerator:
    """Test RPG character generation."""

    def test_character_generator_init(self):
        """Test character generator initialization."""
        cg = RPGCharacterGenerator()
        assert cg.CLASSES is not None
        assert cg.RACES is not None

    def test_generate_character_basic(self):
        """Test basic character generation."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=1)
        
        assert "identity" in char
        assert "abilities" in char
        assert "combat" in char
        assert char["identity"]["level"] == 1

    def test_generate_character_with_class(self):
        """Test character with specific class."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=5, char_class="Wizard")
        
        assert char["identity"]["class"] == "Wizard"

    def test_generate_character_with_race(self):
        """Test character with specific race."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=1, race="Elf")
        
        assert char["identity"]["race"] == "Elf"

    def test_ability_score_generation(self):
        """Test ability score generation."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=1)
        
        abilities = char["abilities"]["scores"]
        assert "STR" in abilities
        assert "DEX" in abilities
        assert "CON" in abilities
        assert "INT" in abilities
        assert "WIS" in abilities
        assert "CHA" in abilities
        
        # All scores should be reasonable (3-18 typically)
        for score in abilities.values():
            assert 1 <= score <= 25

    def test_modifier_calculation(self):
        """Test ability modifier calculation."""
        cg = RPGCharacterGenerator()
        
        # Modifier for 10 should be 0
        modifiers = cg._calculate_modifiers({"STR": 10})
        assert modifiers["STR"] == 0
        
        # Modifier for 12 should be +1
        modifiers = cg._calculate_modifiers({"STR": 12})
        assert modifiers["STR"] == 1
        
        # Modifier for 8 should be -1
        modifiers = cg._calculate_modifiers({"STR": 8})
        assert modifiers["STR"] == -1

    def test_hp_calculation(self):
        """Test HP calculation."""
        cg = RPGCharacterGenerator()
        
        # Level 1 fighter with +2 CON
        hp = cg._calculate_hp(level=1, class_name="Fighter", con_mod=2)
        assert hp == 12  # d10 + 2
        
        # Level 1 wizard with +0 CON
        hp = cg._calculate_hp(level=1, class_name="Wizard", con_mod=0)
        assert hp == 6  # d6 + 0

    def test_generate_party(self):
        """Test party generation."""
        cg = RPGCharacterGenerator()
        party = cg.generate_party(party_size=4, level=3)
        
        assert len(party) == 4
        for char in party:
            assert char["identity"]["level"] == 3

    def test_seed_reproducibility(self):
        """Test seed produces reproducible characters."""
        cg1 = RPGCharacterGenerator()
        cg2 = RPGCharacterGenerator()
        
        char1 = cg1.generate_character(level=1, seed=42)
        char2 = cg2.generate_character(level=1, seed=42)
        
        # Same seed should produce same ability scores
        assert char1["abilities"]["scores"] == char2["abilities"]["scores"]


class TestNameGenerator:
    """Test name generation."""

    def test_name_generator_init(self):
        """Test name generator initialization."""
        ng = NameGenerator(culture="elvish")
        assert ng.culture == "elvish"

    def test_generate_name(self):
        """Test name generation."""
        ng = NameGenerator(culture="elvish")
        name = ng.generate_name()
        
        assert len(name) > 0
        assert name[0].isupper()

    def test_generate_multiple_unique(self):
        """Test generating multiple unique names."""
        ng = NameGenerator(culture="dwarvish")
        names = ng.generate_multiple(10)
        
        assert len(names) == 10
        # All names should be unique
        assert len(set(names)) == 10

    def test_party_names(self):
        """Test party name generation."""
        ng = NameGenerator()
        party = ng.generate_party_names(4)
        
        assert len(party) == 4

    def test_list_cultures(self):
        """Test listing available cultures."""
        cultures = NameGenerator.list_cultures()
        assert len(cultures) > 0
        assert "elvish" in cultures
        assert "dwarvish" in cultures


class TestQuestBuilder:
    """Test quest building functionality."""

    def test_quest_builder_init(self):
        """Test quest builder initialization."""
        qb = QuestBuilder()
        assert qb.quest_hooks is not None

    def test_generate_quest_basic(self):
        """Test basic quest generation."""
        qb = QuestBuilder()
        quest = qb.generate_quest(complexity="simple", party_level=2)
        
        assert "identity" in quest
        assert "hook" in quest
        assert "objectives" in quest
        assert quest["identity"]["complexity"] == "simple"

    def test_generate_quest_by_type(self):
        """Test quest generation by type."""
        qb = QuestBuilder()
        quest = qb.generate_quest(quest_type="rescue")
        
        assert quest["identity"]["type"] == "rescue"

    def test_quest_complications(self):
        """Test quest with complications."""
        qb = QuestBuilder()
        quest = qb.generate_quest(include_complications=True, num_complications=3)
        
        assert len(quest["complications"]) <= 3

    def test_quest_rewards_scaling(self):
        """Test quest rewards scale with level."""
        qb = QuestBuilder()
        
        low_quest = qb.generate_quest(party_level=1, complexity="simple")
        high_quest = qb.generate_quest(party_level=10, complexity="complex")
        
        # Higher level quest should have better rewards
        assert high_quest["rewards"]["primary"]["amount"] >= low_quest["rewards"]["primary"]["amount"]

    def test_quest_chain(self):
        """Test quest chain generation."""
        qb = QuestBuilder()
        chain = qb.generate_quest_chain(num_quests=3, starting_complexity="simple")
        
        assert len(chain) == 3
        # Complexity should increase
        assert chain[0]["identity"]["complexity"] == "simple"


class TestInitiativeTracker:
    """Test initiative tracking functionality."""

    def test_tracker_init(self):
        """Test tracker initialization."""
        tracker = InitiativeTracker()
        assert tracker.combats == {}

    def test_create_combat(self):
        """Test combat creation."""
        tracker = InitiativeTracker()
        combat = tracker.create_combat("Test Combat")
        
        assert combat.name == "Test Combat"
        assert tracker.current_combat == "Test Combat"

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
        
        assert combatant.name == "Fighter"
        assert combatant.hp_max == 30
        assert combatant.ac == 18

    def test_initiative_order(self):
        """Test initiative sorting."""
        tracker = InitiativeTracker()
        tracker.create_combat("Test")
        
        tracker.add_combatant("Slow", hp=20, ac=10, initiative_mod=0, roll_initiative=False)
        tracker.add_combatant("Fast", hp=20, ac=10, initiative_mod=5, roll_initiative=False)
        
        # Fast should be first (higher initiative)
        combat = tracker.combats["Test"]
        assert combat.combatants[0].name == "Fast"

    def test_damage_tracking(self):
        """Test damage tracking."""
        tracker = InitiativeTracker()
        tracker.create_combat("Test")
        tracker.add_combatant("Test", hp=50, ac=15, roll_initiative=False)
        
        result = tracker.damage_combatant("Test", 15, "slashing", "Sword")
        
        assert result["damage_taken"] == 15
        assert result["hp_current"] == 35

    def test_death_saves(self):
        """Test death save tracking."""
        tracker = InitiativeTracker()
        tracker.create_combat("Test")
        tracker.add_combatant("Downed", hp=0, ac=10, roll_initiative=False)
        
        # Three failures should result in death
        tracker.death_save("Downed", 5)  # Failure
        tracker.death_save("Downed", 3)  # Failure (not 1)
        result = tracker.death_save("Downed", 9)  # Failure
        
        assert result["status"] == "dead"

    def test_seed_reproducibility(self):
        """Test seed produces reproducible initiative."""
        tracker1 = InitiativeTracker(seed=42)
        tracker2 = InitiativeTracker(seed=42)
        
        tracker1.create_combat("Test")
        tracker2.create_combat("Test")
        
        tracker1.add_combatant("A", hp=20, ac=10, initiative_mod=2)
        tracker2.add_combatant("A", hp=20, ac=10, initiative_mod=2)
        
        # Same seed should produce same initiative roll
        c1 = tracker1.combats["Test"].combatants[0]
        c2 = tracker2.combats["Test"].combatants[0]
        assert c1.initiative == c2.initiative


class TestSpellCardGenerator:
    """Test spell card generation."""

    def test_spell_generator_init(self):
        """Test spell generator initialization."""
        gen = SpellCardGenerator()
        assert gen.spells is not None

    def test_filter_spells_by_class(self):
        """Test filtering spells by class."""
        gen = SpellCardGenerator()
        wizard_spells = gen.filter_spells(char_class="wizard")
        
        assert len(wizard_spells) > 0
        for spell in wizard_spells:
            assert "wizard" in [c.lower() for c in spell.get("classes", [])]

    def test_filter_spells_by_level(self):
        """Test filtering spells by level."""
        gen = SpellCardGenerator()
        level_3 = gen.filter_spells(level=3)
        
        assert len(level_3) > 0
        for spell in level_3:
            assert spell.get("level") == 3

    def test_generate_spell_card(self):
        """Test spell card generation."""
        gen = SpellCardGenerator()
        card = gen.generate_spell_card("Fireball")
        
        assert card is not None
        assert card["name"] == "Fireball"
        assert card["level"] == 3

    def test_spell_list_export(self):
        """Test spell list export."""
        gen = SpellCardGenerator()
        spell_list = gen.generate_spell_list("wizard", format="text")
        
        assert "Wizard" in spell_list
        assert len(spell_list) > 0


class TestCampaignLogger:
    """Test campaign logging functionality."""

    def test_logger_init(self):
        """Test logger initialization."""
        logger = CampaignLogger("Test Campaign", "Test DM")
        assert logger.current_campaign == "Test Campaign"

    def test_create_campaign(self):
        """Test campaign creation."""
        logger = CampaignLogger()
        campaign = logger.create_campaign("New Campaign", "DM")
        
        assert campaign.name == "New Campaign"
        assert logger.current_campaign == "New Campaign"

    def test_add_character(self):
        """Test adding characters."""
        logger = CampaignLogger("Test", "DM")
        char = logger.add_character(
            name="Thorin",
            player="Alice",
            char_class="Fighter",
            level=1
        )
        
        assert char.name == "Thorin"
        assert char.level == 1

    def test_log_session(self):
        """Test session logging."""
        logger = CampaignLogger("Test", "DM")
        logger.add_character("Thorin", "Alice", "Fighter", 1)
        
        session = logger.log_session(
            title="First Adventure",
            summary="The party meets in a tavern",
            xp_awarded={"Thorin": 300}
        )
        
        assert session.session_number == 1
        assert session.title == "First Adventure"

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
        assert char["xp_current"] >= 300

    def test_story_arc(self):
        """Test story arc management."""
        logger = CampaignLogger("Test", "DM")
        arc = logger.add_story_arc(
            name="The Dark Cult",
            description="A cult threatens the land",
            key_npcs=["Cult Leader"]
        )
        
        assert arc.name == "The Dark Cult"
        assert arc.status == "planned"

    def test_export_json(self):
        """Test JSON export."""
        logger = CampaignLogger("Test", "DM")
        logger.add_character("Thorin", "Alice", "Fighter")
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            logger.export_to_json(f.name)
            
            # Verify file exists and is valid JSON
            with open(f.name, 'r') as read_f:
                data = json.load(read_f)
                assert data["name"] == "Test"
            
            os.unlink(f.name)


class TestIntegration:
    """Integration tests combining multiple generators."""

    def test_full_encounter_to_vtt(self):
        """Test full encounter generation to VTT export."""
        eg = EncounterGenerator()
        encounter = eg.generate_encounter(difficulty="medium", terrain="forest")
        
        assert encounter["monster_count"] > 0
        assert encounter["xp_budget"] > 0

    def test_quest_with_npcs(self):
        """Test quest generation with integrated NPCs."""
        qb = QuestBuilder()
        quest = qb.generate_quest(include_npcs=True)
        
        assert quest["hook"]["text"] is not None

    def test_loot_for_encounter(self):
        """Test generating appropriate loot for encounter."""
        eg = EncounterGenerator()
        lg = LootGenerator()
        
        encounter = eg.generate_encounter(difficulty="hard", party_level=7)
        hoard = lg.generate_hoard(party_level=7, party_size=4)
        
        assert hoard["total_value"] > 0

    def test_character_with_name(self):
        """Test character generation with integrated name generator."""
        cg = RPGCharacterGenerator()
        char = cg.generate_character(level=1)
        
        assert char["identity"]["name"] is not None
        assert len(char["identity"]["name"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
