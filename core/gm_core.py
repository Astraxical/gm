#!/usr/bin/env python3
"""
DnD GM Toolkit - Core Module

Shared utilities, base classes, and common components for all GM tools.
Follows DRY (Don't Repeat Yourself) principles.

Features:
- Shared logging setup
- Cached JSON loading
- Base generator class
- Base tracker class
- Shared CLI components
- Common export functions
"""

import json
import logging
import random
import argparse
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, TypeVar, Generic
from dataclasses import dataclass, asdict

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_DATA_DIR = Path(__file__).parent / "data"

# D&D Standard Tables
DIFFICULTY_MODIFIERS = {
    "easy": 0.5,
    "medium": 1.0,
    "hard": 1.5,
    "deadly": 2.0
}

RARITY_PRICES = {
    "common": (50, 100),
    "uncommon": (100, 500),
    "rare": (500, 5000),
    "very_rare": (5000, 50000),
    "legendary": (50000, 500000)
}

CR_XP_TABLE = {
    0: 0, 0.125: 10, 0.25: 50, 0.5: 100, 1: 200, 2: 450,
    3: 700, 4: 1100, 5: 1800, 6: 2300, 7: 2900, 8: 3900,
    9: 5000, 10: 5900, 11: 7200, 12: 8400, 13: 10000,
    14: 11500, 15: 13000, 16: 15000, 17: 18000, 18: 20000,
    19: 22000, 20: 25000, 21: 28000, 22: 31000, 23: 34000,
    24: 37000, 25: 40000, 26: 43000, 27: 46000, 28: 49000,
    29: 52000, 30: 55000
}

CONDITIONS_LIST = [
    "blinded", "charmed", "deafened", "frightened", "grappled",
    "incapacitated", "invisible", "paralyzed", "petrified", "poisoned",
    "prone", "restrained", "stunned", "unconscious", "exhaustion"
]

DICE = {
    "d4": 4, "d6": 6, "d8": 8, "d10": 10, "d12": 12, "d20": 20, "d100": 100
}

# =============================================================================
# LOGGING
# =============================================================================


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with standard formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Only add handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# Create default logger for this module
logger = setup_logger(__name__)

# =============================================================================
# CACHED DATA LOADING
# =============================================================================


@lru_cache(maxsize=16)
def load_json_data(data_dir: str, filename: str) -> Dict[str, Any]:
    """
    Load JSON data with LRU caching.
    
    Args:
        data_dir: Directory containing data files (as string for caching)
        filename: Name of the JSON file
        
    Returns:
        Dict with loaded data or empty dict on error
    """
    filepath = Path(data_dir) / filename
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {filename}: {e}")
    return {}


def load_json_file(filepath: str) -> Dict[str, Any]:
    """
    Load a JSON file without caching (for one-off loads).
    
    Args:
        filepath: Full path to JSON file
        
    Returns:
        Dict with loaded data or empty dict on error
    """
    path = Path(filepath)
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {filepath}: {e}")
    return {}


# =============================================================================
# RANDOM/SEED MANAGEMENT
# =============================================================================


