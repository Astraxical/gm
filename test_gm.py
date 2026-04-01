#!/usr/bin/env python3
"""
Tests for the Template-based Sentence Generator (sentence_forge.py)
"""

import pytest
import json
import csv
import os
import tempfile
from sentence_forge import SentenceGenerator


class TestSentenceGeneratorBasic:
    """Test basic functionality."""

    def test_single_template_no_placeholders(self):
        """Test template without placeholders."""
        gen = SentenceGenerator("Hello World")
        assert gen.placeholders == []
        assert gen.generate() == "Hello World"

    def test_single_placeholder(self):
        """Test template with one placeholder."""
        gen = SentenceGenerator("{USER} is here")
        gen.set_values("USER", ["Alice", "Bob"])
        result = gen.generate(seed=42)
        assert result in ["Alice is here", "Bob is here"]

    def test_multiple_placeholders(self):
        """Test template with multiple placeholders."""
        gen = SentenceGenerator("{USER} {ACTION} {TARGET}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("ACTION", ["killed"])
        gen.set_values("TARGET", ["Bob"])
        assert gen.generate() == "Alice killed Bob"

    def test_method_chaining(self):
        """Test method chaining."""
        gen = (SentenceGenerator("{USER} is {STATUS}")
               .set_values("USER", ["Alice"])
               .set_values("STATUS", ["happy"]))
        assert gen.generate() == "Alice is happy"


class TestSentenceGeneratorMultipleTemplates:
    """Test multiple template variations."""

    def test_multiple_templates(self):
        """Test with multiple template variations."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        gen.set_values("USER", ["Alice"])
        result = gen.generate(seed=42)
        assert result in ["Alice won", "Alice lost"]

    def test_add_template(self):
        """Test adding templates dynamically."""
        gen = SentenceGenerator("{USER} won")
        gen.add_template("{USER} lost")
        assert len(gen.templates) == 2

    def test_remove_template(self):
        """Test removing templates."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        gen.remove_template(0)
        assert len(gen.templates) == 1
        assert gen.templates[0] == "{USER} lost"

    def test_clear_templates(self):
        """Test clearing all templates."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        gen.clear_templates()
        assert len(gen.templates) == 0
        assert gen.placeholders == []


class TestInlineAlternatives:
    """Test inline alternatives feature."""

    def test_simple_alternatives(self):
        """Test simple inline alternatives."""
        gen = SentenceGenerator("{USER} {killed|eliminated} {TARGET}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("TARGET", ["Bob"])
        result = gen.generate(seed=42)
        assert result in ["Alice killed Bob", "Alice eliminated Bob"]

    def test_weighted_alternatives(self):
        """Test weighted inline alternatives."""
        gen = SentenceGenerator("{USER} {killed:3|eliminated:1} {TARGET}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("TARGET", ["Bob"])
        # With seed, should be deterministic
        results = [gen.generate(seed=i) for i in range(10)]
        # "killed" has 3x weight, should appear more often
        killed_count = sum(1 for r in results if "killed" in r)
        assert killed_count > 3  # Should be roughly 75%

    def test_multiple_alternatives_in_template(self):
        """Test multiple inline alternatives in one template."""
        gen = SentenceGenerator("{USER} {killed|eliminated} {TARGET} {quietly|silently}")
        gen.set_values("USER", ["Alice"])
        gen.set_values("TARGET", ["Bob"])
        result = gen.generate()
        # Should contain one word from each alternative
        assert any(word in result for word in ["killed", "eliminated"])
        assert any(word in result for word in ["quietly", "silently"])


class TestTransforms:
    """Test transform functions."""

    def test_upper_transform(self):
        """Test uppercase transform."""
        gen = SentenceGenerator("{USER|upper}")
        gen.set_values("USER", ["alice"])
        assert gen.generate() == "ALICE"

    def test_lower_transform(self):
        """Test lowercase transform."""
        gen = SentenceGenerator("{USER|lower}")
        gen.set_values("USER", ["ALICE"])
        assert gen.generate() == "alice"

    def test_title_transform(self):
        """Test title case transform."""
        gen = SentenceGenerator("{USER|title}")
        gen.set_values("USER", ["alice smith"])
        assert gen.generate() == "Alice Smith"

    def test_capitalize_transform(self):
        """Test capitalize transform."""
        gen = SentenceGenerator("{USER|capitalize}")
        gen.set_values("USER", ["alice smith"])
        assert gen.generate() == "Alice smith"

    def test_truncate_transform(self):
        """Test truncate transform."""
        gen = SentenceGenerator("{USER|truncate:5}")
        gen.set_values("USER", ["Alexander"])
        assert gen.generate() == "Alexa"

    def test_default_transform(self):
        """Test default transform for empty values."""
        gen = SentenceGenerator("Hello {USER|default:Guest}")
        gen.set_values("USER", [""])
        assert gen.generate() == "Hello Guest"

    def test_a_transform_vowel(self):
        """Test 'a' transform with vowel start."""
        gen = SentenceGenerator("I saw {USER|a}")
        gen.set_values("USER", ["elephant"])
        assert gen.generate() == "I saw an elephant"

    def test_a_transform_consonant(self):
        """Test 'a' transform with consonant start."""
        gen = SentenceGenerator("I saw {USER|a}")
        gen.set_values("USER", ["cat"])
        assert gen.generate() == "I saw a cat"

    def test_plural_transform_regular(self):
        """Test plural transform on regular noun."""
        gen = SentenceGenerator("I have {NUM} {ITEM|plural}")
        gen.set_values("NUM", ["many"])
        gen.set_values("ITEM", ["cat"])
        assert gen.generate() == "I have many cats"

    def test_plural_transform_es(self):
        """Test plural transform on words ending in -s, -sh, -ch, -x, -z."""
        gen = SentenceGenerator("Multiple {ITEM|plural}")
        gen.set_values("ITEM", ["box"])
        assert gen.generate() == "Multiple boxes"

    def test_plural_transform_ies(self):
        """Test plural transform on words ending in consonant+y."""
        gen = SentenceGenerator("Multiple {ITEM|plural}")
        gen.set_values("ITEM", ["city"])
        assert gen.generate() == "Multiple cities"

    def test_pluralize_custom_suffix(self):
        """Test pluralize with custom suffix."""
        gen = SentenceGenerator("{ITEM|pluralize:es}")
        gen.set_values("ITEM", ["bus"])
        assert gen.generate() == "buses"


class TestGenerateAll:
    """Test generate_all functionality."""

    def test_generate_all_combinations(self):
        """Test generating all combinations."""
        gen = SentenceGenerator("{USER} is {STATUS}")
        gen.set_values("USER", ["Alice", "Bob"])
        gen.set_values("STATUS", ["happy", "sad"])
        results = gen.generate_all()
        assert len(results) == 4
        assert "Alice is happy" in results
        assert "Alice is sad" in results
        assert "Bob is happy" in results
        assert "Bob is sad" in results

    def test_generate_all_with_inline_alternatives(self):
        """Test generate_all with inline alternatives."""
        gen = SentenceGenerator("{USER} {won|lost}")
        gen.set_values("USER", ["Alice"])
        results = gen.generate_all()
        assert len(results) == 2
        assert "Alice won" in results
        assert "Alice lost" in results


class TestGenerateMultiple:
    """Test generate_multiple functionality."""

    def test_generate_multiple(self):
        """Test generating multiple sentences."""
        gen = SentenceGenerator("{USER} is here")
        gen.set_values("USER", ["Alice", "Bob", "Charlie"])
        results = gen.generate_multiple(5, seed=42)
        assert len(results) == 5
        assert all(r.endswith(" is here") for r in results)

    def test_generate_multiple_reproducibility(self):
        """Test that seed produces reproducible results."""
        gen = SentenceGenerator("{USER} won")
        gen.set_values("USER", ["Alice", "Bob", "Charlie"])
        results1 = gen.generate_multiple(3, seed=123)
        results2 = gen.generate_multiple(3, seed=123)
        assert results1 == results2


class TestDefaults:
    """Test default values functionality."""

    def test_default_values(self):
        """Test using default values."""
        gen = SentenceGenerator("{USER} is {STATUS}", default_values={"STATUS": "unknown"})
        gen.set_values("USER", ["Alice"])
        assert "Alice is unknown" in gen.generate()

    def test_default_overridden(self):
        """Test that set values override defaults."""
        gen = SentenceGenerator("{USER} is {STATUS}", default_values={"STATUS": "unknown"})
        gen.set_values("USER", ["Alice"])
        gen.set_values("STATUS", ["happy"])
        assert gen.generate() == "Alice is happy"

    def test_use_defaults_false(self):
        """Test that use_defaults=False raises error for missing values."""
        gen = SentenceGenerator("{USER} is {STATUS}", default_values={"STATUS": "unknown"})
        gen.set_values("USER", ["Alice"])
        with pytest.raises(ValueError, match="No values set for placeholder 'STATUS'"):
            gen.generate(use_defaults=False)


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_placeholder(self):
        """Test error when setting values for non-existent placeholder."""
        gen = SentenceGenerator("{USER} is here")
        with pytest.raises(ValueError, match="Placeholder 'INVALID' not found"):
            gen.set_values("INVALID", ["value"])

    def test_empty_values(self):
        """Test error when setting empty values list."""
        gen = SentenceGenerator("{USER} is here")
        with pytest.raises(ValueError, match="cannot be empty"):
            gen.set_values("USER", [])

    def test_missing_values_no_defaults(self):
        """Test error when placeholder has no values and no defaults."""
        gen = SentenceGenerator("{USER} is here")
        with pytest.raises(ValueError, match="No values set for placeholder 'USER'"):
            gen.generate(use_defaults=False)


class TestFileLoading:
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
                assert values == ["Alice", "Bob"]
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
                assert values == ["Alice", "Bob"]
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
                assert values == ["Alice", "Bob", "Charlie"]
            finally:
                os.unlink(f.name)

    def test_load_from_unsupported_format(self):
        """Test error when loading from unsupported format."""
        gen = SentenceGenerator("{USER} is here")
        with pytest.raises(ValueError, match="Unsupported file format"):
            gen.load_values_from_file("data.txt")


class TestCaching:
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
        assert gen._expanded_templates_cache is cache_after_first

    def test_cache_invalidated_on_add_template(self):
        """Test that cache is invalidated when adding templates."""
        gen = SentenceGenerator("{USER} won")
        gen.set_values("USER", ["Alice"])
        gen.generate()
        assert gen._expanded_templates_cache is not None
        gen.add_template("{USER} lost")
        assert gen._expanded_templates_cache is None

    def test_cache_invalidated_on_remove_template(self):
        """Test that cache is invalidated when removing templates."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        gen.set_values("USER", ["Alice"])
        gen.generate()
        assert gen._expanded_templates_cache is not None
        gen.remove_template(0)
        assert gen._expanded_templates_cache is None


class TestUtilityMethods:
    """Test utility methods."""

    def test_has_placeholder_true(self):
        """Test has_placeholder returns True for existing placeholder."""
        gen = SentenceGenerator("{USER} is here")
        assert gen.has_placeholder("USER") is True

    def test_has_placeholder_false(self):
        """Test has_placeholder returns False for non-existing placeholder."""
        gen = SentenceGenerator("{USER} is here")
        assert gen.has_placeholder("INVALID") is False

    def test_get_values(self):
        """Test getting values for a placeholder."""
        gen = SentenceGenerator("{USER} is here")
        gen.set_values("USER", ["Alice", "Bob"])
        assert gen.get_values("USER") == ["Alice", "Bob"]

    def test_get_values_not_set(self):
        """Test getting values when not set returns None."""
        gen = SentenceGenerator("{USER} is here")
        assert gen.get_values("USER") is None

    def test_clear_values(self):
        """Test clearing all values."""
        gen = SentenceGenerator("{USER} is here")
        gen.set_values("USER", ["Alice"])
        gen.clear_values()
        assert gen.get_values("USER") is None

    def test_get_template(self):
        """Test getting template at index."""
        gen = SentenceGenerator(["{USER} won", "{USER} lost"])
        assert gen.get_template(0) == "{USER} won"
        assert gen.get_template(1) == "{USER} lost"

    def test_get_template_invalid_index(self):
        """Test getting template at invalid index."""
        gen = SentenceGenerator("{USER} won")
        with pytest.raises(IndexError):
            gen.get_template(5)

    def test_repr(self):
        """Test string representation."""
        gen = SentenceGenerator("{USER} is {STATUS}")
        repr_str = repr(gen)
        assert "SentenceGenerator" in repr_str
        assert "placeholders=" in repr_str


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_template(self):
        """Test empty template."""
        gen = SentenceGenerator("")
        assert gen.generate() == ""

    def test_placeholder_with_numbers(self):
        """Test placeholder with numbers in name."""
        gen = SentenceGenerator("{USER1} and {USER2}")
        gen.set_values("USER1", ["Alice"])
        gen.set_values("USER2", ["Bob"])
        assert gen.generate() == "Alice and Bob"

    def test_braces_in_value(self):
        """Test values containing braces."""
        gen = SentenceGenerator("{USER}")
        gen.set_values("USER", ["test{value}"])
        # Should not be interpreted as placeholder
        assert gen.generate() == "test{value}"

    def test_whitespace_in_template(self):
        """Test template with extra whitespace."""
        gen = SentenceGenerator("  {USER}  is  {STATUS}  ")
        gen.set_values("USER", ["Alice"])
        gen.set_values("STATUS", ["happy"])
        result = gen.generate()
        assert "Alice" in result
        assert "happy" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
