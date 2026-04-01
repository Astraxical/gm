#!/usr/bin/env python3
"""
Pattern Learner Module

Analyzes existing content to extract patterns for generation.
Learns structures, styles, and common elements from your content.
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """A learned pattern from content."""
    name: str
    pattern_type: str  # structure, phrase, transition, etc.
    frequency: int = 0
    examples: List[str] = field(default_factory=list)
    structure: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "pattern_type": self.pattern_type,
            "frequency": self.frequency,
            "examples": self.examples,
            "structure": self.structure,
            "confidence": self.confidence
        }


class PatternLearner:
    """Learn patterns from existing content."""
    
    def __init__(self, memory_dir: str = "ai_data"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Pattern storage
        self.patterns: Dict[str, List[Pattern]] = defaultdict(list)
        self.style_profile: Dict[str, Any] = {}
        self.content_stats: Dict[str, Any] = {}
        
        # N-gram storage for text generation
        self.unigrams: Counter = Counter()
        self.bigrams: Counter = Counter()
        self.trigrams: Counter = Counter()
        
        # Load existing patterns
        self._load_patterns()
    
    def learn_from_content(self, content: Dict[str, Any], content_type: str) -> None:
        """
        Learn patterns from a piece of content.
        
        Args:
            content: Content dict (quest, NPC, encounter, etc.)
            content_type: Type of content
        """
        # Learn structure patterns
        self._learn_structure(content, content_type)
        
        # Learn text patterns
        self._learn_text_patterns(content, content_type)
        
        # Learn progression patterns
        self._learn_progression(content, content_type)
        
        # Update stats
        self._update_stats(content_type)
        
        logger.debug(f"Learned from {content_type}: {content.get('name', 'unnamed')}")
    
    def _learn_structure(self, content: Dict[str, Any], content_type: str) -> None:
        """Learn structural patterns from content."""
        # Extract top-level keys as structure
        keys = tuple(sorted(content.keys()))
        
        # Find or create structure pattern
        pattern_name = f"{content_type}_structure"
        existing = self._find_pattern(pattern_name, "structure")
        
        if existing:
            existing.frequency += 1
        else:
            pattern = Pattern(
                name=pattern_name,
                pattern_type="structure",
                frequency=1,
                structure={"keys": list(keys)},
                confidence=1.0
            )
            self.patterns["structure"].append(pattern)
    
    def _learn_text_patterns(self, content: Dict[str, Any], content_type: str) -> None:
        """Learn text patterns from content fields."""
        text_fields = self._extract_text_fields(content)
        
        for field_name, text in text_fields.items():
            if isinstance(text, str) and len(text) > 10:
                # Learn n-grams
                self._learn_ngrams(text)
                
                # Learn common phrases
                self._learn_phrases(text, f"{content_type}_{field_name}")
                
                # Learn sentence patterns
                self._learn_sentence_patterns(text, content_type)
    
    def _learn_ngrams(self, text: str) -> None:
        """Learn n-grams from text for generation."""
        # Tokenize
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Unigrams
        self.unigrams.update(words)
        
        # Bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            self.bigrams[bigram] += 1
        
        # Trigrams
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            self.trigrams[trigram] += 1
    
    def _learn_phrases(self, text: str, category: str) -> None:
        """Learn common phrases from text."""
        # Extract common phrase patterns
        phrase_patterns = [
            (r'the [a-z]+ [a-z]+', 'noun_phrase'),
            (r'[a-z]+ly [a-z]+', 'adverb_phrase'),
            (r'[a-z]+ion of [a-z]+', 'abstract_phrase'),
        ]
        
        for pattern, ptype in phrase_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches[:5]:  # Limit per category
                self._add_pattern(category, ptype, match)
    
    def _learn_sentence_patterns(self, text: str, content_type: str) -> None:
        """Learn sentence structure patterns."""
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue
            
            # Categorize by start/end
            words = sentence.split()
            if not words:
                continue
                
            start_word = words[0].lower()
            end_word = words[-1].lower()
            
            # Track sentence patterns
            pattern_key = f"{content_type}_sentence"
            self._add_pattern(pattern_key, "sentence_start", start_word)
            self._add_pattern(pattern_key, "sentence_end", end_word)
    
    def _learn_progression(self, content: Dict[str, Any], content_type: str) -> None:
        """Learn progression patterns (for linear content)."""
        if content_type == "quest" or content_type == "adventure":
            # Learn encounter/scene ordering
            locations = content.get('locations', [])
            encounters = content.get('encounters', [])
            
            if locations:
                # Learn typical location flow
                location_types = [loc.get('type', 'unknown') for loc in locations]
                self._add_pattern("progression", "location_flow", "->".join(location_types))
            
            if encounters:
                # Learn difficulty progression
                difficulties = [enc.get('difficulty', 'medium') for enc in encounters]
                self._add_pattern("progression", "difficulty_flow", "->".join(difficulties))
    
    def _extract_text_fields(self, content: Dict[str, Any]) -> Dict[str, str]:
        """Extract text fields from content for analysis."""
        text_fields = {}
        
        for key, value in content.items():
            if isinstance(value, str) and len(value) > 5:
                text_fields[key] = value
            elif isinstance(value, dict):
                # Recurse into nested dicts
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str) and len(sub_value) > 5:
                        text_fields[f"{key}_{sub_key}"] = sub_value
        
        return text_fields
    
    def _add_pattern(self, category: str, pattern_type: str, value: str) -> None:
        """Add or update a pattern."""
        pattern_name = f"{category}_{pattern_type}"
        existing = self._find_pattern(pattern_name, pattern_type)
        
        if existing:
            existing.frequency += 1
            if value not in existing.examples:
                existing.examples.append(value)
            existing.confidence = min(1.0, existing.frequency / 10)
        else:
            pattern = Pattern(
                name=pattern_name,
                pattern_type=pattern_type,
                frequency=1,
                examples=[value],
                confidence=0.1
            )
            self.patterns[pattern_type].append(pattern)
    
    def _find_pattern(self, name: str, pattern_type: str) -> Optional[Pattern]:
        """Find an existing pattern by name."""
        for pattern in self.patterns.get(pattern_type, []):
            if pattern.name == name:
                return pattern
        return None
    
    def _update_stats(self, content_type: str) -> None:
        """Update content statistics."""
        if content_type not in self.content_stats:
            self.content_stats[content_type] = {
                "count": 0,
                "avg_length": 0,
                "common_elements": Counter()
            }
        
        self.content_stats[content_type]["count"] += 1
    
    def generate_text(self, length: int = 50, seed_text: str = "") -> str:
        """
        Generate text using learned n-grams.
        
        Args:
            length: Target word count
            seed_text: Starting text
            
        Returns:
            Generated text
        """
        if not seed_text:
            # Start with common word
            if self.unigrams:
                seed_word = self.unigrams.most_common(1)[0][0]
                seed_text = seed_word.capitalize()
            else:
                return "The adventure begins."
        
        words = seed_text.lower().split()
        result = [seed_text]
        
        for _ in range(length):
            # Try trigram first
            if len(words) >= 2:
                key = f"{words[-2]} {words[-1]}"
                matches = [t for t in self.trigrams.keys() if t.startswith(key)]
                
                if matches:
                    next_word = random.choice(matches).split()[-1]
                    result.append(next_word)
                    words.append(next_word)
                    continue
            
            # Try bigram
            if len(words) >= 1:
                key = words[-1]
                matches = [b for b in self.bigrams.keys() if b.startswith(key)]
                
                if matches:
                    next_word = random.choice(matches).split()[-1]
                    result.append(next_word)
                    words.append(next_word)
                    continue
            
            # Fallback to common word
            if self.unigrams:
                next_word = random.choice(self.unigrams.most_common(20))[0]
                result.append(next_word)
                words.append(next_word)
        
        return ' '.join(result) + '.'
    
    def get_progression_pattern(self, content_type: str) -> List[str]:
        """
        Get learned progression pattern for content type.
        
        Returns:
            List of stages in order
        """
        patterns = self.patterns.get("progression", [])
        
        for pattern in patterns:
            if content_type in pattern.name:
                if pattern.examples:
                    # Return most common flow
                    return pattern.examples[0].split("->")
        
        # Default progression
        if content_type == "quest":
            return ["hook", "journey", "challenge", "climax", "resolution"]
        elif content_type == "adventure":
            return ["introduction", "exploration", "complication", "climax", "conclusion"]
        
        return ["beginning", "middle", "end"]
    
    def get_style_profile(self) -> Dict[str, Any]:
        """Get the learned style profile."""
        return {
            "common_words": self.unigrams.most_common(20),
            "common_phrases": self.bigrams.most_common(10),
            "patterns_count": sum(len(p) for p in self.patterns.values()),
            "content_stats": self.content_stats
        }
    
    def save_patterns(self) -> None:
        """Save learned patterns to file."""
        data = {
            "patterns": {
                k: [p.to_dict() for p in v] 
                for k, v in self.patterns.items()
            },
            "style_profile": self.get_style_profile(),
            "ngrams": {
                "unigrams": dict(self.unigrams.most_common(1000)),
                "bigrams": dict(self.bigrams.most_common(500)),
                "trigrams": dict(self.trigrams.most_common(200))
            }
        }
        
        filepath = self.memory_dir / "learned_patterns.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved patterns to {filepath}")
    
    def _load_patterns(self) -> None:
        """Load patterns from file."""
        filepath = self.memory_dir / "learned_patterns.json"
        
        if filepath.exists():
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Load patterns
            for pattern_type, patterns in data.get("patterns", {}).items():
                for p in patterns:
                    pattern = Pattern(
                        name=p["name"],
                        pattern_type=p["pattern_type"],
                        frequency=p.get("frequency", 0),
                        examples=p.get("examples", []),
                        structure=p.get("structure"),
                        confidence=p.get("confidence", 0)
                    )
                    self.patterns[pattern_type].append(pattern)
            
            # Load ngrams
            ngrams = data.get("ngrams", {})
            self.unigrams = Counter(ngrams.get("unigrams", {}))
            self.bigrams = Counter(ngrams.get("bigrams", {}))
            self.trigrams = Counter(ngrams.get("trigrams", {}))
            
            logger.info(f"Loaded patterns from {filepath}")
    
    def clear_patterns(self) -> None:
        """Clear all learned patterns."""
        self.patterns.clear()
        self.unigrams.clear()
        self.bigrams.clear()
        self.trigrams.clear()
        self.content_stats.clear()
        logger.info("Cleared all patterns")


# Import random at module level for generation
import random