def set_seed(seed: Optional[int]) -> None:
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Random seed value
    """
    if seed is not None:
        random.seed(seed)


def roll_dice(dice: str, modifier: int = 0, advantage: bool = False, 
              disadvantage: bool = False) -> int:
    """
    Roll dice with optional modifier and advantage/disadvantage.
    
    Args:
        dice: Dice notation (e.g., "d20", "2d6")
        modifier: Modifier to add
        advantage: Roll twice, take higher
        disadvantage: Roll twice, take lower
        
    Returns:
        Roll result
    """
    if 'd' not in dice:
        return int(dice) + modifier
    
    parts = dice.split('d')
    num_dice = int(parts[0]) if parts[0] else 1
    die_size = int(parts[1])
    
    if die_size not in DICE.values():
        return 0
    
    if advantage:
        roll1 = sum(random.randint(1, die_size) for _ in range(num_dice))
        roll2 = sum(random.randint(1, die_size) for _ in range(num_dice))
        return max(roll1, roll2) + modifier
    elif disadvantage:
        roll1 = sum(random.randint(1, die_size) for _ in range(num_dice))
        roll2 = sum(random.randint(1, die_size) for _ in range(num_dice))
        return min(roll1, roll2) + modifier
    else:
        return sum(random.randint(1, die_size) for _ in range(num_dice)) + modifier


def weighted_choice(items: List[Any], weights: Optional[List[float]] = None) -> Any:
    """
    Select item with weighted probability.
    
    Args:
        items: List of items to choose from
        weights: Optional weights for each item
        
    Returns:
        Selected item
    """
    if not items:
        return None
    if weights is None:
        return random.choice(items)
    return random.choices(items, weights=weights, k=1)[0]


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================


def export_to_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> bool:
    """
    Export data to JSON file.
    
    Args:
        data: Data to export
        filepath: Output file path
        indent: JSON indentation level
        
    Returns:
        True if successful
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=indent)
        logger.info(f"Exported to {filepath}")
        return True
    except IOError as e:
        logger.error(f"Failed to export to {filepath}: {e}")
        return False


def export_to_markdown(content: str, filepath: str) -> bool:
    """
    Export content to Markdown file.
    
    Args:
        content: Markdown content
        filepath: Output file path
        
    Returns:
        True if successful
    """
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        logger.info(f"Exported to {filepath}")
        return True
    except IOError as e:
        logger.error(f"Failed to export to {filepath}: {e}")
        return False


def export_to_csv(rows: List[List[Any]], filepath: str, 
                  headers: Optional[List[str]] = None) -> bool:
    """
    Export data to CSV file.
    
    Args:
        rows: List of rows (each row is a list of values)
        filepath: Output file path
        headers: Optional header row
        
    Returns:
        True if successful
    """
    try:
        import csv
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            writer.writerows(rows)
        logger.info(f"Exported to {filepath}")
        return True
    except IOError as e:
        logger.error(f"Failed to export to {filepath}: {e}")
        return False


# =============================================================================
# DATA CLASS MIXINS
# =============================================================================


class ToDictMixin:
    """Mixin to add to_dict() method to dataclasses."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert dataclass to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class TimestampMixin:
    """Mixin to add timestamp tracking."""
    
    created: str
    updated: str
    
    def _set_timestamps(self) -> None:
        """Set created and updated timestamps."""
        now = datetime.now(timezone.utc).isoformat()
        if not hasattr(self, 'created') or not self.created:
            self.created = now
        self.updated = now
    
    def touch(self) -> None:
        """Update the timestamp."""
        self.updated = datetime.now(timezone.utc).isoformat()


# =============================================================================
# BASE GENERATOR CLASS
# =============================================================================


T = TypeVar('T')


class BaseGenerator(Generic[T]):
    """
    Base class for all generators.
    
    Provides shared functionality:
    - Seed management
    - Data directory handling
    - Cached data loading
    - Export methods
    """
    
    def __init__(self, data_dir: Optional[str] = None, 
                 seed: Optional[int] = None,
                 logger_name: Optional[str] = None):
        """
        Initialize base generator.
        
        Args:
            data_dir: Directory for data files
            seed: Random seed for reproducibility
            logger_name: Name for logger
        """
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.seed = seed
        self.logger = setup_logger(logger_name or self.__class__.__name__)
        
        if seed is not None:
            set_seed(seed)
            self.logger.debug(f"Random seed set to {seed}")
    
    def load_data(self, filename: str) -> Dict[str, Any]:
        """
        Load JSON data from data directory.
        
        Args:
            filename: Name of JSON file
            
        Returns:
            Loaded data or empty dict
        """
        return load_json_data(str(self.data_dir), filename)
    
    def export(self, data: Dict[str, Any], filepath: str) -> bool:
        """
        Export data to JSON file.
        
        Args:
            data: Data to export
            filepath: Output file path
            
        Returns:
            True if successful
        """
        return export_to_json(data, filepath)
    
    def generate(self, *args, **kwargs) -> T:
        """
        Generate content. Override in subclass.
        
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement generate()")


