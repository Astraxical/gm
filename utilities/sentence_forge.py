#!/usr/bin/env python3
"""
Template-based Sentence Generator

Generate sentences by filling in placeholders in a template.
Supports multiple template variations and inline word alternatives.

Features:
- Placeholders: {USER}, {TARGET}, etc.
- Inline alternatives: {killed|eliminated|took out}
- Weighted alternatives: {killed:3|eliminated:1}
- Transforms: {USER|upper}, {ITEM|plural}, {ANIMAL|a}
- Conditionals: {if:PLACEHOLDER:value:then|else}
- Nested placeholders: {{PREFIX}_{NAME}}
"""

import re
import random
import itertools
import csv
import json
from typing import Dict, List, Optional, Any

# Regex patterns (defined once for DRY compliance)
PLACEHOLDER_PATTERN = re.compile(r'\{([A-Z][A-Z0-9_]*)\}')
# Inline alternatives: lowercase start, but NOT 'if:' which is for conditionals
INLINE_ALTERNATIVE_PATTERN = re.compile(r'\{((?!if:)[a-z][a-zA-Z0-9 :]*(?:\|[a-zA-Z][a-zA-Z0-9 :]*)*)\}')
# Transform pattern: supports transforms with underscores like verb_s, verb_ing
TRANSFORM_PATTERN = re.compile(r'\{([A-Z][A-Z0-9_]*)(\|[a-z_]+(?:[^}]*)?)?\}')
CONDITIONAL_PATTERN = re.compile(r'\{if:([A-Z][A-Z0-9_]*):')  # Extracts placeholder from {if:PLACEHOLDER:...}


