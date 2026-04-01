#!/usr/bin/env python3
"""
Choice Engine Module

Generate meaningful choices for story continuation.
Tracks consequences and provides branching narrative options.
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class StoryChoice:
    """A story choice option."""
    id: int
    question: str
    options: List[Dict[str, Any]] = field(default_factory=list)
    context: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "options": self.options,
            "context": self.context
        }


@dataclass
class ChoiceConsequence:
    """Consequence of a choice."""
    choice_id: int
    option_index: int
    immediate_effect: str
    long_term_effect: str
    difficulty_change: int = 0
    relationship_changes: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "choice_id": self.choice_id,
            "option_index": self.option_index,
            "immediate_effect": self.immediate_effect,
            "long_term_effect": self.long_term_effect,
            "difficulty_change": self.difficulty_change,
            "relationship_changes": self.relationship_changes
        }


class ChoiceEngine:
    """Generate and track story choices."""
    
    # Choice templates by situation
    CHOICE_TEMPLATES = {
        "approach": {
            "question": "How do you approach the situation?",
            "options": [
                {"text": "Direct confrontation", "style": "aggressive", "risk": "high"},
                {"text": "Careful observation", "style": "cautious", "risk": "low"},
                {"text": "Seek information first", "style": "investigative", "risk": "medium"},
                {"text": "Find an alternative route", "style": "creative", "risk": "medium"}
            ]
        },
        "conflict": {
            "question": "How do you handle the conflict?",
            "options": [
                {"text": "Fight", "style": "combat", "risk": "high"},
                {"text": "Negotiate", "style": "social", "risk": "medium"},
                {"text": "Sneak past", "style": "stealth", "risk": "medium"},
                {"text": "Bribe or trade", "style": "diplomatic", "risk": "low"}
            ]
        },
        "mystery": {
            "question": "What do you investigate?",
            "options": [
                {"text": "The crime scene", "focus": "physical_evidence"},
                {"text": "Witness accounts", "focus": "testimony"},
                {"text": "Historical records", "focus": "background"},
                {"text": "Suspect's belongings", "focus": "personal_items"}
            ]
        },
        "travel": {
            "question": "Which route do you take?",
            "options": [
                {"text": "Main road (safe but slow)", "speed": "slow", "danger": "low"},
                {"text": "Forest path (faster but risky)", "speed": "medium", "danger": "medium"},
                {"text": "Mountain pass (fastest, dangerous)", "speed": "fast", "danger": "high"},
                {"text": "River route (unpredictable)", "speed": "variable", "danger": "variable"}
            ]
        },
        "treasure": {
            "question": "How do you handle the treasure?",
            "options": [
                {"text": "Take everything", "greed": "high", "consequence": "may trigger traps"},
                {"text": "Take only valuables", "greed": "medium", "consequence": "balanced"},
                {"text": "Leave a fair share", "greed": "low", "consequence": "good karma"},
                {"text": "Document and report", "greed": "none", "consequence": "reputation boost"}
            ]
        },
        "npc_interaction": {
            "question": "How do you respond?",
            "options": [
                {"text": "Friendly and open", "attitude": "friendly"},
                {"text": "Cautious and reserved", "attitude": "neutral"},
                {"text": "Demanding and assertive", "attitude": "aggressive"},
                {"text": "Deceptive and manipulative", "attitude": "deceptive"}
            ]
        }
    }
    
    # Consequence templates
    CONSEQUENCE_TEMPLATES = {
        "aggressive": {
            "immediate": "You move forward boldly",
            "long_term": "Enemies know to fear you, but allies may be wary",
            "difficulty_change": 1
        },
        "cautious": {
            "immediate": "You proceed carefully",
            "long_term": "You avoid many dangers but progress is slow",
            "difficulty_change": -1
        },
        "investigative": {
            "immediate": "You gather valuable information",
            "long_term": "Knowledge proves useful in future encounters",
            "difficulty_change": 0
        },
        "creative": {
            "immediate": "You find an unexpected solution",
            "long_term": "Your reputation for ingenuity grows",
            "difficulty_change": 0
        },
        "combat": {
            "immediate": "Battle is joined",
            "long_term": "Victory brings glory, defeat brings consequences",
            "difficulty_change": 2
        },
        "social": {
            "immediate": "You attempt to reason",
            "long_term": "Relationships are built or broken",
            "difficulty_change": -1
        },
        "stealth": {
            "immediate": "You move unseen",
            "long_term": "Unknown dangers may remain ahead",
            "difficulty_change": 0
        },
        "diplomatic": {
            "immediate": "You seek common ground",
            "long_term": "Alliances form through negotiation",
            "difficulty_change": -1
        },
        "friendly": {
            "immediate": "Warmth is reciprocated",
            "long_term": "Friendships develop",
            "difficulty_change": 0
        },
        "neutral": {
            "immediate": "Professional distance maintained",
            "long_term": "Respect without closeness",
            "difficulty_change": 0
        }
    }
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        
        self.choice_history: List[Dict[str, Any]] = []
        self.current_choices: List[StoryChoice] = []
    
    def generate_choices(
        self,
        situation: str,
        context: str = "",
        party_state: Optional[Dict[str, Any]] = None
    ) -> StoryChoice:
        """
        Generate choices for a situation.
        
        Args:
            situation: Type of situation (approach, conflict, mystery, etc.)
            context: Additional context
            party_state: Current party state (level, resources, etc.)
            
        Returns:
            StoryChoice with options
        """
        template = self.CHOICE_TEMPLATES.get(
            situation, 
            self.CHOICE_TEMPLATES["approach"]
        )
        
        # Create choice
        choice = StoryChoice(
            id=len(self.current_choices) + 1,
            question=template["question"],
            options=self._customize_options(template["options"], party_state),
            context=context
        )
        
        self.current_choices.append(choice)
        logger.debug(f"Generated choices for situation: {situation}")
        
        return choice
    
    def _customize_options(
        self,
        options: List[Dict[str, Any]],
        party_state: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Customize options based on party state."""
        customized = []
        
        for option in options:
            new_option = option.copy()
            
            # Adjust based on party level
            if party_state:
                level = party_state.get("level", 1)
                
                # High level parties get more options
                if level >= 5 and "risk" in option:
                    if option["risk"] == "high":
                        new_option["success_chance"] = "improved"
                
                # Resource-strapped parties see different risks
                if party_state.get("low_resources", False):
                    if option.get("risk") == "high":
                        new_option["warning"] = "Risky with current resources"
            
            customized.append(new_option)
        
        return customized
    
    def get_consequence(
        self,
        choice: StoryChoice,
        option_index: int
    ) -> ChoiceConsequence:
        """
        Get the consequence of a choice.
        
        Args:
            choice: The choice made
            option_index: Which option was selected
            
        Returns:
            ChoiceConsequence
        """
        if option_index >= len(choice.options):
            option_index = 0
        
        option = choice.options[option_index]
        
        # Determine style
        style = option.get("style", "neutral")
        
        # Get consequence template
        template = self.CONSEQUENCE_TEMPLATES.get(
            style,
            self.CONSEQUENCE_TEMPLATES["neutral"]
        )
        
        consequence = ChoiceConsequence(
            choice_id=choice.id,
            option_index=option_index,
            immediate_effect=template["immediate"],
            long_term_effect=template["long_term"],
            difficulty_change=template.get("difficulty_change", 0)
        )
        
        # Record choice
        self.choice_history.append({
            "choice_id": choice.id,
            "question": choice.question,
            "selected_option": option.get("text", ""),
            "style": style,
            "consequence": consequence.to_dict()
        })
        
        return consequence
    
    def get_branching_path(self, choices_made: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze choice history to determine story path.
        
        Args:
            choices_made: List of previous choices
            
        Returns:
            Path analysis
        """
        path_analysis = {
            "dominant_style": self._find_dominant_style(choices_made),
            "risk_tolerance": self._calculate_risk_tolerance(choices_made),
            "suggested_difficulty": self._suggest_difficulty(choices_made),
            "relationship_impacts": self._analyze_relationships(choices_made)
        }
        
        return path_analysis
    
    def _find_dominant_style(self, choices: List[Dict[str, Any]]) -> str:
        """Find the most common choice style."""
        style_counts = {}
        
        for choice in choices:
            style = choice.get("style", "neutral")
            style_counts[style] = style_counts.get(style, 0) + 1
        
        if not style_counts:
            return "balanced"
        
        return max(style_counts, key=style_counts.get)
    
    def _calculate_risk_tolerance(self, choices: List[Dict[str, Any]]) -> str:
        """Calculate party's risk tolerance."""
        risk_scores = {"low": 1, "medium": 2, "high": 3}
        total = 0
        count = 0
        
        for choice in choices:
            option = choice.get("selected_option", "")
            # Simplified risk calculation
            if "careful" in option.lower() or "cautious" in option.lower():
                total += 1
                count += 1
            elif "bold" in option.lower() or "direct" in option.lower():
                total += 3
                count += 1
            else:
                total += 2
                count += 1
        
        if count == 0:
            return "unknown"
        
        avg = total / count
        if avg < 1.5:
            return "cautious"
        elif avg > 2.5:
            return "bold"
        else:
            return "balanced"
    
    def _suggest_difficulty(self, choices: List[Dict[str, Any]]) -> str:
        """Suggest difficulty based on choices."""
        # Analyze if party handles challenges well
        bold_choices = sum(1 for c in choices if c.get("style") in ["aggressive", "combat"])
        cautious_choices = sum(1 for c in choices if c.get("style") in ["cautious", "stealth"])
        
        if bold_choices > cautious_choices * 2:
            return "challenging"  # They like action
        elif cautious_choices > bold_choices:
            return "moderate"  # Prefer careful play
        else:
            return "balanced"
    
    def _analyze_relationships(self, choices: List[Dict[str, Any]]) -> Dict[str, str]:
        """Analyze relationship impacts from choices."""
        impacts = {}
        
        for choice in choices:
            style = choice.get("style", "")
            
            if style in ["aggressive", "combat"]:
                impacts["intimidation"] = "increased"
                impacts["diplomacy"] = "decreased"
            elif style in ["diplomatic", "social"]:
                impacts["diplomacy"] = "increased"
            elif style in ["friendly"]:
                impacts["friendship"] = "increased"
            elif style in ["deceptive"]:
                impacts["trust"] = "decreased"
        
        return impacts
    
    def get_choice_history(self) -> List[Dict[str, Any]]:
        """Get all choices made."""
        return self.choice_history
    
    def clear_history(self) -> None:
        """Clear choice history."""
        self.choice_history.clear()
        self.current_choices.clear()
    
    def export_choices(self) -> Dict[str, Any]:
        """Export choices and consequences."""
        return {
            "current_choices": [c.to_dict() for c in self.current_choices],
            "choice_history": self.choice_history
        }
    
    def display_choices(self, choice: Optional[StoryChoice] = None) -> str:
        """Display choices in readable format."""
        if choice is None:
            if not self.current_choices:
                return "No active choices"
            choice = self.current_choices[-1]
        
        lines = []
        lines.append(f"\n{choice.question}")
        lines.append("-" * 40)
        
        for i, option in enumerate(choice.options, 1):
            lines.append(f"  {i}. {option.get('text', 'Unknown')}")
            
            # Show additional info if available
            if "risk" in option:
                lines.append(f"     Risk: {option['risk']}")
            if "warning" in option:
                lines.append(f"     ⚠️ {option['warning']}")
        
        return "\n".join(lines)
