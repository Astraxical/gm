#!/usr/bin/env python3
"""
Tests for the Template-based Sentence Generator (sentence_forge.py)
Converted from pytest to unittest for stdlib compatibility
"""

import json
import csv
import os
import tempfile
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utilities.sentence_forge import SentenceGenerator


class TestSentenceGeneratorBasic(unittest.TestCase):
    """Test basic functionality."""

    def test_single_template_no_placeholders(self):
        """Test template without placeholders."""
        gen = SentenceGenerator("Hello World")
        self.assertEqual(gen.placeholders, [])
        self.assertEqual(gen.generate(), "Hello World")

    def test_single_placeholder(self):
        """Test template with one placeholder."""
        gen = SentenceGenerator("{USER} is here")
        gen.set_values("USER", ["Alice", "Bob"])
        result = gen.generate(seed=42)
        self.assertIn(result, ["Alice is here", "Bob is here"])

    def test_multiple_placeholders(self):
        """Test template with multiple placeholders."""
        gen = SentenceGenerator("{USER} {ACTION} {TARGET}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("ACTION", ["killed"])
        gen.set_values("TARGET", ["Bob"])
        self.assertEqual(gen.generate(), "Alice killed Bob")

    def test_method_chaining(self):
        """Test method chaining."""
        gen = (SentenceGenerator("{USER} is {STATUS}")
               .set_values("USER", ["Alice"])
               .set_values("STATUS", ["happy"]))
        self.assertEqual(gen.generate(), "Alice is happy")


class TestSentenceGeneratorMultipleTemplates(unittest.TestCase):
    """Test multiple template variations."""

    def test_multiple_templates(self):
        """Test with multiple template variations."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        gen.set_values("USER", ["Alice"])
        result = gen.generate(seed=42)
        self.assertIn(result, ["Alice won", "Alice lost"])

    def test_add_template(self):
        """Test adding templates dynamically."""
        gen = SentenceGenerator("{USER} won")
        gen.add_template("{USER} lost")
        self.assertEqual(len(gen.templates), 2)

    def test_remove_template(self):
        """Test removing templates."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        gen.remove_template(0)
        self.assertEqual(len(gen.templates), 1)
        self.assertEqual(gen.templates[0], "{USER} lost")

    def test_clear_templates(self):
        """Test clearing all templates."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        gen.clear_templates()
        self.assertEqual(len(gen.templates), 0)
        self.assertEqual(gen.placeholders, [])


class TestInlineAlternatives(unittest.TestCase):
    """Test inline alternatives feature."""

    def test_simple_alternatives(self):
        """Test simple inline alternatives."""
        gen = SentenceGenerator("{USER} {killed|eliminated} {TARGET}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("TARGET", ["Bob"])
        result = gen.generate(seed=42)
        self.assertIn(result, ["Alice killed Bob", "Alice eliminated Bob"])

    def test_weighted_alternatives(self):
        """Test weighted inline alternatives."""
        gen = SentenceGenerator("{USER} {killed:3|eliminated:1} {TARGET}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("TARGET", ["Bob"])
        # With seed, should be deterministic
        results = [gen.generate(seed=i) for i in range(10)]
        # "killed" has 3x weight, should appear more often
        killed_count = sum(1 for r in results if "killed" in r)
        self.assertGreater(killed_count, 3)  # Should be roughly 75%

    def test_multiple_alternatives_in_template(self):
        """Test multiple inline alternatives in one template."""
        gen = SentenceGenerator("{USER} {killed|eliminated} {TARGET} {quietly|silently}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("TARGET", ["Bob"])
        result = gen.generate()
        # Should contain one word from each alternative
        self.assertTrue(any(word in result for word in ["killed", "eliminated"]))
        self.assertTrue(any(word in result for word in ["quietly", "silently"]))


class TestTransforms(unittest.TestCase):
    """Test transform functions."""

    def test_upper_transform(self):
        """Test uppercase transform."""
        gen = SentenceGenerator("{USER|upper}")
        gen.set_values("USER", ["alice"])
        self.assertEqual(gen.generate(), "ALICE")

    def test_lower_transform(self):
        """Test lowercase transform."""
        gen = SentenceGenerator("{USER|lower}")
        gen.set_values("USER", ["ALICE"])
        self.assertEqual(gen.generate(), "alice")

    def test_title_transform(self):
        """Test title case transform."""
        gen = SentenceGenerator("{USER|title}")
        gen.set_values("USER", ["alice smith"])
        self.assertEqual(gen.generate(), "Alice Smith")

    def test_capitalize_transform(self):
        """Test capitalize transform."""
        gen = SentenceGenerator("{USER|capitalize}")
        gen.set_values("USER", ["alice smith"])
        self.assertEqual(gen.generate(), "Alice smith")

    def test_truncate_transform(self):
        """Test truncate transform."""
        gen = SentenceGenerator("{USER|truncate:5}")
        gen.set_values("USER", ["Alexander"])
        self.assertEqual(gen.generate(), "Alexa")

    def test_default_transform(self):
        """Test default transform for empty values."""
        gen = SentenceGenerator("Hello {USER|default:Guest}")
        gen.set_values("USER", [""])
        self.assertEqual(gen.generate(), "Hello Guest")

    def test_a_transform_vowel(self):
        """Test 'a' transform with vowel start."""
        gen = SentenceGenerator("I saw {USER|a}")
        gen.set_values("USER", ["elephant"])
        self.assertEqual(gen.generate(), "I saw an elephant")

    def test_a_transform_consonant(self):
        """Test 'a' transform with consonant start."""
        gen = SentenceGenerator("I saw {USER|a}")
        gen.set_values("USER", ["cat"])
        self.assertEqual(gen.generate(), "I saw a cat")

    def test_plural_transform_regular(self):
        """Test plural transform on regular noun."""
        gen = SentenceGenerator("I have {NUM} {ITEM|plural}")
        gen.set_values("NUM", ["many"])
        gen.set_values("ITEM", ["cat"])
        self.assertEqual(gen.generate(), "I have many cats")

    def test_plural_transform_es(self):
        """Test plural transform on words ending in -s, -sh, -ch, -x, -z."""
        gen = SentenceGenerator("Multiple {ITEM|plural}")
        gen.set_values("ITEM", ["box"])
        self.assertEqual(gen.generate(), "Multiple boxes")

    def test_plural_transform_ies(self):
        """Test plural transform on words ending in consonant+y."""
        gen = SentenceGenerator("Multiple {ITEM|plural}")
        gen.set_values("ITEM", ["city"])
        self.assertEqual(gen.generate(), "Multiple cities")

    def test_pluralize_custom_suffix(self):
        """Test pluralize with custom suffix."""
        gen = SentenceGenerator("{ITEM|pluralize:es}")
        gen.set_values("ITEM", ["bus"])
        self.assertEqual(gen.generate(), "buses")


class TestGenerateAll(unittest.TestCase):
    """Test generate_all functionality."""

    def test_generate_all_combinations(self):
        """Test generating all combinations."""
        gen = SentenceGenerator("{USER} is {STATUS}")
        gen.set_values("USER", ["Alice", "Bob"])
        gen.set_values("STATUS", ["happy", "sad"])
        results = gen.generate_all()
        self.assertEqual(len(results), 4)
        self.assertIn("Alice is happy", results)
        self.assertIn("Alice is sad", results)
        self.assertIn("Bob is happy", results)
        self.assertIn("Bob is sad", results)

    def test_generate_all_with_inline_alternatives(self):
        """Test generate_all with inline alternatives."""
        gen = SentenceGenerator("{USER} {won|lost}")
        gen.set_values("USER", ["Alice"])
        results = gen.generate_all()
        self.assertEqual(len(results), 2)
        self.assertIn("Alice won", results)
        self.assertIn("Alice lost", results)


class TestGenerateMultiple(unittest.TestCase):
    """Test generate_multiple functionality."""

    def test_generate_multiple(self):
        """Test generating multiple sentences."""
        gen = SentenceGenerator("{USER} is here")
        gen.set_values("USER", ["Alice", "Bob", "Charlie"])
        results = gen.generate_multiple(5, seed=42)
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.endswith(" is here") for r in results))

    def test_generate_multiple_reproducibility(self):
        """Test that seed produces reproducible results."""
        gen = SentenceGenerator("{USER} won")
        gen.set_values("USER", ["Alice", "Bob", "Charlie"])
        results1 = gen.generate_multiple(3, seed=123)
        results2 = gen.generate_multiple(3, seed=123)
        self.assertEqual(results1, results2)


class TestDefaults(unittest.TestCase):
    """Test default values functionality."""

    def test_default_values(self):
        """Test using default values."""
        gen = SentenceGenerator("{USER} is {STATUS}", default_values={"STATUS": "unknown"})
        gen.set_values("USER", ["Alice"])
        self.assertIn("Alice is unknown", gen.generate())

    def test_default_overridden(self):
        """Test that set values override defaults."""
        gen = SentenceGenerator("{USER} is {STATUS}", default_values={"STATUS": "unknown"})
        gen.set_values("USER", ["Alice"])
        gen.set_values("STATUS", ["happy"])
        self.assertEqual(gen.generate(), "Alice is happy")

    def test_use_defaults_false(self):
        """Test that use_defaults=False raises error for missing values."""
        gen = SentenceGenerator("{USER} is {STATUS}", default_values={"STATUS": "unknown"})
        gen.set_values("USER", ["Alice"])
        with self.assertRaises(ValueError) as context:
            gen.generate(use_defaults=False)
        self.assertIn("No values set for placeholder 'STATUS'", str(context.exception))


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""

    def test_invalid_placeholder(self):
        """Test error when setting values for non-existent placeholder."""
        gen = SentenceGenerator("{USER} is here")
        with self.assertRaises(ValueError) as context:
            gen.set_values("INVALID", ["value"])
        self.assertIn("Placeholder 'INVALID' not found", str(context.exception))

    def test_empty_values(self):
        """Test error when setting empty values list."""
        gen = SentenceGenerator("{USER} is here")
        with self.assertRaises(ValueError) as context:
            gen.set_values("USER", [])
        self.assertIn("cannot be empty", str(context.exception))

    def test_missing_values_no_defaults(self):
        """Test error when placeholder has no values and no defaults."""
        gen = SentenceGenerator("{USER} is here")
        with self.assertRaises(ValueError) as context:
            gen.generate(use_defaults=False)
        self.assertIn("No values set for placeholder 'USER'", str(context.exception))


class TestFileLoading(unittest.TestCase):
    """Test loading values from files."""

    def test_load_from_json(self):
        """Test loading values from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"USER": ["Alice", "Bob"]}, f)
            f.flush()
            try:
                gen = SentenceGenerator("{USER} is here")
                gen.load_values_from_json(f.name)
                values = gen.get_values("USER")
                self.assertEqual(values, ["Alice", "Bob"])
            finally:
                os.unlink(f.name)

    def test_load_from_csv(self):
        """Test loading values from CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['placeholder', 'value'])
            writer.writerow(['USER', 'Alice'])
            writer.writerow(['USER', 'Bob'])
            f.flush()
            try:
                gen = SentenceGenerator("{USER} is here")
                gen.load_values_from_csv(f.name)
                values = gen.get_values("USER")
                self.assertEqual(values, ["Alice", "Bob"])
            finally:
                os.unlink(f.name)

    def test_load_from_csv_comma_separated(self):
        """Test loading values from CSV with comma-separated values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['placeholder', 'value'])
            writer.writerow(['USER', 'Alice,Bob,Charlie'])
            f.flush()
            try:
                gen = SentenceGenerator("{USER} is here")
                gen.load_values_from_csv(f.name)
                values = gen.get_values("USER")
                self.assertEqual(values, ["Alice", "Bob", "Charlie"])
            finally:
                os.unlink(f.name)

    def test_load_from_unsupported_format(self):
        """Test error when loading from unsupported format."""
        gen = SentenceGenerator("{USER} is here")
        with self.assertRaises(ValueError) as context:
            gen.load_values_from_file("data.txt")
        self.assertIn("Unsupported file format", str(context.exception))


