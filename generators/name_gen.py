#!/usr/bin/env python3
"""
Fantasy Name Generator v2.0

Generate fantasy names with cultural/racial variants.
Supports 16 cultures including Elvish, Dwarvish, Human, Orcish, Celtic, Norse, Arabic, Japanese, Chinese, Egyptian, and more.

Features:
- 16 cultural naming styles
- Name meanings/etymology
- Dynasty/house name generation
- Gender-specific naming patterns
- Batch export (JSON, CSV)
"""

import random
import json
import csv
from typing import List, Optional, Dict, Tuple
from pathlib import Path


class NameGenerator:
    """Generate fantasy names with cultural variants."""

    # Syllable patterns for different cultures
    CULTURES = {
        "elvish": {
            "prefixes": ["ael", "thel", "syl", "fae", "lir", "gal", "el", "fin", "aran", "celeb"],
            "middles": ["an", "en", "in", "on", "th", "l", "r", "ss", "dr", "vr"],
            "suffixes": ["a", "e", "iel", "ion", "as", "is", "wen", "wyn", "thien", "riel"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "dwarvish": {
            "prefixes": ["dur", "thor", "grim", "iron", "stone", "bron", "thrain", "gim", "forg", "gran"],
            "middles": ["in", "ar", "or", "ur", "ek", "ak", "din", "gar", "thor", "brand"],
            "suffixes": ["in", "ar", "or", "ek", "ak", "din", "gar", "thor", "brand", "hammer"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "human": {
            "prefixes": ["ar", "bal", "car", "dar", "fal", "gar", "hal", "jar", "kal", "lar"],
            "middles": ["an", "en", "in", "on", "or", "al", "el", "il", "ol", "ul"],
            "suffixes": ["a", "us", "or", "an", "en", "is", "os", "as", "im", "em"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "orcish": {
            "prefixes": ["grom", "thrak", "dush", "mog", "nar", "shar", "urz", "grak", "thok", "draz"],
            "middles": ["g", "k", "th", "z", "r", "gr", "kr", "dr", "thr", "gar"],
            "suffixes": ["a", "uk", "ak", "ish", "oth", "ar", "or", "um", "ash", "th"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "halfling": {
            "prefixes": ["bil", "mer", "per", "ros", "sam", "wil", "fol", "pip", "ros", "tan"],
            "middles": ["bo", "ri", "di", "li", "ni", "wi", "fi", "ti", "go", "ho"],
            "suffixes": ["o", "a", "y", "ie", "ie", "er", "in", "et", "it", "us"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "draconic": {
            "prefixes": ["arth", "bal", "cry", "drac", "ember", "fyr", "ign", "pyr", "serp", "vex"],
            "middles": ["ax", "ex", "ix", "ox", "ux", "ath", "eth", "ith", "oth", "uth"],
            "suffixes": ["ion", "us", "a", "is", "os", "ax", "ex", "ix", "ar", "or"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "celestial": {
            "prefixes": ["ael", "lum", "sol", "cel", "aur", "ser", "gal", "eth", "ion", "val"],
            "middles": ["an", "en", "in", "on", "ar", "el", "il", "ol", "ul", "or"],
            "suffixes": ["a", "e", "iel", "ion", "us", "is", "iel", "iel", "th", "ra"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "fiendish": {
            "prefixes": ["mal", "dar", "vex", "zor", "krad", "mor", "thar", "bal", "naz", "groth"],
            "middles": ["g", "k", "th", "z", "r", "gr", "kr", "dr", "thr", "gar"],
            "suffixes": ["a", "us", "oth", "ax", "ex", "is", "os", "ar", "or", "th"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "gnomish": {
            "prefixes": ["bim", "fin", "gim", "kil", "lim", "nim", "pim", "rim", "sim", "tim"],
            "middles": ["ble", "cle", "dle", "fle", "gle", "kle", "ple", "tle", "zle", "wix"],
            "suffixes": ["o", "a", "y", "ie", "ix", "it", "et", "in", "ik", "ip"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        # NEW v2.0 Cultures
        "celtic": {
            "prefixes": ["brigh", "cael", "donn", "eoin", "fionn", "gwen", "iar", "kelly", "liam", "morg"],
            "middles": ["an", "ach", "en", "in", "oc", "an", "wen", "ryn", "lan", "dar"],
            "suffixes": ["a", "ach", "een", "an", "in", "oc", "us", "wyn", "rie", "gan"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "norse": {
            "prefixes": ["agnar", "bjorn", "erik", "frey", "gund", "haldor", "ivar", "jorund", "ketil", "leif"],
            "middles": ["ar", "biorn", "fin", "grim", "har", "if", "ket", "mund", "rad", "stein"],
            "suffixes": ["ar", "born", "frid", "gar", "hild", "if", "mar", "olf", "rand", "ulf"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "arabic": {
            "prefixes": ["abd", "ahm", "ali", "far", "hab", "jas", "kam", "mah", "nas", "omar"],
            "middles": ["al", "ar", "az", "el", "im", "ir", "ul", "ur", "ad", "id"],
            "suffixes": ["ad", "al", "an", "ar", "at", "ee", "id", "im", "ul", "us"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "japanese": {
            "prefixes": ["aki", "dai", "emi", "haru", "ichi", "jiro", "ka", "maki", "nao", "rei"],
            "middles": ["bu", "chi", "di", "fu", "gi", "hi", "ji", "ki", "mi", "ni"],
            "suffixes": ["bi", "chi", "di", "ko", "mi", "mu", "na", "ro", "shi", "ta"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "chinese": {
            "prefixes": ["chen", "fang", "gui", "hong", "jian", "kai", "ling", "mei", "ping", "qing"],
            "middles": ["an", "ang", "en", "eng", "in", "ing", "on", "ong", "un", "uan"],
            "suffixes": ["an", "ang", "ei", "en", "i", "in", "ng", "u", "ua", "wei"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        },
        "egyptian": {
            "prefixes": ["akh", "ben", "djed", "heq", "ibu", "ka", "men", "neb", "pet", "ra"],
            "middles": ["am", "an", "en", "is", "it", "em", "um", "ut", "ar", "ur"],
            "suffixes": ["amun", "emhet", "hotep", "iset", "ka", "mes", "nefer", "ra", "set", "tawi"],
            "structure": ["prefix+suffix", "prefix+middle+suffix"]
        }
    }

    # Name meanings by culture and name component
    NAME_MEANINGS = {
        "elvish": {
            "ael": "star", "thel": "light", "syl": "forest", "fae": "fair", "lir": "sea",
            "wen": "maiden", "wyn": "blessed", "riel": "daughter", "ion": "son"
        },
        "dwarvish": {
            "dur": "stone", "thor": "thunder", "grim": "fierce", "iron": "iron", "stone": "rock",
            "in": "descendant", "gar": "spear", "brand": "sword", "din": "warrior"
        },
        "norse": {
            "agnar": "edge warrior", "bjorn": "bear", "erik": "eternal ruler", "frey": "lord",
            "gund": "war", "haldor": "thor's protection", "ivar": "yew warrior", "leif": "heir",
            "ulf": "wolf", "rand": "shield", "hild": "battle"
        },
        "celtic": {
            "brigh": "strength", "cael": "slender", "donn": "brown", "fionn": "fair", "gwen": "white",
            "morg": "sea", "wyn": "blessed", "rie": "queen"
        },
        "arabic": {
            "abd": "servant", "ahm": "praised", "ali": "exalted", "far": "victory",
            "jas": "bringer of good", "kam": "generous", "mah": "protected", "nas": "victorious"
        },
        "japanese": {
            "aki": "bright", "dai": "great", "emi": "blessing", "haru": "spring",
            "ichi": "first", "ka": "fragrance", "nao": "honest", "rei": "lovely"
        },
        "chinese": {
            "chen": "morning", "fang": "fragrant", "hong": "red", "jian": "strong",
            "kai": "triumphant", "ling": "delicate", "mei": "beautiful", "qing": "clear"
        },
        "egyptian": {
            "akh": "spirit", "djed": "enduring", "heq": "ruler", "ka": "soul",
            "men": "enduring", "neb": "lord", "ra": "sun", "hotep": "peace", "nefer": "beautiful"
        }
    }

    # Dynasty/House name patterns
    DYNASTY_PATTERNS = {
        "elvish": ["{prefix}an", "{prefix}thien", "House of {name}", "{name}wood"],
        "dwarvish": ["{prefix}hold", "{prefix}forge", "Iron{suffix}", "{name}beard"],
        "human": ["House {name}", "{name}field", "{name}worth", "{name}ton"],
        "norse": ["{name}sson", "{name}dottir", "{name}gaard", "{name}vik"],
        "celtic": ["O'{name}", "Mac{name}", "{name}wyn", "House of {name}"],
        "arabic": ["al-{name}", "bin {name}", "{name}i", "House of {name}"],
        "japanese": ["{name}-clan", "{name} family", "House {name}"],
        "chinese": ["{name} family", "House of {name}", "{name} clan"],
        "egyptian": ["House of {name}", "{name}hotep", "{name}ra", "{name}nefer"],
        "default": ["House {name}", "{name} family", "The {name}s"]
    }

    # Title patterns
    TITLES = {
        "warrior": ["the Bold", "the Brave", "the Mighty", "the Fierce", "the Unyielding"],
        "mage": ["the Wise", "the Learned", "the Arcane", "the Mystical", "the Enchanted"],
        "rogue": ["the Silent", "the Swift", "the Shadow", "the Cunning", "the Invisible"],
        "cleric": ["the Devout", "the Holy", "the Blessed", "the Righteous", "the Pious"],
        "noble": ["the Noble", "the Just", "the Fair", "the Regal", "the Majestic"],
        "outlaw": ["the Wicked", "the Cruel", "the Ruthless", "the Damned", "the Forsaken"]
    }

    def __init__(self, culture: str = "human", seed: Optional[int] = None):
        """
        Initialize the name generator.

        Args:
            culture: The cultural style (elvish, dwarvish, human, orcish, etc.)
            seed: Optional random seed for reproducibility
        """
        self.culture = culture.lower()
        if seed is not None:
            random.seed(seed)

    def generate_name(self, gender: Optional[str] = None, length: str = "medium") -> str:
        """
        Generate a single name.

        Args:
            gender: Optional gender hint (some cultures have gendered endings)
            length: Name length preference ("short", "medium", "long")

        Returns:
            Generated name
        """
        if self.culture not in self.CULTURES:
            self.culture = "human"

        culture_data = self.CULTURES[self.culture]
        structure = random.choice(culture_data["structure"])

        if length == "short":
            structure = "prefix+suffix"
        elif length == "long":
            structure = "prefix+middle+suffix"

        name = ""
        parts = structure.split("+")

        for part in parts:
            if part == "prefix":
                name += random.choice(culture_data["prefixes"])
            elif part == "middle":
                name += random.choice(culture_data["middles"])
            elif part == "suffix":
                suffix = random.choice(culture_data["suffixes"])
                # Apply gender hints if applicable
                if gender and gender.lower() == "female":
                    if suffix in ["us", "or", "os"]:
                        suffix = suffix.replace("us", "a").replace("or", "a").replace("os", "a")
                name += suffix

        # Capitalize first letter
        return name.capitalize()

    def get_name_meaning(self, name: str) -> Optional[str]:
        """
        Get the meaning/etymology of a name component.

        Args:
            name: Name or name component to look up

        Returns:
            Meaning string or None if not found
        """
        name_lower = name.lower()
        culture_meanings = self.NAME_MEANINGS.get(self.culture, {})

        # Try exact match first
        if name_lower in culture_meanings:
            return culture_meanings[name_lower]

        # Try partial matches
        for component, meaning in culture_meanings.items():
            if component in name_lower or name_lower in component:
                return meaning

        return None

    def generate_name_with_meaning(self, gender: Optional[str] = None,
                                    length: str = "medium") -> Tuple[str, str]:
        """
        Generate a name with its meaning.

        Args:
            gender: Optional gender hint
            length: Name length preference

        Returns:
            Tuple of (name, meaning)
        """
        name = self.generate_name(gender, length)
        meaning = self.get_name_meaning(name)

        if not meaning:
            # Generate meaning from components
            culture_data = self.CULTURES.get(self.culture, {})
            prefixes = culture_data.get("prefixes", [])
            suffixes = culture_data.get("suffixes", [])

            meaning_parts = []
            name_lower = name.lower()

            for prefix in prefixes:
                if name_lower.startswith(prefix):
                    if prefix in self.NAME_MEANINGS.get(self.culture, {}):
                        meaning_parts.append(self.NAME_MEANINGS[self.culture][prefix])
                    break

            for suffix in suffixes:
                if name_lower.endswith(suffix):
                    if suffix in self.NAME_MEANINGS.get(self.culture, {}):
                        meaning_parts.append(self.NAME_MEANINGS[self.culture][suffix])
                    break

            meaning = " and ".join(meaning_parts) if meaning_parts else "unknown origin"

        return name, meaning

    def generate_dynasty_name(self, base_name: Optional[str] = None) -> str:
        """
        Generate a dynasty/house name.

        Args:
            base_name: Optional base name to use (generates one if None)

        Returns:
            Dynasty/house name
        """
        if not base_name:
            base_name = self.generate_name()

        patterns = self.DYNASTY_PATTERNS.get(self.culture, self.DYNASTY_PATTERNS["default"])
        pattern = random.choice(patterns)

        # Get a prefix/suffix for pattern substitution
        culture_data = self.CULTURES.get(self.culture, {})
        prefix = random.choice(culture_data.get("prefixes", [""]))
        suffix = random.choice(culture_data.get("suffixes", [""]))

        return pattern.format(name=base_name, prefix=prefix, suffix=suffix)

    def generate_full_name(self, gender: Optional[str] = None, include_title: bool = False,
                           title_class: Optional[str] = None, include_dynasty: bool = False) -> str:
        """
        Generate a full name with optional title and dynasty.

        Args:
            gender: Optional gender hint
            include_title: Whether to include a title
            title_class: Specific title class (warrior, mage, rogue, etc.)
            include_dynasty: Whether to include dynasty/house name

        Returns:
            Full name with optional title and dynasty
        """
        # Generate first name
        first_name = self.generate_name(gender, "medium")

        # Generate last name (shorter structure)
        last_name = self.generate_name(gender, "short")

        full_name = f"{first_name} {last_name}"

        if include_dynasty:
            dynasty = self.generate_dynasty_name(first_name)
            full_name = f"{first_name} of {dynasty}"

        if include_title:
            if title_class and title_class in self.TITLES:
                title = random.choice(self.TITLES[title_class])
            else:
                all_titles = [t for titles in self.TITLES.values() for t in titles]
                title = random.choice(all_titles)
            full_name = f"{full_name} {title}"

        return full_name

    def export_to_json(self, names: List[str], filepath: str,
                       include_meanings: bool = False) -> None:
        """
        Export names to JSON file.

        Args:
            names: List of names to export
            filepath: Output file path
            include_meanings: Whether to include name meanings
        """
        if include_meanings:
            data = []
            for name in names:
                meaning = self.get_name_meaning(name)
                data.append({"name": name, "meaning": meaning or "unknown"})
        else:
            data = {"names": names, "culture": self.culture}

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def export_to_csv(self, names: List[str], filepath: str,
                      include_meanings: bool = False) -> None:
        """
        Export names to CSV file.

        Args:
            names: List of names to export
            filepath: Output file path
            include_meanings: Whether to include name meanings
        """
        with open(filepath, 'w', newline='') as f:
            if include_meanings:
                writer = csv.writer(f)
                writer.writerow(['Name', 'Meaning', 'Culture'])
                for name in names:
                    meaning = self.get_name_meaning(name) or "unknown"
                    writer.writerow([name, meaning, self.culture])
            else:
                writer = csv.writer(f)
                writer.writerow(['Name', 'Culture'])
                for name in names:
                    writer.writerow([name, self.culture])

    def generate_multiple(self, count: int, gender: Optional[str] = None,
                          include_title: bool = False) -> List[str]:
        """
        Generate multiple unique names.

        Args:
            count: Number of names to generate
            gender: Optional gender hint
            include_title: Whether to include titles

        Returns:
            List of unique names
        """
        names = set()
        attempts = 0
        max_attempts = count * 10

        while len(names) < count and attempts < max_attempts:
            if include_title:
                name = self.generate_full_name(gender, include_title=True)
            else:
                name = self.generate_name(gender)
            names.add(name)
            attempts += 1

        return list(names)[:count]

    def generate_party_names(self, party_size: int = 4) -> Dict[str, str]:
        """
        Generate names for a typical adventuring party.

        Args:
            party_size: Number of party members

        Returns:
            Dict mapping character concepts to names
        """
        cultures = ["human", "elvish", "dwarvish", "halfling", "orcish"]
        roles = ["warrior", "mage", "rogue", "cleric", "ranger"]

        names = {}
        for i in range(party_size):
            culture = cultures[i % len(cultures)]
            role = roles[i % len(roles)]
            generator = NameGenerator(culture=culture)
            name = generator.generate_full_name(include_title=True, title_class=role)
            names[f"{culture.capitalize()} {role.capitalize()}"] = name

        return names

    @classmethod
    def list_cultures(cls) -> List[str]:
        """Return list of available cultures."""
        return list(cls.CULTURES.keys())

    @classmethod
    def list_title_classes(cls) -> List[str]:
        """Return list of available title classes."""
        return list(cls.TITLES.keys())


def main():
    """CLI for the fantasy name generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fantasy Name Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python name_gen.py -c elvish -n 5
  python name_gen.py -c dwarvish --title --class warrior
  python name_gen.py --party
  python name_gen.py -c human -f female -n 10
        """
    )

    parser.add_argument("-c", "--culture", default="human",
                        help="Cultural style (elvish, dwarvish, human, orcish, etc.)")
    parser.add_argument("-n", "--count", type=int, default=5,
                        help="Number of names to generate")
    parser.add_argument("-f", "--female", action="store_true",
                        help="Generate female-leaning names")
    parser.add_argument("-m", "--male", action="store_true",
                        help="Generate male-leaning names")
    parser.add_argument("--title", action="store_true",
                        help="Include titles")
    parser.add_argument("--class", dest="title_class",
                        help="Specific title class (warrior, mage, rogue, etc.)")
    parser.add_argument("--party", action="store_true",
                        help="Generate a party of adventurers")
    parser.add_argument("--seed", type=int,
                        help="Random seed for reproducibility")
    parser.add_argument("--list-cultures", action="store_true",
                        help="List available cultures")

    args = parser.parse_args()

    if args.list_cultures:
        print("Available cultures:", ", ".join(NameGenerator.list_cultures()))
        print("Available title classes:", ", ".join(NameGenerator.list_title_classes()))
        return

    gender = None
    if args.female:
        gender = "female"
    elif args.male:
        gender = "male"

    generator = NameGenerator(culture=args.culture, seed=args.seed)

    if args.party:
        print("=== Adventuring Party ===\n")
        party = generator.generate_party_names()
        for role, name in party.items():
            print(f"  {role}: {name}")
    elif args.title:
        print(f"=== {args.culture.capitalize()} Names with Titles ===\n")
        names = generator.generate_multiple(args.count, gender=gender, include_title=True)
        for name in names:
            print(f"  {name}")
    else:
        print(f"=== {args.culture.capitalize()} Names ===\n")
        names = generator.generate_multiple(args.count, gender=gender)
        for name in names:
            print(f"  {name}")


if __name__ == "__main__":
    main()