# =============================================================================
# BASE TRACKER CLASS
# =============================================================================


class BaseTracker:
    """
    Base class for all trackers.
    
    Provides shared functionality:
    - State management
    - Timestamp tracking
    - Export methods
    """
    
    def __init__(self, name: str = "Tracker", 
                 data_dir: Optional[str] = None,
                 logger_name: Optional[str] = None):
        """
        Initialize base tracker.
        
        Args:
            name: Tracker name
            data_dir: Directory for data files
            logger_name: Name for logger
        """
        self.name = name
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.logger = setup_logger(logger_name or self.__class__.__name__)
        self.created = datetime.now(timezone.utc).isoformat()
        self.last_updated = self.created
    
    def _update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.last_updated = datetime.now(timezone.utc).isoformat()
    
    def export(self, data: Dict[str, Any], filepath: str) -> bool:
        """
        Export tracker data to JSON file.
        
        Args:
            data: Data to export
            filepath: Output file path
            
        Returns:
            True if successful
        """
        return export_to_json(data, filepath)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get tracker summary. Override in subclass.
        
        Returns:
            Summary dict
        """
        return {
            "name": self.name,
            "created": self.created,
            "last_updated": self.last_updated
        }


# =============================================================================
# SHARED CLI COMPONENTS
# =============================================================================


def create_base_parser(description: str, epilog: str = "") -> argparse.ArgumentParser:
    """
    Create base argument parser with common arguments.
    
    Args:
        description: Parser description
        epilog: Optional epilog text
        
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add common arguments
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--data-dir", type=str, help="Data directory path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument("--export", type=str, help="Export to file")
    parser.add_argument("--export-format", choices=["json", "md", "csv"], 
                        default="json", help="Export format")
    
    return parser


def add_output_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add common output arguments to parser.
    
    Args:
        parser: ArgumentParser to modify
    """
    parser.add_argument("-o", "--output", type=str, help="Output file path")
    parser.add_argument("--format", choices=["text", "json", "markdown"], 
                        default="text", help="Output format")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")


def add_difficulty_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add difficulty-related arguments to parser.
    
    Args:
        parser: ArgumentParser to modify
    """
    parser.add_argument("-d", "--difficulty", default="medium",
                        choices=["easy", "medium", "hard", "deadly"],
                        help="Difficulty level")
    parser.add_argument("--level", type=int, default=1, help="Character/encounter level")
    parser.add_argument("--party-size", type=int, default=4, help="Party size")
    parser.add_argument("--party-level", type=int, default=1, help="Average party level")


def handle_common_args(args: argparse.Namespace, generator: BaseGenerator) -> None:
    """
    Handle common arguments after parsing.
    
    Args:
        args: Parsed arguments
        generator: Generator instance to configure
    """
    if hasattr(args, 'seed') and args.seed is not None:
        set_seed(args.seed)
    
    if hasattr(args, 'verbose') and args.verbose:
        generator.logger.setLevel(logging.DEBUG)
    elif hasattr(args, 'quiet') and args.quiet:
        generator.logger.setLevel(logging.WARNING)


# =============================================================================
# FORMATTING UTILITIES
# =============================================================================