class TestCaching(unittest.TestCase):
    """Test template caching functionality."""

    def test_cache_used_on_multiple_generates(self):
        """Test that cache is used for multiple generate calls."""
        gen = SentenceGenerator("{USER} {killed|eliminated} {TARGET}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("TARGET", ["Bob"])
        # First call builds cache
        gen.generate()
        cache_after_first = gen._expanded_templates_cache
        # Second call should use same cache
        gen.generate()
        self.assertEqual(gen._expanded_templates_cache, cache_after_first)

    def test_cache_invalidated_on_add_template(self):
        """Test that cache is invalidated when adding templates."""
        gen = SentenceGenerator("{USER} won")
        gen.set_values("USER", ["Alice"])
        gen.generate()
        self.assertIsNotNone(gen._expanded_templates_cache)
        gen.add_template("{USER} lost")
        self.assertIsNone(gen._expanded_templates_cache)

    def test_cache_invalidated_on_remove_template(self):
        """Test that cache is invalidated when removing templates."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        gen.set_values("USER", ["Alice"])
        gen.generate()
        self.assertIsNotNone(gen._expanded_templates_cache)
        gen.remove_template(0)
        self.assertIsNone(gen._expanded_templates_cache)


class TestUtilityMethods(unittest.TestCase):
    """Test utility methods."""

    def test_has_placeholder_true(self):
        """Test has_placeholder returns True for existing placeholder."""
        gen = SentenceGenerator("{USER} is here")
        self.assertTrue(gen.has_placeholder("USER"))

    def test_has_placeholder_false(self):
        """Test has_placeholder returns False for non-existing placeholder."""
        gen = SentenceGenerator("{USER} is here")
        self.assertFalse(gen.has_placeholder("INVALID"))

    def test_get_values(self):
        """Test getting values for a placeholder."""
        gen = SentenceGenerator("{USER} is here")
        gen.set_values("USER", ["Alice", "Bob"])
        self.assertEqual(gen.get_values("USER"), ["Alice", "Bob"])

    def test_get_values_not_set(self):
        """Test getting values when not set returns None."""
        gen = SentenceGenerator("{USER} is here")
        self.assertIsNone(gen.get_values("USER"))

    def test_clear_values(self):
        """Test clearing all values."""
        gen = SentenceGenerator("{USER} is here")
        gen.set_values("USER", ["Alice"])
        gen.clear_values()
        self.assertIsNone(gen.get_values("USER"))

    def test_get_template(self):
        """Test getting template at index."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        self.assertEqual(gen.get_template(0), "{USER} won")
        self.assertEqual(gen.get_template(1), "{USER} lost")

    def test_get_template_invalid_index(self):
        """Test getting template at invalid index."""
        gen = SentenceGenerator("{USER} won")
        with self.assertRaises(IndexError):
            gen.get_template(5)

    def test_repr(self):
        """Test string representation."""
        gen = SentenceGenerator("{USER} is {STATUS}")
        repr_str = repr(gen)
        self.assertIn("SentenceGenerator", repr_str)
        self.assertIn("placeholders=", repr_str)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases."""

    def test_empty_template(self):
        """Test empty template."""
        gen = SentenceGenerator("")
        self.assertEqual(gen.generate(), "")

    def test_placeholder_with_numbers(self):
        """Test placeholder with numbers in name."""
        gen = SentenceGenerator("{USER1} and {USER2}")
        gen.set_values("USER1", ["Alice"])
        gen.set_values("USER2", ["Bob"])
        self.assertEqual(gen.generate(), "Alice and Bob")

    def test_braces_in_value(self):
        """Test values containing braces."""
        gen = SentenceGenerator("{USER}")
        gen.set_values("USER", ["test{value}"])
        # Should not be interpreted as placeholder
        self.assertEqual(gen.generate(), "test{value}")

    def test_whitespace_in_template(self):
        """Test template with extra whitespace."""
        gen = SentenceGenerator("  {USER}  is  {STATUS}  ")
        gen.set_values("USER", ["Alice"])
        gen.set_values("STATUS", ["happy"])
        result = gen.generate()
        self.assertIn("Alice", result)
        self.assertIn("happy", result)


if __name__ == "__main__":
    unittest.main()