class SentenceGenerator:
    """Generate sentences from templates with placeholders."""

    @staticmethod
    def _extract_placeholders_from_template(template: str) -> List[str]:
        """Extract placeholder names from a single template."""
        # Use TRANSFORM_PATTERN to support placeholders with transforms like {USER|upper}
        matches = TRANSFORM_PATTERN.findall(template)
        # Return just the placeholder names (first element of each tuple)
        placeholders = [m[0] for m in matches]

        # Also extract placeholders from conditionals {if:PLACEHOLDER:...}
        conditional_matches = CONDITIONAL_PATTERN.findall(template)
        placeholders.extend(conditional_matches)

        # Extract placeholders from math expressions {LEVEL+2}, {DAMAGE*10}
        math_pattern = re.compile(r'\{([A-Z][A-Z0-9_]*)[\+\-\*\/\%]')
        math_matches = math_pattern.findall(template)
        placeholders.extend(math_matches)

        # Extract placeholders from loops {repeat:COUNT:...}
        loop_pattern = re.compile(r'\{repeat:([A-Z][A-Z0-9_]*):')
        loop_matches = loop_pattern.findall(template)
        placeholders.extend(loop_matches)

        # Extract placeholders from comparison conditionals {if:LEVEL>5:...}
        comparison_pattern = re.compile(r'\{if:([A-Z][A-Z0-9_]*)[><=!]+')
        comparison_matches = comparison_pattern.findall(template)
        placeholders.extend(comparison_matches)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(placeholders))

    @staticmethod
    def _fill_single_placeholder(text: str, placeholder: str, value: str) -> str:
        """Replace a single placeholder with a value."""
        return text.replace(f'{{{placeholder}}}', value, 1)

    @staticmethod
    def _parse_transform_args(transform_str: str) -> tuple[str, Optional[str]]:
        """
        Parse transform string like 'upper' or 'truncate:50'.

        Returns:
            Tuple of (transform_name, argument)
        """
        if ':' in transform_str:
            parts = transform_str.split(':', 1)
            return parts[0], parts[1]
        return transform_str, None

    def __init__(self, template: str | List[str], default_values: Optional[Dict[str, str]] = None):
        """
        Initialize with a template string or list of template variations.

        Placeholders are denoted by curly braces: {PLACEHOLDER}
        Inline alternatives use pipe: {killed|eliminated|took out}
        Transforms: {USER|upper}, {ITEM|plural}, {ANIMAL|a}

        Args:
            template: Template string or list of template variations
            default_values: Optional dict of default values for missing placeholders

        Examples:
            >>> gen = SentenceGenerator("{USER} is {STATUS}")
            >>> gen.set_values("USER", ["Alice", "Bob"])
            >>> gen.set_values("STATUS", ["happy"])
            >>> gen.generate(seed=42)
            'Alice is happy'

            >>> gen = SentenceGenerator("{ITEM|plural}", default_values={"ITEM": "cat"})
            >>> gen.generate()
            'cats'

            >>> gen = SentenceGenerator(["{USER} won", "{USER} lost"])
            >>> gen.template_count
            2
        """
        if isinstance(template, list):
            self.templates = template
        else:
            self.templates = [template]

        self.values: Dict[str, List[str]] = {}
        self.default_values: Dict[str, str] = default_values or {}
        self._placeholders = self._extract_placeholders()
        self._expanded_templates_cache: Optional[List[str]] = None
        self._templates_hash: int = hash(tuple(self.templates))

    def _extract_placeholders(self) -> List[str]:
        """Extract unique placeholder names from all templates."""
        all_placeholders = []
        for template in self.templates:
            all_placeholders.extend(self._extract_placeholders_from_template(template))
        # Preserve order, remove duplicates
        return list(dict.fromkeys(all_placeholders))

    def _parse_alternative_options(self, options_str: str) -> List[str]:
        """
        Parse alternatives string, expanding weighted options.

        Supports syntax: {option:weight|option:weight}
        Weight defaults to 1 if not specified.

        Example: "killed:3|eliminated:1" -> ["killed", "killed", "killed", "eliminated"]
        """
        result: List[str] = []
        for opt in options_str.split('|'):
            opt = opt.strip()
            if ':' in opt:
                # Weighted option: "option:weight"
                parts = opt.rsplit(':', 1)
                option = parts[0].strip()
                try:
                    weight = int(parts[1].strip())
                except ValueError:
                    weight = 1
                result.extend([option] * max(1, weight))
            else:
                result.append(opt)
        return result

    def _expand_inline_alternatives(self, template: str) -> List[str]:
        """
        Expand inline alternatives like {killed|eliminated} into multiple templates.

        Supports weighted alternatives: {killed:3|eliminated:1}
        Higher weight = more likely to be chosen (expands to more templates).

        Example: "{A} {killed|eliminated} {B}" -> ["{A} killed {B}", "{A} eliminated {B}"]
        Example: "{A} {killed:2|eliminated:1} {B}" -> ["{A} killed {B}", "{A} killed {B}", "{A} eliminated {B}"]
        """
        matches = list(INLINE_ALTERNATIVE_PATTERN.finditer(template))
        if not matches:
            return [template]

        # Build all combinations of alternatives (with weights expanded)
        all_options = [self._parse_alternative_options(m.group(1)) for m in matches]

        results = []
        for combination in itertools.product(*all_options):
            result = template
            # Replace each {a|b|c} with the chosen option
            for match, choice in zip(matches, combination):
                result = result.replace(match.group(0), choice, 1)
            results.append(result)

        return results

    @property
    def placeholders(self) -> List[str]:
        """Return list of placeholders found in all templates."""
        return self._placeholders.copy()

    @property
    def template_count(self) -> int:
        """Return number of template variations (after expanding inline alternatives)."""
        return len(self._get_all_expanded_templates())

    def set_values(self, placeholder: str, values: List[str]) -> 'SentenceGenerator':
        """
        Set possible values for a placeholder.

        Args:
            placeholder: The placeholder name (without braces)
            values: List of possible values to choose from

        Returns:
            self for method chaining

        Raises:
            ValueError: If placeholder not found or values list is empty

        Example:
            >>> gen = SentenceGenerator("{USER} is here")
            >>> gen.set_values("USER", ["Alice", "Bob"])
            >>> gen.get_values("USER")
            ['Alice', 'Bob']
        """
        if placeholder not in self._placeholders:
            raise ValueError(
                f"Placeholder '{placeholder}' not found in templates. "
                f"Available: {', '.join(self._placeholders) if self._placeholders else 'none'}"
            )
        if not values:
            raise ValueError(f"Values list for '{placeholder}' cannot be empty")
        self.values[placeholder] = values
        return self

    def set_value(self, placeholder: str, value: str) -> 'SentenceGenerator':
        """
        Set a single value for a placeholder.

        Args:
            placeholder: The placeholder name (without braces)
            value: The value to use

        Returns:
            self for method chaining
        """
        return self.set_values(placeholder, [value])

    def has_placeholder(self, placeholder: str) -> bool:
        """
        Check if a placeholder exists in the templates.

        Args:
            placeholder: The placeholder name (without braces)

        Returns:
            True if placeholder exists, False otherwise
        """
        return placeholder in self._placeholders

    def get_values(self, placeholder: str) -> Optional[List[str]]:
        """
        Get the current values for a placeholder.

        Args:
            placeholder: The placeholder name (without braces)

        Returns:
            List of values, or None if placeholder has no values set
        """
        return self.values.get(placeholder)

    def clear_values(self) -> 'SentenceGenerator':
        """
        Clear all placeholder values.

        Returns:
            self for method chaining
        """
        self.values.clear()
        return self

    def add_template(self, template: str) -> 'SentenceGenerator':
        """
        Add another template variation.

        Args:
            template: New template string

        Returns:
            self for method chaining
        """
        self.templates.append(template)
        self._placeholders = self._extract_placeholders()
        self._expanded_templates_cache = None
        self._templates_hash = hash(tuple(self.templates))
        return self

    def get_template(self, index: int) -> str:
        """
        Get a template at the specified index.

        Args:
            index: The template index (0-based)

        Returns:
            The template string

        Raises:
            IndexError: If index is out of range
        """
        return self.templates[index]

    def remove_template(self, index: int) -> 'SentenceGenerator':
        """
        Remove a template at the specified index.

        Args:
            index: The template index (0-based)

        Returns:
            self for method chaining

        Raises:
            IndexError: If index is out of range
        """
        del self.templates[index]
        self._placeholders = self._extract_placeholders()
        self._expanded_templates_cache = None
        self._templates_hash = hash(tuple(self.templates))
        return self

    def clear_templates(self) -> 'SentenceGenerator':
        """
        Remove all templates and clear values.

        Returns:
            self for method chaining
        """
        self.templates.clear()
        self.values.clear()
        self._placeholders = self._extract_placeholders()
        self._expanded_templates_cache = None
        self._templates_hash = hash(tuple(self.templates))
        return self

    def _get_all_expanded_templates(self) -> List[str]:
        """Get all templates with inline alternatives expanded."""
        # Check if templates have changed
        current_hash = hash(tuple(self.templates))
        if self._expanded_templates_cache is not None and current_hash == self._templates_hash:
            return self._expanded_templates_cache

        expanded: List[str] = []
        for t in self.templates:
            expanded.extend(self._expand_inline_alternatives(t))

        # Cache the result
        self._expanded_templates_cache = expanded
        self._templates_hash = current_hash
        return expanded

    def _apply_transform(self, value: str, transform: str, arg: Optional[str]) -> str:
        """
        Apply a transform function to a value.

        Supported transforms:
            - upper: Convert to uppercase
            - lower: Convert to lowercase
            - title: Title case
            - capitalize: Capitalize first letter
            - truncate:N: Truncate to N characters
            - default:N: Use N if value is empty
            - a: Add 'a' or 'an' before the value
            - an: Add 'an' before the value (force)
            - plural: Pluralize the value (simple -s rule)
            - pluralize:N: Pluralize with custom suffix

        Example:
            >>> gen._apply_transform("hello", "upper", None)
            'HELLO'
            >>> gen._apply_transform("apple", "a", None)
            'an apple'
            >>> gen._apply_transform("cat", "plural", None)
            'cats'
        """
        if transform == 'upper':
            return value.upper()
        elif transform == 'lower':
            return value.lower()
        elif transform == 'title':
            return value.title()
        elif transform == 'capitalize':
            return value.capitalize()
        elif transform == 'truncate' and arg:
            try:
                n = int(arg)
                return value[:n]
            except ValueError:
                return value
        elif transform == 'default' and arg:
            return value if value else arg
        elif transform == 'a':
            # Add 'a' or 'an' based on first letter
            if value and value[0].lower() in 'aeiou':
                return f'an {value}'
            return f'a {value}'
        elif transform == 'an':
            return f'an {value}'
        elif transform == 'plural':
            # Enhanced pluralization with irregular forms
            return self._pluralize(value)
        elif transform == 'pluralize' and arg:
            return value + arg
        elif transform == 'verb_s':
            # Third person singular verb conjugation
            return self._conjugate_verb(value, person='third', number='singular')
        elif transform == 'verb_ing':
            # Present participle (-ing form)
            return self._verb_to_ing(value)
        elif transform == 'verb_ed':
            # Past tense (-ed form)
            return self._verb_to_past(value)
        elif transform == 'possessive':
            # Make possessive
            if value.endswith('s'):
                return value + "'"
            return value + "'s"
        elif transform == 'reverse':
            # Reverse the string
            return value[::-1]
        elif transform == 'first':
            # First letter only
            return value[0] if value else ''
        elif transform == 'last':
            # Last letter only
            return value[-1] if value else ''
        elif transform == 'comparative':
            # Convert adjective to comparative form
            return self._to_comparative(value)
        elif transform == 'superlative':
            # Convert adjective to superlative form
            return self._to_superlative(value)
        elif transform == 'negate':
            # Add negation prefix
            return self._negate_word(value)
        elif transform == 'random' and arg:
            # Pick N random characters from value
            try:
                n = int(arg)
                if len(value) <= n:
                    return value
                return ''.join(random.sample(value, n))
            except ValueError:
                return value
        elif transform == 'choose' and arg:
            # Choose Nth character (0-indexed)
            try:
                n = int(arg)
                return value[n] if 0 <= n < len(value) else value
            except ValueError:
                return value
        elif transform == 'slice' and arg:
            # Slice string: {VAR|slice:0:5}
            try:
                parts = arg.split(':')
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else None
                return value[start:end]
            except (ValueError, IndexError):
                return value
        elif transform == 'length':
            # Return length of string
            return str(len(value))
        elif transform == 'pad' and arg:
            # Pad to length: {VAR|pad:10} or {VAR|pad:10:X}
            try:
                parts = arg.split(':')
                width = int(parts[0])
                fillchar = parts[1] if len(parts) > 1 else ' '
                return value.ljust(width, fillchar)
            except ValueError:
                return value
        elif transform == 'strip':
            # Strip whitespace
            return value.strip()
        elif transform == 'replace' and arg:
            # Replace: {VAR|replace:old:new}
            try:
                parts = arg.split(':')
                if len(parts) >= 2:
                    return value.replace(parts[0], parts[1])
            except (ValueError, IndexError):
                pass
            return value
        return value

    def _to_comparative(self, adjective: str) -> str:
        """Convert adjective to comparative form."""
        if not adjective:
            return adjective

        # Irregular comparatives
        irregular = {
            'good': 'better', 'bad': 'worse', 'far': 'farther',
            'little': 'less', 'much': 'more', 'many': 'more'
        }
        lower = adjective.lower()
        if lower in irregular:
            result = irregular[lower]
            return result.capitalize() if adjective[0].isupper() else result

        # One syllable: add -er
        if len(adjective) <= 5:
            if adjective.endswith('e'):
                return adjective + 'r'
            elif adjective.endswith('y'):
                return adjective[:-1] + 'ier'
            elif len(adjective) >= 3 and adjective[-1] not in 'aeiou' and adjective[-2] in 'aeiou':
                return adjective + adjective[-1] + 'er'
            return adjective + 'er'

        # Two+ syllables: add 'more'
        return f'more {adjective}'

    def _to_superlative(self, adjective: str) -> str:
        """Convert adjective to superlative form."""
        if not adjective:
            return adjective

        # Irregular superlatives
        irregular = {
            'good': 'best', 'bad': 'worst', 'far': 'farthest',
            'little': 'least', 'much': 'most', 'many': 'most'
        }
        lower = adjective.lower()
        if lower in irregular:
            result = irregular[lower]
            return result.capitalize() if adjective[0].isupper() else result

        # One syllable: add -est
        if len(adjective) <= 5:
            if adjective.endswith('e'):
                return adjective + 'st'
            elif adjective.endswith('y'):
                return adjective[:-1] + 'iest'
            elif len(adjective) >= 3 and adjective[-1] not in 'aeiou' and adjective[-2] in 'aeiou':
                return adjective + adjective[-1] + 'est'
            return adjective + 'est'

        # Two+ syllables: add 'most'
        return f'most {adjective}'

    def _negate_word(self, word: str) -> str:
        """Add negation prefix to a word."""
        if not word:
            return word

        # Common negation patterns
        prefixes = {
            'possible': 'impossible', 'able': 'unable', 'known': 'unknown',
            'known': 'unknown', 'fair': 'unfair', 'happy': 'unhappy',
            'lucky': 'unlucky', 'clear': 'unclear', 'certain': 'uncertain',
            'correct': 'incorrect', 'direct': 'indirect', 'active': 'inactive',
            'visible': 'invisible', 'valid': 'invalid', 'legal': 'illegal',
            'mortal': 'immortal', 'moral': 'immoral', 'perfect': 'imperfect',
            'regular': 'irregular', 'responsible': 'irresponsible'
        }

        lower = word.lower()
        if lower in prefixes:
            result = prefixes[lower]
            return result.capitalize() if word[0].isupper() else result

        # Default to 'un-' prefix
        return f'un{word}'

    def _pluralize(self, word: str) -> str:
        """
        Pluralize a noun with support for irregular forms.

        Args:
            word: Singular noun

        Returns:
            Plural form
        """
        if not word:
            return word

        # Irregular plurals
        irregular = {
            'person': 'people',
            'child': 'children',
            'man': 'men',
            'woman': 'women',
            'foot': 'feet',
            'tooth': 'teeth',
            'goose': 'geese',
            'mouse': 'mice',
            'louse': 'lice',
            'ox': 'oxen',
            'die': 'dice',
            'cactus': 'cacti',
            'focus': 'foci',
            'fungus': 'fungi',
            'nucleus': 'nuclei',
            'syllabus': 'syllabi',
            'analysis': 'analyses',
            'diagnosis': 'diagnoses',
            'oasis': 'oases',
            'thesis': 'theses',
            'crisis': 'crises',
            'phenomenon': 'phenomena',
            'criterion': 'criteria',
            'datum': 'data',
            'medium': 'media',
            'memorandum': 'memoranda',
            'curriculum': 'curricula',
            'alumnus': 'alumni',
            'stimulus': 'stimuli',
            'radius': 'radii',
            'appendix': 'appendices',
            'index': 'indices',
            'sheep': 'sheep',
            'deer': 'deer',
            'fish': 'fish',
            'species': 'species',
            'series': 'series',
            'aircraft': 'aircraft',
        }

        lower_word = word.lower()
        if lower_word in irregular:
            plural = irregular[lower_word]
            # Preserve capitalization
            if word[0].isupper():
                return plural.capitalize()
            return plural

        # Standard rules
        if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return word + 'es'
        elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
            return word[:-1] + 'ies'
        elif word.endswith(('fe', 'f')):
            # Words ending in -f or -fe often change to -ves
            if word.endswith('fe'):
                return word[:-2] + 'ves'
            elif word.endswith('rf') or word.endswith('ff'):
                return word + 's'
            else:
                return word[:-1] + 'ves'
        elif word.endswith('o'):
            # Words ending in -o often add -es
            if word in {'piano', 'photo', 'memo', 'studio', 'zoo', 'radio', 'video'}:
                return word + 's'
            return word + 'es'
        elif word.endswith('us'):
            # Latin -us to -i
            if word in {'cactus', 'focus', 'fungus', 'nucleus', 'syllabus', 'stimulus', 'radius'}:
                return word[:-2] + 'i'
            return word + 'es'
        elif word.endswith('is'):
            # Greek -is to -es
            if word in {'analysis', 'diagnosis', 'oasis', 'thesis', 'crisis'}:
                return word[:-2] + 'es'
            return word + 'es'
        elif word.endswith('on'):
            # Greek -on to -a
            if word in {'phenomenon', 'criterion', 'automaton'}:
                return word[:-2] + 'a'
            return word + 's'

        return word + 's'

    def _conjugate_verb(self, verb: str, person: str = 'third', number: str = 'singular') -> str:
        """
        Conjugate a verb for the given person and number.

        Args:
            verb: Base form of verb
            person: 'first', 'second', or 'third'
            number: 'singular' or 'plural'

        Returns:
            Conjugated verb
        """
        if not verb:
            return verb

        # Only third person singular adds -s
        if person != 'third' or number != 'singular':
            return verb

        # Third person singular rules
        if verb.endswith(('s', 'sh', 'ch', 'x', 'z', 'o')):
            return verb + 'es'
        elif verb.endswith('y') and len(verb) > 1 and verb[-2] not in 'aeiou':
            return verb[:-1] + 'ies'
        elif verb.endswith('have'):
            return 'has'
        elif verb.endswith('be'):
            return 'is'
        elif verb.endswith('do'):
            return 'does'

        return verb + 's'

    def _verb_to_ing(self, verb: str) -> str:
        """
        Convert verb to present participle (-ing form).

        Args:
            verb: Base form of verb

        Returns:
            -ing form
        """
        if not verb:
            return verb

        # Special cases
        special = {'be': 'being', 'have': 'having', 'die': 'dying', 'lie': 'lying', 'tie': 'tying'}
        if verb.lower() in special:
            return special[verb.lower()]

        # Drop silent -e
        if verb.endswith('e') and not verb.endswith(('ee', 'oe', 'ye')):
            return verb[:-1] + 'ing'

        # Double final consonant for CVC pattern with stressed last syllable
        if len(verb) >= 3 and verb[-1].isalpha() and verb[-1] not in 'aeiou':
            if verb[-2] in 'aeiou' and verb[-3] not in 'aeiou':
                # Check if last syllable is stressed (simplified: assume yes for short verbs)
                if len(verb) <= 4:
                    return verb + verb[-1] + 'ing'

        return verb + 'ing'

    def _verb_to_past(self, verb: str) -> str:
        """
        Convert verb to simple past tense (-ed form).

        Args:
            verb: Base form of verb

        Returns:
            Past tense form (regular only)
        """
        if not verb:
            return verb

        # Common irregular past tenses
        irregular = {
            'be': 'was/were', 'have': 'had', 'do': 'did', 'say': 'said',
            'go': 'went', 'get': 'got', 'make': 'made', 'know': 'knew',
            'think': 'thought', 'take': 'took', 'see': 'saw', 'come': 'came',
            'want': 'wanted', 'give': 'gave', 'use': 'used', 'find': 'found',
            'tell': 'told', 'ask': 'asked', 'work': 'worked', 'seem': 'seemed',
            'feel': 'felt', 'try': 'tried', 'leave': 'left', 'call': 'called',
            'keep': 'kept', 'let': 'let', 'begin': 'began', 'hold': 'held',
            'write': 'wrote', 'stand': 'stood', 'hear': 'heard', 'run': 'ran',
            'bring': 'brought', 'sit': 'sat', 'win': 'won', 'understand': 'understood',
            'draw': 'drew', 'break': 'broke', 'spend': 'spent', 'cut': 'cut',
            'rise': 'rose', 'drive': 'drove', 'buy': 'bought', 'wear': 'wore',
            'choose': 'chose', 'seek': 'sought', 'throw': 'threw', 'catch': 'caught',
            'deal': 'dealt', 'lose': 'lost', 'fall': 'fell', 'send': 'sent',
            'build': 'built', 'grow': 'grew', 'pay': 'paid', 'eat': 'ate',
            'lead': 'led', 'read': 'read', 'blow': 'blew', 'show': 'showed/shown',
            'fly': 'flew', 'forget': 'forgot', 'sell': 'sold', 'fight': 'fought',
            'teach': 'taught', 'sing': 'sang', 'forget': 'forgot', 'swim': 'swam',
            'drink': 'drank', 'ring': 'rang', 'shake': 'shook', 'wake': 'woke',
            'freeze': 'froze', 'speak': 'spoke', 'steal': 'stole', 'tear': 'tore',
            'hide': 'hid', 'slide': 'slid', 'strike': 'struck', 'swing': 'swung',
            'slay': 'slew', 'slay': 'slain', 'bind': 'bound', 'grind': 'ground',
            'wind': 'wound', 'find': 'found', 'shine': 'shone', 'spin': 'spun',
            'spit': 'spat', 'stick': 'stuck', 'sting': 'stung', 'sling': 'slung',
            'creep': 'crept', 'sleep': 'slept', 'sweep': 'swept', 'weep': 'wept',
            'feed': 'fed', 'speed': 'sped', 'bleed': 'bled', 'breed': 'bred',
            'flee': 'fled', 'lead': 'led', 'meet': 'met', 'shoot': 'shot'
        }

        lower_verb = verb.lower()
        if lower_verb in irregular:
            past = irregular[lower_verb]
            # Preserve capitalization
            if verb[0].isupper():
                return past.capitalize()
            return past

        # Regular -ed rules
        if verb.endswith('e'):
            return verb + 'd'
        elif verb.endswith('y') and len(verb) > 1 and verb[-2] not in 'aeiou':
            return verb[:-1] + 'ied'
        elif len(verb) >= 3 and verb[-1].isalpha() and verb[-1] not in 'aeiou':
            if verb[-2] in 'aeiou' and verb[-3] not in 'aeiou':
                if len(verb) <= 4:
                    return verb + verb[-1] + 'ed'

        return verb + 'ed'

    def _evaluate_comparison(self, left: str, operator: str, right: str) -> bool:
        """
        Evaluate a comparison expression.

        Supports: ==, !=, <, >, <=, >=
        """
        # Try to convert to numbers
        try:
            left_val = float(left)
            right_val = float(right)
            if operator == '==':
                return left_val == right_val
            elif operator == '!=':
                return left_val != right_val
            elif operator == '<':
                return left_val < right_val
            elif operator == '>':
                return left_val > right_val
            elif operator == '<=':
                return left_val <= right_val
            elif operator == '>=':
                return left_val >= right_val
        except ValueError:
            # String comparison
            if operator == '==':
                return left == right
            elif operator == '!=':
                return left != right
            elif operator == '<':
                return left < right
            elif operator == '>':
                return left > right
            elif operator == '<=':
                return left <= right
            elif operator == '>=':
                return left >= right
        return False

    def _evaluate_conditional(self, condition: str, values_map: Dict[str, str]) -> str:
        """
        Evaluate a conditional expression.

        Syntax:
        - {if:PLACEHOLDER:value:then_text|else_text}
        - {if:LEVEL>5:high_level|low_level}
        - {if:HP>50 and MANA>30:powerful|weak}

        Args:
            condition: The conditional string (without the {if: prefix)
            values_map: Map of placeholder values

        Returns:
            Evaluated result string
        """
        # Handle comparison syntax: {if:LEVEL>5:then|else}
        comparison_match = re.match(r'([A-Z][A-Z0-9_]*|[\d.]+)\s*(==|!=|<=|>=|<|>)\s*([\d.]+|[A-Z][A-Z0-9_]*):(.+)', condition)
        if comparison_match:
            left = comparison_match.group(1)
            operator = comparison_match.group(2)
            right = comparison_match.group(3)
            then_else = comparison_match.group(4)

            # Resolve placeholders
            if left in values_map:
                left = values_map[left]
            if right in values_map:
                right = values_map[right]

            # Parse then/else
            if '|' in then_else:
                then_part, else_part = then_else.split('|', 1)
            else:
                then_part = then_else
                else_part = ''

            if self._evaluate_comparison(str(left), operator, str(right)):
                return then_part
            return else_part

        # Handle boolean logic: {if:A and B:then|else} or {if:A or B:then|else}
        if ' and ' in condition or ' or ' in condition:
            # Simple boolean evaluation
            parts = re.split(r'\s+(and|or)\s+', condition, maxsplit=1)
            if len(parts) == 3:
                left_cond = parts[0].strip()
                logic_op = parts[1]
                right_cond = parts[2].strip()

                # Evaluate each condition (simple check if value exists and is truthy)
                left_result = bool(values_map.get(left_cond, ''))
                right_result = bool(values_map.get(right_cond, ''))

                if logic_op == 'and':
                    result = left_result and right_result
                else:  # or
                    result = left_result or right_result

                # Get then/else from the last part after colon
                if ':' in right_cond:
                    idx = condition.rfind(':')
                    then_else = condition[idx+1:]
                    if '|' in then_else:
                        then_part, else_part = then_else.split('|', 1)
                    else:
                        then_part = then_else
                        else_part = ''
                    return then_part if result else else_part

        # Handle PLACEHOLDER:value:then|else syntax (already stripped {if: prefix)
        parts = condition.split(':')
        if len(parts) >= 3:
            placeholder = parts[0]
            check_value = parts[1]
            then_else = ':'.join(parts[2:])  # Rejoin in case then_text contains colons

            if '|' in then_else:
                then_part, else_part = then_else.split('|', 1)
            else:
                then_part = then_else
                else_part = ''

            actual_value = values_map.get(placeholder, '')
            if actual_value == check_value:
                return then_part
            return else_part

        return ''

    def _evaluate_math(self, expression: str, values_map: Dict[str, str]) -> str:
        """
        Evaluate a math expression.

        Syntax: {LEVEL+2}, {COUNT*10}, {DAMAGE/2}, {GOLD-50}
        Supports: +, -, *, /, % (modulo)

        Args:
            expression: Math expression
            values_map: Map of placeholder values

        Returns:
            Result as string
        """
        # Replace placeholders with values
        for placeholder, values in values_map.items():
            if placeholder in expression:
                # Use first value if list
                value = values[0] if isinstance(values, list) else values
                try:
                    expression = expression.replace(placeholder, str(float(value)))
                except (ValueError, TypeError):
                    pass

        # Safe math evaluation
        try:
            # Only allow safe characters
            if re.match(r'^[\d\s\+\-\*\/\%\.\(\)]+$', expression):
                result = eval(expression)
                # Return as int if whole number
                if isinstance(result, float) and result.is_integer():
                    return str(int(result))
                return str(result)
        except (SyntaxError, ZeroDivisionError, TypeError):
            pass

        return expression

    def _expand_loops(self, template: str, values_map: Dict[str, str]) -> str:
        """
        Expand loop/repeat syntax.

        Syntax: {repeat:N:content} or {repeat:PLACEHOLDER:content}

        Args:
            template: Template string with potential loops
            values_map: Map of placeholder values

        Returns:
            Template with loops expanded
        """
        loop_pattern = re.compile(r'\{repeat:(\d+|[A-Z][A-Z0-9_]*):([^}]+)\}')

        def replace_loop(match):
            count_str = match.group(1)
            content = match.group(2)

            # Get repeat count
            if count_str.isdigit():
                count = int(count_str)
            elif count_str in values_map:
                try:
                    count = int(values_map[count_str])
                except (ValueError, TypeError):
                    count = 1
            else:
                count = 1

            # Repeat content
            return ''.join([content] * count)

        return loop_pattern.sub(replace_loop, template)

    def _expand_nested_placeholders(self, template: str, values_map: Dict[str, str]) -> str:
        """
        Expand nested placeholders like {{INNER}_{OUTER}}.

        Nested placeholders are evaluated inner-first.

        Args:
            template: Template string with potential nested placeholders
            values_map: Map of placeholder values

        Returns:
            Template with nested placeholders expanded
        """
        max_iterations = 10
        iteration = 0

        while '{{' in template and iteration < max_iterations:
            # Find innermost nested placeholder (one without nested braces inside)
            # Pattern: { ... { ... } ... }
            inner_pattern = re.compile(r'\{([^{}]*\{[^{}]+\}[^{}]*)\}')
            match = inner_pattern.search(template)

            if not match:
                break

            inner_content = match.group(1)
            # Evaluate the inner content
            evaluated = self._fill_template(inner_content, values_map)
            # Replace the entire match with evaluated content
            template = template[:match.start()] + evaluated + template[match.end():]
            iteration += 1

        return template

    def _process_advanced_syntax(self, template: str, values_map: Dict[str, str]) -> str:
        """
        Process advanced template syntax including conditionals, math, and loops.

        Args:
            template: Template string
            values_map: Map of placeholder values

        Returns:
            Processed template string
        """
        result = template

        # First, expand loops
        result = self._expand_loops(result, values_map)

        # Handle math expressions: {LEVEL+2}, {COUNT*10}
        math_pattern = re.compile(r'\{([A-Z][A-Z0-9_]*[\+\-\*\/\%][\d\.A-Z_]+)\}')
        for match in math_pattern.finditer(result):
            expression = match.group(1)
            replacement = self._evaluate_math(expression, values_map)
            result = result.replace(match.group(0), replacement, 1)

        # Handle conditionals with special pattern
        conditional_pattern = re.compile(r'\{if:([^}]+)\}')
        for match in conditional_pattern.finditer(result):
            condition = match.group(1)
            replacement = self._evaluate_conditional(condition, values_map)
            result = result.replace(match.group(0), replacement, 1)

        # Handle nested placeholders
        result = self._expand_nested_placeholders(result, values_map)

        return result

    def _fill_template(self, template: str, values_map: Dict[str, str]) -> str:
        """
        Fill a single template with given values.

        Supports transforms: {PLACEHOLDER|transform[:arg]}
        Example: "{USER|upper}", "{NAME|truncate:10}"
        Supports conditionals: {if:PLACEHOLDER:value:then|else}
        Supports nested: {{PREFIX}_{NAME}}
        """
        result = template

        # First process advanced syntax (conditionals, nested)
        result = self._process_advanced_syntax(result, values_map)

        # Find all placeholders with optional transforms
        for match in TRANSFORM_PATTERN.finditer(result):
            full_match = match.group(0)
            placeholder = match.group(1)
            transform_part = match.group(2)  # e.g., "|upper" or "|truncate:10"

            if placeholder in values_map:
                value = values_map[placeholder]

                # Apply transform if present
                if transform_part:
                    # Remove leading '|' and parse
                    transform_str = transform_part[1:]
                    transform_name, transform_arg = self._parse_transform_args(transform_str)
                    value = self._apply_transform(value, transform_name, transform_arg)

                result = result.replace(full_match, value, 1)

        return result

    def generate(self, seed: Optional[int] = None, use_defaults: bool = True) -> str:
        """
        Generate a single sentence with random template and values.

        Args:
            seed: Optional random seed for reproducibility
            use_defaults: If True, use default_values for missing placeholders.
                         If False, raise ValueError for missing values.

        Returns:
            Generated sentence

        Raises:
            ValueError: If placeholder has no values and use_defaults is False

        Example:
            >>> gen = SentenceGenerator("{USER} {killed|eliminated} {TARGET}")
            >>> gen.set_values("USER", ["Alice"])
            >>> gen.set_values("TARGET", ["Bob"])
            >>> gen.generate(seed=42)
            'Alice killed Bob'
        """
        if seed is not None:
            random.seed(seed)

        # Expand inline alternatives and pick a random template
        expanded = self._get_all_expanded_templates()
        template = random.choice(expanded)
        placeholders_in_template = self._extract_placeholders_from_template(template)

        values_map: Dict[str, str] = {}
        for placeholder in placeholders_in_template:
            if placeholder in self.values:
                values_map[placeholder] = random.choice(self.values[placeholder])
            elif use_defaults and placeholder in self.default_values:
                values_map[placeholder] = self.default_values[placeholder]
            else:
                raise ValueError(
                    f"No values set for placeholder '{placeholder}'. "
                    f"Available: {', '.join(self.values.keys()) if self.values else 'none'}"
                )

        return self._fill_template(template, values_map)

    def generate_all(self, use_defaults: bool = True) -> List[str]:
        """
        Generate all possible combinations across all template variations.

        Args:
            use_defaults: If True, use default_values for missing placeholders.
                         If False, raise ValueError for missing values.

        Returns:
            List of all possible sentences

        Raises:
            ValueError: If placeholder has no values and use_defaults is False

        Example:
            >>> gen = SentenceGenerator("{USER} is {STATUS}")
            >>> gen.set_values("USER", ["Alice", "Bob"])
            >>> gen.set_values("STATUS", ["happy", "sad"])
            >>> gen.generate_all()
            ['Alice is happy', 'Alice is sad', 'Bob is happy', 'Bob is sad']
        """
        sentences = []
        expanded = self._get_all_expanded_templates()

        for template in expanded:
            placeholders_in_template = self._extract_placeholders_from_template(template)

            # Skip if no placeholders
            if not placeholders_in_template:
                sentences.append(template)
                continue

            # Build value lists, using defaults for missing placeholders
            value_lists = []
            for p in placeholders_in_template:
                if p in self.values:
                    value_lists.append(self.values[p])
                elif use_defaults and p in self.default_values:
                    value_lists.append([self.default_values[p]])
                else:
                    raise ValueError(
                        f"No values set for placeholder '{p}'. "
                        f"Available: {', '.join(self.values.keys()) if self.values else 'none'}"
                    )

            for combination in itertools.product(*value_lists):
                values_map = dict(zip(placeholders_in_template, combination))
                sentences.append(self._fill_template(template, values_map))

        return sentences

    def generate_multiple(self, count: int, seed: Optional[int] = None, use_defaults: bool = True) -> List[str]:
        """
        Generate multiple random sentences.

        Args:
            count: Number of sentences to generate
            seed: Optional random seed for reproducibility
            use_defaults: If True, use default_values for missing placeholders

        Returns:
            List of generated sentences
        """
        if seed is not None:
            random.seed(seed)

        return [self.generate(use_defaults=use_defaults) for _ in range(count)]

    def load_values_from_json(self, filepath: str) -> 'SentenceGenerator':
        """
        Load placeholder values from a JSON file.

        JSON format:
        {
            "USER": ["Alice", "Bob"],
            "STATUS": ["happy", "sad"]
        }

        Args:
            filepath: Path to the JSON file

        Returns:
            self for method chaining
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        for key, value in data.items():
            key = key.upper()
            if self.has_placeholder(key):
                self.set_values(key, value if isinstance(value, list) else [value])
        return self

    def load_values_from_csv(self, filepath: str, placeholder_column: str = 'placeholder',
                             value_column: str = 'value') -> 'SentenceGenerator':
        """
        Load placeholder values from a CSV file.

        CSV format (default):
        placeholder,value
        USER,Alice
        USER,Bob
        STATUS,happy

        Or with multiple values per row:
        placeholder,values
        USER,"Alice,Bob,Charlie"
        STATUS,"happy,sad"

        Args:
            filepath: Path to the CSV file
            placeholder_column: Name of the column containing placeholder names
            value_column: Name of the column containing values

        Returns:
            self for method chaining
        """
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                placeholder = row.get(placeholder_column, '').strip().upper()
                value = row.get(value_column, '').strip()
                if placeholder and value:
                    # Support comma-separated values in a single cell
                    values = [v.strip() for v in value.split(',') if v.strip()]
                    if self.has_placeholder(placeholder):
                        if placeholder not in self.values:
                            self.values[placeholder] = []
                        self.values[placeholder].extend(values)
        return self

    def load_values_from_file(self, filepath: str) -> 'SentenceGenerator':
        """
        Load placeholder values from a file (auto-detect format).

        Supports JSON (.json) and CSV (.csv) files.

        Args:
            filepath: Path to the file

        Returns:
            self for method chaining

        Raises:
            ValueError: If file format is not supported
        """
        if filepath.endswith('.json'):
            return self.load_values_from_json(filepath)
        elif filepath.endswith('.csv'):
            return self.load_values_from_csv(filepath)
        else:
            raise ValueError(
                f"Unsupported file format: {filepath}. Use .json or .csv"
            )

    def __repr__(self) -> str:
        return f"SentenceGenerator(templates={self.template_count}, placeholders={self._placeholders})"


def main():
    """Interactive CLI for the sentence generator."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Template-Based Sentence Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Syntax:
  {PLACEHOLDER}              - Variable (uppercase)
  {word1|word2}              - Inline alternatives
  {word:2|other:1}           - Weighted alternatives (higher weight = more likely)
  {PLACEHOLDER|transform}    - Transforms: upper, lower, title, a, an, plural, truncate:N