class TextFormatter:
    """Shared text formatting utilities."""
    
    # ANSI color codes
    COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
        "bold": "\033[1m",
    }
    
    @classmethod
    def colorize(cls, text: str, color: str, use_color: bool = True) -> str:
        """
        Add color to text.
        
        Args:
            text: Text to colorize
            color: Color name
            use_color: Whether to apply color
            
        Returns:
            Colorized text
        """
        if not use_color or color not in cls.COLORS:
            return text
        return f"{cls.COLORS[color]}{text}{cls.COLORS['reset']}"
    
    @classmethod
    def create_bar(cls, current: int, maximum: int, width: int = 20,
                   fill_char: str = "█", empty_char: str = "░") -> str:
        """
        Create a visual progress bar.
        
        Args:
            current: Current value
            maximum: Maximum value
            width: Bar width in characters
            fill_char: Character for filled portion
            empty_char: Character for empty portion
            
        Returns:
            Progress bar string
        """
        if maximum <= 0:
            return empty_char * width
        
        filled = int((current / maximum) * width)
        empty = width - filled
        return fill_char * filled + empty_char * empty
    
    @classmethod
    def format_table(cls, rows: List[List[str]], headers: Optional[List[str]] = None,
                     padding: int = 2) -> str:
        """
        Format data as ASCII table.
        
        Args:
            rows: List of rows (each row is list of strings)
            headers: Optional header row
            padding: Column padding
            
        Returns:
            Formatted table string
        """
        if not rows:
            return ""
        
        # Calculate column widths
        all_rows = [headers] + rows if headers else rows
        col_widths = [max(len(str(cell)) for cell in col) 
                      for col in zip(*all_rows)]
        
        lines = []
        
        # Header
        if headers:
            header_line = " " * padding
            for i, header in enumerate(headers):
                header_line += str(header).ljust(col_widths[i] + padding)
            lines.append(header_line)
            lines.append("-" * len(header_line))
        
        # Data rows
        for row in rows:
            line = " " * padding
            for i, cell in enumerate(row):
                line += str(cell).ljust(col_widths[i] + padding)
            lines.append(line)
        
        return "\n".join(lines)
    
    @classmethod
    def wrap_text(cls, text: str, width: int = 80, indent: str = "") -> str:
        """
        Wrap text to specified width.
        
        Args:
            text: Text to wrap
            width: Maximum line width
            indent: String to indent each line
            
        Returns:
            Wrapped text
        """
        words = text.split()
        lines = []
        current_line = indent
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                current_line += (" " if current_line != indent else "") + word
            else:
                if current_line != indent:
                    lines.append(current_line)
                current_line = indent + word
        
        if current_line != indent:
            lines.append(current_line)
        
        return "\n".join(lines)


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================


class Validator:
    """Shared validation utilities."""
    
    @staticmethod
    def validate_range(value: Any, min_val: Any = None, max_val: Any = None,
                       name: str = "value") -> bool:
        """
        Validate value is within range.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            name: Name for error message
            
        Returns:
            True if valid
        """
        if min_val is not None and value < min_val:
            logger.error(f"{name} must be at least {min_val}")
            return False
        if max_val is not None and value > max_val:
            logger.error(f"{name} must be at most {max_val}")
            return False
        return True
    
    @staticmethod
    def validate_choice(value: Any, choices: List[Any], 
                        name: str = "value") -> bool:
        """
        Validate value is in allowed choices.
        
        Args:
            value: Value to validate
            choices: Allowed values
            name: Name for error message
            
        Returns:
            True if valid
        """
        if value not in choices:
            logger.error(f"{name} must be one of: {', '.join(map(str, choices))}")
            return False
        return True
    
    @staticmethod
    def validate_required(data: Dict[str, Any], required_fields: List[str],
                          name: str = "data") -> bool:
        """
        Validate required fields are present.
        
        Args:
            data: Data dict to validate
            required_fields: List of required field names
            name: Name for error message
            
        Returns:
            True if valid
        """
        missing = [f for f in required_fields if f not in data]
        if missing:
            logger.error(f"{name} missing required fields: {', '.join(missing)}")
            return False
        return True


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Constants
    'DEFAULT_DATA_DIR',
    'DIFFICULTY_MODIFIERS',
    'RARITY_PRICES',
    'CR_XP_TABLE',
    'CONDITIONS_LIST',
    'DICE',
    
    # Logging
    'setup_logger',
    
    # Data loading
    'load_json_data',
    'load_json_file',
    
    # Random
    'set_seed',
    'roll_dice',
    'weighted_choice',
    
    # Export
    'export_to_json',
    'export_to_markdown',
    'export_to_csv',
    
    # Mixins
    'ToDictMixin',
    'TimestampMixin',
    
    # Base classes
    'BaseGenerator',
    'BaseTracker',
    
    # CLI
    'create_base_parser',
    'add_output_arguments',
    'add_difficulty_arguments',
    'handle_common_args',
    
    # Formatting
    'TextFormatter',
    
    # Validation
    'Validator',
]
