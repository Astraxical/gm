#!/usr/bin/env python3
"""
DnD GM Toolkit - AI Module

Homemade text-based AI for pattern learning and linear content generation.
No external APIs - completely self-contained and trainable.

Features:
- Pattern-based content generation
- Linear/progressive content (beginner-friendly)
- JSON memory for short-term state
- SQLite for long-term storage
- Choice-based story continuation
"""

from .pattern_learner import PatternLearner
from .linear_generator import LinearContentGenerator
from .campaign_memory import CampaignMemory
from .sqlite_storage import SQLiteStorage
from .choice_engine import ChoiceEngine
from .ai_trainer import AITrainer

__all__ = [
    'PatternLearner',
    'LinearContentGenerator',
    'CampaignMemory',
    'SQLiteStorage',
    'ChoiceEngine',
    'AITrainer',
]
