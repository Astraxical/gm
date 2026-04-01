#!/usr/bin/env python3
"""
Linear Content Generator

Generate content with proper progression - beginners won't face bosses immediately!
Creates structured, escalating content with clear stages and choices.

Features:
- Progressive difficulty scaling
- Stage-based content generation
- Choice points for continuation
- Beginner-friendly pacing
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class DifficultyLevel(str, Enum):
    """Difficulty levels for progressive content."""
    TUTORIAL = "tutorial"      # Very easy, learning focused
    EASY = "easy"              # Simple challenges
    MODERATE = "moderate"      # Standard challenges
    CHALLENGING = "challenging" # Hard challenges
    BOSS = "boss"              # Major confrontation
    EPIC = "epic"              # Final challenge


@dataclass
class ContentStage:
    """A single stage in linear content."""
    stage_number: int
    name: str
    difficulty: str
    description: str
    encounters: List[Dict[str, Any]] = field(default_factory=list)
    npcs: List[Dict[str, Any]] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    choices: List[Dict[str, Any]] = field(default_factory=list)
    required: bool = True  # Must complete this stage
    min_party_level: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_number": self.stage_number,
            "name": self.name,
            "difficulty": self.difficulty,
            "description": self.description,
            "encounters": self.encounters,
            "npcs": self.npcs,
            "locations": self.locations,
            "choices": self.choices,
            "required": self.required,
            "min_party_level": self.min_party_level
        }


@dataclass
class LinearContent:
    """Complete linear content with stages."""
    title: str
    content_type: str  # quest, adventure, campaign_arc
    theme: str
    total_stages: int
    current_stage: int = 0
    stages: List[ContentStage] = field(default_factory=list)
    party_level_range: Tuple[int, int] = (1, 5)
    estimated_sessions: int = 3
    completed: bool = False
    choices_made: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content_type": self.content_type,
            "theme": self.theme,
            "total_stages": self.total_stages,
            "current_stage": self.current_stage,
            "stages": [s.to_dict() for s in self.stages],
            "party_level_range": self.party_level_range,
            "estimated_sessions": self.estimated_sessions,
            "completed": self.completed,
            "choices_made": self.choices_made
        }


class LinearContentGenerator:
    """Generate linear, progressive content."""
    
    # Stage templates by content type
    STAGE_TEMPLATES = {
        "quest": [
            {"name": "The Hook", "difficulty": DifficultyLevel.TUTORIAL, "description": "The adventure begins"},
            {"name": "First Steps", "difficulty": DifficultyLevel.EASY, "description": "Initial challenges"},
            {"name": "Gathering Information", "difficulty": DifficultyLevel.EASY, "description": "Learn more about the quest"},
            {"name": "The Journey", "difficulty": DifficultyLevel.MODERATE, "description": "Travel to the objective"},
            {"name": "Complications", "difficulty": DifficultyLevel.MODERATE, "description": "Unexpected obstacles"},
            {"name": "The Challenge", "difficulty": DifficultyLevel.CHALLENGING, "description": "Major obstacle"},
            {"name": "The Confrontation", "difficulty": DifficultyLevel.BOSS, "description": "Final encounter"},
            {"name": "Resolution", "difficulty": DifficultyLevel.EASY, "description": "Wrap up and rewards"},
        ],
        "adventure": [
            {"name": "Introduction", "difficulty": DifficultyLevel.TUTORIAL, "description": "Set the scene"},
            {"name": "First Encounter", "difficulty": DifficultyLevel.EASY, "description": "Initial challenge"},
            {"name": "Exploration", "difficulty": DifficultyLevel.EASY, "description": "Discover the area"},
            {"name": "Rising Action", "difficulty": DifficultyLevel.MODERATE, "description": "Tension builds"},
            {"name": "Complication", "difficulty": DifficultyLevel.MODERATE, "description": "Things get worse"},
            {"name": "Low Point", "difficulty": DifficultyLevel.CHALLENGING, "description": "Major setback"},
            {"name": "Climax", "difficulty": DifficultyLevel.BOSS, "description": "Final confrontation"},
            {"name": "Conclusion", "difficulty": DifficultyLevel.EASY, "description": "Resolution"},
        ],
        "campaign_arc": [
            {"name": "Session 1: Introduction", "difficulty": DifficultyLevel.TUTORIAL},
            {"name": "Session 2: First Clues", "difficulty": DifficultyLevel.EASY},
            {"name": "Session 3: Rising Threat", "difficulty": DifficultyLevel.MODERATE},
            {"name": "Session 4: Complications", "difficulty": DifficultyLevel.MODERATE},
            {"name": "Session 5: Major Revelation", "difficulty": DifficultyLevel.CHALLENGING},
            {"name": "Session 6: Preparation", "difficulty": DifficultyLevel.MODERATE},
            {"name": "Session 7: The Battle", "difficulty": DifficultyLevel.BOSS},
            {"name": "Session 8: Aftermath", "difficulty": DifficultyLevel.EASY},
        ]
    }
    
    # Encounter templates by difficulty
    ENCOUNTER_TEMPLATES = {
        DifficultyLevel.TUTORIAL: [
            {"type": "social", "cr_range": (0, 0.5), "count": 1, "description": "Simple interaction"},
            {"type": "exploration", "cr_range": (0, 0.25), "count": 1, "description": "Easy obstacle"},
        ],
        DifficultyLevel.EASY: [
            {"type": "combat", "cr_range": (0.25, 1), "count": 2, "description": "Minor enemies"},
            {"type": "puzzle", "cr_range": (0, 0), "count": 1, "description": "Simple puzzle"},
        ],
        DifficultyLevel.MODERATE: [
            {"type": "combat", "cr_range": (1, 3), "count": 3, "description": "Challenging enemies"},
            {"type": "trap", "cr_range": (1, 2), "count": 1, "description": "Dangerous trap"},
        ],
        DifficultyLevel.CHALLENGING: [
            {"type": "combat", "cr_range": (3, 5), "count": 4, "description": " Tough enemies + leader"},
            {"type": "complex_puzzle", "cr_range": (2, 4), "count": 1, "description": "Multi-stage challenge"},
        ],
        DifficultyLevel.BOSS: [
            {"type": "boss", "cr_range": (5, 8), "count": 1, "description": "Major boss encounter"},
            {"type": "boss_with_minions", "cr_range": (4, 6), "count": 1, "description": "Boss + minions"},
        ],
        DifficultyLevel.EPIC: [
            {"type": "epic_boss", "cr_range": (10, 15), "count": 1, "description": "Campaign finale"},
        ]
    }
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        
        self.current_content: Optional[LinearContent] = None
    
    def generate_quest(
        self,
        theme: str = "rescue",
        party_level: int = 1,
        num_stages: int = 5,
        title: str = ""
    ) -> LinearContent:
        """
        Generate a linear quest with proper progression.
        
        Args:
            theme: Quest theme (rescue, hunt, retrieve, etc.)
            party_level: Starting party level
            num_stages: Number of stages (3-8)
            title: Quest title
            
        Returns:
            LinearContent quest
        """
        num_stages = max(3, min(8, num_stages))
        
        if not title:
            title = self._generate_title(theme)
        
        content = LinearContent(
            title=title,
            content_type="quest",
            theme=theme,
            total_stages=num_stages,
            party_level_range=(party_level, party_level + num_stages // 2)
        )
        
        # Get stage templates
        templates = self.STAGE_TEMPLATES["quest"][:num_stages]
        
        # Generate each stage
        for i, template in enumerate(templates):
            stage = self._generate_stage(
                stage_number=i + 1,
                template=template,
                theme=theme,
                party_level=party_level + (i // 2)
            )
            content.stages.append(stage)
        
        self.current_content = content
        logger.info(f"Generated quest: {title} ({num_stages} stages)")
        return content
    
    def generate_adventure(
        self,
        theme: str = "dungeon",
        party_level: int = 1,
        num_stages: int = 6,
        title: str = ""
    ) -> LinearContent:
        """Generate a linear adventure."""
        num_stages = max(4, min(8, num_stages))
        
        if not title:
            title = self._generate_title(theme)
        
        content = LinearContent(
            title=title,
            content_type="adventure",
            theme=theme,
            total_stages=num_stages,
            party_level_range=(party_level, party_level + 2),
            estimated_sessions=num_stages // 2
        )
        
        templates = self.STAGE_TEMPLATES["adventure"][:num_stages]
        
        for i, template in enumerate(templates):
            stage = self._generate_stage(
                stage_number=i + 1,
                template=template,
                theme=theme,
                party_level=party_level + (i // 3)
            )
            content.stages.append(stage)
        
        self.current_content = content
        logger.info(f"Generated adventure: {title}")
        return content
    
    def _generate_stage(
        self,
        stage_number: int,
        template: Dict[str, Any],
        theme: str,
        party_level: int
    ) -> ContentStage:
        """Generate a single stage."""
        difficulty = template.get("difficulty", DifficultyLevel.EASY)
        
        stage = ContentStage(
            stage_number=stage_number,
            name=template.get("name", f"Stage {stage_number}"),
            difficulty=difficulty.value,
            description=template.get("description", "Adventure continues"),
            min_party_level=party_level
        )
        
        # Generate encounters for this stage
        stage.encounters = self._generate_encounters(difficulty, party_level, theme)
        
        # Generate NPCs if appropriate
        if stage_number == 1 or difficulty in [DifficultyLevel.EASY, DifficultyLevel.MODERATE]:
            stage.npcs = self._generate_npcs(difficulty, theme)
        
        # Generate locations
        stage.locations = self._generate_locations(difficulty, theme)
        
        # Generate choices (except for final stage)
        if stage_number < 6:  # Don't add choices to climax/resolution
            stage.choices = self._generate_choices(stage_number, theme)
        
        return stage
    
    def _generate_encounters(
        self,
        difficulty: DifficultyLevel,
        party_level: int,
        theme: str
    ) -> List[Dict[str, Any]]:
        """Generate encounters appropriate for difficulty."""
        templates = self.ENCOUNTER_TEMPLATES.get(difficulty, self.ENCOUNTER_TEMPLATES[DifficultyLevel.EASY])
        encounters = []
        
        for template in templates:
            cr_min, cr_max = template["cr_range"]
            
            encounter = {
                "type": template["type"],
                "description": template["description"],
                "count": template["count"],
                "cr": random.uniform(cr_min, min(cr_max, party_level + 1)),
                "enemies": self._generate_enemies(template["type"], cr_min, cr_max),
                "xp": self._calculate_xp(template["count"], cr_min, cr_max)
            }
            encounters.append(encounter)
        
        return encounters
    
    def _generate_enemies(self, encounter_type: str, cr_min: float, cr_max: float) -> List[str]:
        """Generate enemy names based on type and CR."""
        enemy_tables = {
            "combat": ["Goblin", "Orc", "Bandit", "Skeleton", "Wolf", "Ogre", "Troll"],
            "boss": ["Dragon Wyrmling", "Ogre Mage", "Troll King", "Bandit Captain", "Lich"],
            "social": ["Merchant", "Guard", "Noble", "Priest", "Scholar"],
        }
        
        table = enemy_tables.get(encounter_type, enemy_tables["combat"])
        return [random.choice(table)]
    
    def _calculate_xp(self, count: int, cr_min: float, cr_max: float) -> int:
        """Calculate XP for encounter."""
        cr_xp = {
            0: 0, 0.125: 10, 0.25: 50, 0.5: 100, 1: 200, 2: 450,
            3: 700, 4: 1100, 5: 1800, 6: 2300, 7: 2900, 8: 3900
        }
        
        avg_cr = (cr_min + cr_max) / 2
        base_xp = cr_xp.get(int(avg_cr), cr_xp.get(1, 200))
        return base_xp * count
    
    def _generate_npcs(self, difficulty: DifficultyLevel, theme: str) -> List[Dict[str, Any]]:
        """Generate NPCs for a stage."""
        npcs = []
        
        if difficulty == DifficultyLevel.TUTORIAL:
            npcs.append({
                "role": "Quest Giver",
                "disposition": "friendly",
                "information": "Basic quest information"
            })
        elif difficulty == DifficultyLevel.EASY:
            npcs.append({
                "role": "Informant",
                "disposition": "neutral",
                "information": "Helpful clue"
            })
        elif difficulty == DifficultyLevel.MODERATE:
            npcs.append({
                "role": "Ally",
                "disposition": "friendly",
                "information": "Tactical information",
                "can_help": True
            })
        
        return npcs
    
    def _generate_locations(self, difficulty: DifficultyLevel, theme: str) -> List[Dict[str, Any]]:
        """Generate locations for a stage."""
        location_tables = {
            "rescue": ["Village", "Bandit Camp", "Dungeon", "Tower"],
            "hunt": ["Forest", "Cave", "Mountain Pass", "Swamp"],
            "retrieve": ["Ruins", "Tomb", "Dragon Lair", "Wizard Tower"],
            "dungeon": ["Entrance Hall", "Corridor", "Chamber", "Treasure Room"],
        }
        
        table = location_tables.get(theme, location_tables["dungeon"])
        
        return [{
            "name": random.choice(table),
            "type": "location",
            "features": self._generate_location_features(difficulty)
        }]
    
    def _generate_location_features(self, difficulty: DifficultyLevel) -> List[str]:
        """Generate location features."""
        features = {
            DifficultyLevel.TUTORIAL: ["Clear path", "Visible objective"],
            DifficultyLevel.EASY: ["Some cover", "Simple layout"],
            DifficultyLevel.MODERATE: ["Multiple levels", "Hidden areas"],
            DifficultyLevel.CHALLENGING: ["Traps", "Complex terrain"],
            DifficultyLevel.BOSS: ["Lair actions", "Multiple phases"],
        }
        return features.get(difficulty, features[DifficultyLevel.EASY])
    
    def _generate_choices(self, stage_number: int, theme: str) -> List[Dict[str, Any]]:
        """Generate choice points for branching."""
        choice_templates = [
            {
                "question": "How do you proceed?",
                "options": [
                    {"text": "Take the direct route", "consequence": "Faster but more dangerous"},
                    {"text": "Take the safe route", "consequence": "Slower but safer"},
                    {"text": "Gather more information first", "consequence": "Gain advantage later"}
                ]
            },
            {
                "question": "How do you handle the situation?",
                "options": [
                    {"text": "Negotiate", "consequence": "May avoid combat"},
                    {"text": "Fight", "consequence": "Immediate resolution"},
                    {"text": "Stealth", "consequence": "Avoid detection"}
                ]
            },
        ]
        
        return [random.choice(choice_templates)]
    
    def _generate_title(self, theme: str) -> str:
        """Generate a title based on theme."""
        prefixes = ["The", "A", "An", "The Quest for", "The Mystery of"]
        theme_words = {
            "rescue": ["Lost", "Missing", "Captive", "Stolen"],
            "hunt": ["Beast", "Monster", "Predator", "Threat"],
            "retrieve": ["Artifact", "Relic", "Treasure", "Secret"],
            "dungeon": ["Depths", "Labyrinth", "Crypt", "Vault"],
        }
        
        prefix = random.choice(prefixes)
        word = random.choice(theme_words.get(theme, ["Adventure"]))
        return f"{prefix} {word} {'Quest' if theme in theme_words else ''}"
    
    def get_current_stage(self) -> Optional[ContentStage]:
        """Get the current stage of active content."""
        if not self.current_content:
            return None
        
        if self.current_content.current_stage < len(self.current_content.stages):
            return self.current_content.stages[self.current_content.current_stage]
        return None
    
    def advance_stage(self, choice_index: Optional[int] = None) -> Optional[ContentStage]:
        """Advance to the next stage."""
        if not self.current_content:
            return None
        
        # Record choice if made
        if choice_index is not None:
            current = self.get_current_stage()
            if current and current.choices:
                self.current_content.choices_made.append({
                    "stage": self.current_content.current_stage,
                    "choice_index": choice_index,
                    "choice": current.choices[0]["options"][choice_index] if choice_index < len(current.choices[0]["options"]) else None
                })
        
        self.current_content.current_stage += 1
        return self.get_current_stage()
    
    def display_content(self, stage_number: Optional[int] = None) -> str:
        """Display content in readable format."""
        if not self.current_content:
            return "No active content"
        
        lines = []
        lines.append(f"=== {self.current_content.title} ===")
        lines.append(f"Theme: {self.current_content.theme}")
        lines.append(f"Stage {self.current_content.current_stage + 1}/{self.current_content.total_stages}")
        lines.append(f"Party Level: {self.current_content.party_level_range[0]}-{self.current_content.party_level_range[1]}")
        lines.append("")
        
        # Display current stage
        if stage_number is None:
            stage = self.get_current_stage()
        else:
            if 0 <= stage_number < len(self.current_content.stages):
                stage = self.current_content.stages[stage_number]
            else:
                return f"Invalid stage number: {stage_number}"
        
        if stage:
            lines.append(f"--- Stage {stage.stage_number}: {stage.name} ---")
            lines.append(f"Difficulty: {stage.difficulty}")
            lines.append(f"Description: {stage.description}")
            lines.append("")
            
            if stage.encounters:
                lines.append("Encounters:")
                for enc in stage.encounters:
                    lines.append(f"  • {enc['description']} (CR {enc['cr']:.1f}, {enc['xp']} XP)")
            
            if stage.npcs:
                lines.append("NPCs:")
                for npc in stage.npcs:
                    lines.append(f"  • {npc['role']} ({npc['disposition']})")
            
            if stage.locations:
                lines.append("Locations:")
                for loc in stage.locations:
                    lines.append(f"  • {loc['name']}")
            
            if stage.choices:
                lines.append("")
                lines.append("Choices:")
                for choice in stage.choices:
                    lines.append(f"  {choice['question']}")
                    for i, option in enumerate(choice["options"]):
                        lines.append(f"    {i + 1}. {option['text']}")
        
        return "\n".join(lines)
    
    def export_to_json(self, filepath: str) -> bool:
        """Export content to JSON file."""
        if not self.current_content:
            return False
        
        with open(filepath, 'w') as f:
            json.dump(self.current_content.to_dict(), f, indent=2)
        
        logger.info(f"Exported content to {filepath}")
        return True