Transforms:
  upper, lower, title        - Case transforms
  capitalize                 - Capitalize first letter
  a, an                      - Add article (auto-detect a/an)
  plural                     - Simple pluralization
  truncate:N                 - Truncate to N characters
  default:VALUE              - Use VALUE if empty

Examples:
  python gm.py -t "{USER} is {STATUS}" -v USER=Alice -v STATUS=happy
  python gm.py -t "{USER} {killed|eliminated} {TARGET}" --count 5
  python gm.py -t "I ate {APPLE|plural}" -v APPLE=apple --count 3
  python gm.py -t "{NAME|upper} is here" -v NAME=alice
  python gm.py --load templates.json --output results.txt
  python gm.py -t "{USER}" --values-file users.json
        """
    )

    parser.add_argument("-t", "--template", action="append", dest="templates",
                        help="Template string (can be specified multiple times)")
    parser.add_argument("-v", "--value", action="append", dest="values",
                        help="Placeholder value in format PLACEHOLDER=value")
    parser.add_argument("-d", "--default", action="append", dest="defaults",
                        help="Default value in format PLACEHOLDER=default")
    parser.add_argument("-c", "--count", type=int, default=1,
                        help="Number of sentences to generate (default: 1)")
    parser.add_argument("--load", dest="load_file",
                        help="Load templates and values from JSON file")
    parser.add_argument("--values-file", dest="values_file",
                        help="Load placeholder values from JSON or CSV file")
    parser.add_argument("--save", dest="save_file",
                        help="Save configuration to JSON file")
    parser.add_argument("-o", "--output", dest="output_file",
                        help="Write output to file instead of stdout")
    parser.add_argument("--all", action="store_true",
                        help="Generate all possible combinations")
    parser.add_argument("--seed", type=int,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    templates = []
    values_map: Dict[str, List[str]] = {}
    defaults: Dict[str, str] = {}

    # Load from file if specified
    if args.load_file:
        try:
            with open(args.load_file, 'r') as f:
                data = json.load(f)
                templates = data.get('templates', [])
                for k, v in data.get('values', {}).items():
                    values_map[k] = v if isinstance(v, list) else [v]
                defaults = data.get('defaults', {})
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading file: {e}", file=sys.stderr)
            sys.exit(1)

    # Add templates from command line
    if args.templates:
        templates.extend(args.templates)

    # Parse defaults from command line
    if args.defaults:
        for item in args.defaults:
            if '=' in item:
                key, value = item.split('=', 1)
                defaults[key.strip().upper()] = value.strip()

    # Create generator
    generator = SentenceGenerator(templates, defaults)

    # Load values from file if specified
    if args.values_file:
        try:
            generator.load_values_from_file(args.values_file)
        except (IOError, json.JSONDecodeError, ValueError) as e:
            print(f"Error loading values file: {e}", file=sys.stderr)
            sys.exit(1)

    # Parse values from command line
    if args.values:
        for item in args.values:
            if '=' in item:
                key, value = item.split('=', 1)
                key = key.strip().upper()
                # Support comma-separated values
                values = [v.strip() for v in value.split(',') if v.strip()]
                if key not in values_map:
                    values_map[key] = []
                values_map[key].extend(values)

    # Apply values from command line
    for placeholder, values in values_map.items():
        if generator.has_placeholder(placeholder):
            generator.set_values(placeholder, values)

    # Interactive mode if no templates provided
    if not templates:
        print("=== Template-Based Sentence Generator ===\n")
        print("Syntax:")
        print("  {PLACEHOLDER} - Variable (uppercase)")
        print("  {word1|word2|word3} - Inline alternatives")
        print("  {word:2|other:1} - Weighted alternatives (lowercase)")
        print("  {PLACEHOLDER|transform} - Transforms: upper, lower, a, an, plural\n")

        # Get first template
        template = input("Enter your template: ")
        if not template.strip():
            print("Error: Template cannot be empty")
            return
        templates.append(template)

        # Ask for more variations
        while True:
            more = input("\nAdd another template variation? (y/n): ").strip().lower()
            if more == 'n':
                break
            elif more == 'y':
                t = input("Enter variation: ")
                if t.strip():
                    templates.append(t)
            else:
                print("Enter 'y' or 'n'")

        generator = SentenceGenerator(templates, defaults)
        placeholders = generator.placeholders

        if not placeholders:
            print("No placeholders found in template!")
            print("Example: '{USER} is NOT the {IMPOSTER}'")
            return

        print(f"\nFound placeholders: {', '.join(placeholders)}")
        print(f"Template variations: {generator.template_count}")
        print("\nEnter values for each placeholder (comma-separated for multiple options):")

        # Get values for each placeholder
        for placeholder in placeholders:
            values_input = input(f"  {placeholder}: ")
            values = [v.strip() for v in values_input.split(',') if v.strip()]
            if not values:
                print(f"Error: Must provide at least one value for '{placeholder}'")
                return
            generator.set_values(placeholder, values)

    # Save configuration if requested
    if args.save_file:
        config = {
            'templates': generator.templates,
            'values': generator.values,
            'defaults': generator.default_values
        }
        try:
            with open(args.save_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Configuration saved to {args.save_file}")
        except IOError as e:
            print(f"Error saving file: {e}", file=sys.stderr)

    # Generate sentences
    output_lines = []

    if args.all:
        sentences = generator.generate_all()
        total = len(sentences)
        output_lines.append(f"All {total} combinations:")
        for i, sentence in enumerate(sentences, 1):
            output_lines.append(f"  {i}. {sentence}")
    else:
        if args.count > 30:
            output_lines.append(f"Generating {args.count} sentences...")
        sentences = generator.generate_multiple(args.count, seed=args.seed)
        for sentence in sentences:
            output_lines.append(sentence)

    # Output results
    output_text = '\n'.join(output_lines)
    if args.output_file:
        try:
            with open(args.output_file, 'w') as f:
                f.write(output_text + '\n')
            print(f"Output written to {args.output_file}")
        except IOError as e:
            print(f"Error writing file: {e}", file=sys.stderr)
    else:
        print("\n--- Generated Sentences ---")
        print(output_text)
        print()


if __name__ == "__main__":
    main()
