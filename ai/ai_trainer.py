#!/usr/bin/env python3
"""
AI Trainer Module

Train the AI on existing content to learn patterns and styles.
Processes quests, NPCs, encounters, and campaign data.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .pattern_learner import PatternLearner
from .sqlite_storage import SQLiteStorage

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class AITrainer:
    """Train AI on existing content."""
    
    def __init__(
        self,
        memory_dir: str = "ai_data",
        db_path: str = "ai_data/gm_campaign.db"
    ):
        self.pattern_learner = PatternLearner(memory_dir)
        self.storage = SQLiteStorage(db_path)
        self.training_stats = {
            "content_processed": 0,
            "patterns_learned": 0,
            "last_trained": None
        }
    
    def train_on_all_content(self) -> Dict[str, int]:
        """
        Train on all available content.
        
        Returns:
            Training statistics
        """
        logger.info("Starting full training...")
        
        stats = {
            "quests": 0,
            "npcs": 0,
            "encounters": 0,
            "characters": 0,
            "sessions": 0
        }
        
        # Train on generated content from storage
        content_types = ["quest", "adventure", "encounter", "npc", "character"]
        
        for content_type in content_types:
            content_list = self.storage.get_generated_content(content_type=content_type)
            
            for content in content_list:
                data = content.get("data", {})
                if isinstance(data, dict):
                    self.pattern_learner.learn_from_content(data, content_type)
                    stats[content_type + "s"] = stats.get(content_type + "s", 0) + 1
        
        # Train on campaign sessions
        sessions = self.storage.get_campaign_sessions("")
        for session in sessions:
            summary = session.get("summary", "")
            if summary:
                self._train_on_text(summary, "session_summary")
                stats["sessions"] += 1
        
        # Save learned patterns
        self.pattern_learner.save_patterns()
        
        # Update stats
        self.training_stats["content_processed"] = sum(stats.values())
        self.training_stats["patterns_learned"] = len(self.pattern_learner.patterns)
        self.training_stats["last_trained"] = str(Path(__file__).parent.parent / "ai_data")
        
        logger.info(f"Training complete: {self.training_stats['content_processed']} items processed")
        return stats
    
    def train_on_file(self, filepath: str, content_type: str) -> int:
        """
        Train on content from a file.
        
        Args:
            filepath: Path to JSON file
            content_type: Type of content
            
        Returns:
            Number of items trained
        """
        path = Path(filepath)
        if not path.exists():
            logger.error(f"File not found: {filepath}")
            return 0
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        count = 0
        
        # Handle list or single item
        items = data if isinstance(data, list) else [data]
        
        for item in items:
            if isinstance(item, dict):
                self.pattern_learner.learn_from_content(item, content_type)
                count += 1
        
        # Save patterns
        self.pattern_learner.save_patterns()
        
        logger.info(f"Trained on {count} {content_type} items from {filepath}")
        return count
    
    def train_on_text(self, text: str, category: str) -> None:
        """
        Train on raw text.
        
        Args:
            text: Text to learn from
            category: Category for patterns
        """
        # Create pseudo-content for text learning
        content = {
            "description": text,
            "name": f"{category}_sample"
        }
        self.pattern_learner.learn_from_content(content, category)
    
    def train_on_campaign_memory(self, memory_data: Dict[str, Any]) -> None:
        """
        Train on campaign memory data.
        
        Args:
            memory_data: Campaign memory dict
        """
        # Learn from recent events
        for event in memory_data.get("recent_events", []):
            if isinstance(event, dict):
                description = event.get("description", "")
                if description:
                    self._train_on_text(description, "event")
        
        # Learn from session history
        for session in memory_data.get("session_history", []):
            summary = session.get("summary", "")
            if summary:
                self._train_on_text(summary, "session")
        
        # Learn from DM notes
        dm_notes = memory_data.get("dm_notes", "")
        if dm_notes:
            self._train_on_text(dm_notes, "dm_notes")
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status."""
        return {
            **self.training_stats,
            "pattern_types": list(self.pattern_learner.patterns.keys()),
            "style_profile": self.pattern_learner.get_style_profile()
        }
    
    def reset_training(self) -> None:
        """Reset all training data."""
        self.pattern_learner.clear_patterns()
        logger.info("Training data reset")
    
    def export_training_data(self, filepath: str) -> bool:
        """Export training data to file."""
        try:
            data = {
                "stats": self.training_stats,
                "patterns": {
                    k: [p.to_dict() for p in v]
                    for k, v in self.pattern_learner.patterns.items()
                },
                "ngrams": {
                    "unigrams": dict(self.pattern_learner.unigrams.most_common(1000)),
                    "bigrams": dict(self.pattern_learner.bigrams.most_common(500)),
                    "trigrams": dict(self.pattern_learner.trigrams.most_common(200))
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported training data to {filepath}")
            return True
        except IOError as e:
            logger.error(f"Failed to export: {e}")
            return False
    
    def import_training_data(self, filepath: str) -> bool:
        """Import training data from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Restore patterns
            for pattern_type, patterns in data.get("patterns", {}).items():
                for p in patterns:
                    # Pattern restoration handled by pattern_learner
                    pass
            
            # Restore ngrams
            ngrams = data.get("ngrams", {})
            self.pattern_learner.unigrams.clear()
            self.pattern_learner.bigrams.clear()
            self.pattern_learner.trigrams.clear()
            
            for word, count in ngrams.get("unigrams", {}).items():
                for _ in range(min(count, 100)):  # Limit to prevent overflow
                    self.pattern_learner.unigrams[word] += 1
            
            for phrase, count in ngrams.get("bigrams", {}).items():
                for _ in range(min(count, 50)):
                    self.pattern_learner.bigrams[phrase] += 1
            
            for phrase, count in ngrams.get("trigrams", {}).items():
                for _ in range(min(count, 20)):
                    self.pattern_learner.trigrams[phrase] += 1
            
            # Restore stats
            self.training_stats = data.get("stats", self.training_stats)
            
            logger.info(f"Imported training data from {filepath}")
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to import: {e}")
            return False
    
    def generate_sample(self, content_type: str, length: int = 50) -> str:
        """
        Generate sample text based on training.
        
        Args:
            content_type: Type of content to generate
            length: Target word count
            
        Returns:
            Generated text sample
        """
        return self.pattern_learner.generate_text(length)
    
    def get_learned_progression(self, content_type: str) -> List[str]:
        """
        Get learned progression pattern.
        
        Args:
            content_type: Type of content
            
        Returns:
            List of stages in order
        """
        return self.pattern_learner.get_progression_pattern(content_type)
    
    def __del__(self):
        """Cleanup."""
        self.storage.close()
