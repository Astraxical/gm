#!/usr/bin/env python3
"""
DnD Weather Generator v1.0

Generate dynamic weather systems, seasonal effects, and environmental conditions.
Perfect for adding realism to outdoor adventures.

Features:
- Seasonal weather patterns
- Regional climate variations
- Extreme weather events
- Weather effects on gameplay
- Multi-day forecasts
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class Climate(str, Enum):
    TEMPERATE = "temperate"
    TROPICAL = "tropical"
    ARCTIC = "arctic"
    DESERT = "desert"
    MOUNTAIN = "mountain"
    COASTAL = "coastal"


@dataclass
class WeatherDay:
    """Single day's weather."""
    day: int
    season: str
    temperature: str
    condition: str
    precipitation: str
    wind: str
    visibility: str
    effects: List[str] = field(default_factory=list)
    survival_dc: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "season": self.season,
            "temperature": self.temperature,
            "condition": self.condition,
            "precipitation": self.precipitation,
            "wind": self.wind,
            "visibility": self.visibility,
            "effects": self.effects,
            "survival_dc": self.survival_dc
        }


class WeatherGenerator:
    """Generate weather patterns and effects."""

    # Weather tables by season and climate
    WEATHER_TABLES = {
        Climate.TEMPERATE: {
            Season.SPRING: {
                "conditions": ["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Thunderstorm", "Fog"],
                "weights": [30, 25, 20, 10, 10, 5],
                "temp_range": ("Cool", "Warm")
            },
            Season.SUMMER: {
                "conditions": ["Clear", "Partly Cloudy", "Hot", "Thunderstorm", "Heat Wave"],
                "weights": [35, 25, 20, 15, 5],
                "temp_range": ("Warm", "Hot")
            },
            Season.AUTUMN: {
                "conditions": ["Clear", "Cloudy", "Light Rain", "Windy", "Fog", "Frost"],
                "weights": [30, 25, 20, 10, 10, 5],
                "temp_range": ("Cool", "Cold")
            },
            Season.WINTER: {
                "conditions": ["Clear", "Cloudy", "Snow", "Heavy Snow", "Blizzard", "Freezing"],
                "weights": [25, 25, 20, 15, 10, 5],
                "temp_range": ("Cold", "Freezing")
            }
        },
        Climate.TROPICAL: {
            Season.SPRING: {
                "conditions": ["Clear", "Partly Cloudy", "Humid", "Tropical Storm", "Monsoon"],
                "weights": [30, 25, 20, 15, 10],
                "temp_range": ("Warm", "Hot")
            },
            Season.SUMMER: {
                "conditions": ["Clear", "Humid", "Thunderstorm", "Tropical Storm", "Hurricane"],
                "weights": [25, 25, 20, 20, 10],
                "temp_range": ("Hot", "Very Hot")
            },
            Season.AUTUMN: {
                "conditions": ["Clear", "Humid", "Rain", "Thunderstorm", "Typhoon"],
                "weights": [30, 25, 20, 15, 10],
                "temp_range": ("Warm", "Hot")
            },
            Season.WINTER: {
                "conditions": ["Clear", "Partly Cloudy", "Humid", "Rain", "Warm"],
                "weights": [35, 25, 20, 15, 5],
                "temp_range": ("Warm", "Warm")
            }
        },
        Climate.ARCTIC: {
            Season.SPRING: {
                "conditions": ["Clear", "Cloudy", "Snow", "Blizzard", "Thaw"],
                "weights": [25, 25, 25, 15, 10],
                "temp_range": ("Freezing", "Cold")
            },
            Season.SUMMER: {
                "conditions": ["Clear", "Cloudy", "Cold", "Snow", "Rain"],
                "weights": [30, 25, 20, 15, 10],
                "temp_range": ("Cold", "Cool")
            },
            Season.AUTUMN: {
                "conditions": ["Clear", "Cloudy", "Snow", "Blizzard", "Freezing"],
                "weights": [20, 25, 25, 20, 10],
                "temp_range": ("Cold", "Freezing")
            },
            Season.WINTER: {
                "conditions": ["Clear", "Snow", "Heavy Snow", "Blizzard", "Extreme Cold"],
                "weights": [15, 25, 25, 25, 10],
                "temp_range": ("Freezing", "Extreme Cold")
            }
        },
        Climate.DESERT: {
            Season.SPRING: {
                "conditions": ["Clear", "Hot", "Dry", "Sandstorm", "Clear"],
                "weights": [40, 25, 20, 10, 5],
                "temp_range": ("Warm", "Hot")
            },
            Season.SUMMER: {
                "conditions": ["Clear", "Very Hot", "Heat Wave", "Sandstorm", "Mirage"],
                "weights": [35, 30, 15, 15, 5],
                "temp_range": ("Hot", "Extreme Heat")
            },
            Season.AUTUMN: {
                "conditions": ["Clear", "Hot", "Warm", "Sandstorm", "Clear"],
                "weights": [40, 25, 20, 10, 5],
                "temp_range": ("Warm", "Hot")
            },
            Season.WINTER: {
                "conditions": ["Clear", "Warm", "Cool", "Rain", "Cold Night"],
                "weights": [40, 25, 20, 10, 5],
                "temp_range": ("Cool", "Warm")
            }
        },
        Climate.MOUNTAIN: {
            Season.SPRING: {
                "conditions": ["Clear", "Cloudy", "Rain", "Snow", "Thunderstorm", "Fog"],
                "weights": [25, 20, 20, 15, 15, 5],
                "temp_range": ("Cold", "Cool")
            },
            Season.SUMMER: {
                "conditions": ["Clear", "Partly Cloudy", "Thunderstorm", "Fog", "Rain"],
                "weights": [30, 25, 20, 15, 10],
                "temp_range": ("Cool", "Warm")
            },
            Season.AUTUMN: {
                "conditions": ["Clear", "Cloudy", "Rain", "Snow", "Windy", "Fog"],
                "weights": [25, 20, 20, 15, 15, 5],
                "temp_range": ("Cold", "Cool")
            },
            Season.WINTER: {
                "conditions": ["Clear", "Snow", "Heavy Snow", "Blizzard", "Avalanche Risk"],
                "weights": [20, 25, 25, 20, 10],
                "temp_range": ("Freezing", "Cold")
            }
        },
        Climate.COASTAL: {
            Season.SPRING: {
                "conditions": ["Clear", "Partly Cloudy", "Rain", "Fog", "Storm"],
                "weights": [30, 25, 20, 15, 10],
                "temp_range": ("Cool", "Warm")
            },
            Season.SUMMER: {
                "conditions": ["Clear", "Sunny", "Humid", "Thunderstorm", "Hurricane"],
                "weights": [35, 25, 20, 15, 5],
                "temp_range": ("Warm", "Hot")
            },
            Season.AUTUMN: {
                "conditions": ["Clear", "Cloudy", "Rain", "Fog", "Storm"],
                "weights": [30, 25, 20, 15, 10],
                "temp_range": ("Cool", "Warm")
            },
            Season.WINTER: {
                "conditions": ["Clear", "Cloudy", "Rain", "Storm", "Fog"],
                "weights": [25, 25, 25, 15, 10],
                "temp_range": ("Cold", "Cool")
            }
        }
    }

    # Weather effects on gameplay
    WEATHER_EFFECTS = {
        "Clear": [],
        "Partly Cloudy": [],
        "Cloudy": ["Reduced sunlight for photosynthesis"],
        "Light Rain": ["Ground becomes slippery", "Fire difficulty increased"],
        "Heavy Rain": ["Visibility reduced", "Fire extinguished", "Difficult terrain in mud"],
        "Thunderstorm": ["Lightning risk in open", "Thunder masks sounds", "Fire extinguished"],
        "Snow": ["Difficult terrain", "Cold exposure risk", "Tracks covered"],
        "Heavy Snow": ["Heavy difficult terrain", "Visibility reduced", "Cold exposure"],
        "Blizzard": ["Heavy difficult terrain", "Visibility near zero", "Severe cold exposure", "Navigation DC 15"],
        "Fog": ["Visibility reduced to 30ft", "Ranged attacks at disadvantage"],
        "Heat Wave": ["Heat exhaustion risk", "Water consumption doubled", "Fire damage increased"],
        "Extreme Heat": ["Severe heat exhaustion", "Water consumption tripled", "Metal burns touch"],
        "Extreme Cold": ["Cold exhaustion risk", "Water freezes", "Unprotected skin freezes"],
        "Sandstorm": ["Visibility reduced", "Breathing difficulty", "Equipment damage risk"],
        "Hurricane": ["Impossible ranged attacks", "Flying impossible", "Severe difficult terrain"],
        "Tropical Storm": ["Heavy rain", "Strong winds", "Difficult terrain"],
        "Heat Wave": ["Exhaustion risk", "Increased water needs"],
    }

    WIND_LEVELS = ["Calm", "Light Breeze", "Moderate Wind", "Strong Wind", "Gale", "Storm"]

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.forecast: List[WeatherDay] = []

    def generate_day(
        self,
        season: str = "spring",
        climate: str = "temperate",
        day: int = 1
    ) -> WeatherDay:
        """Generate weather for a single day."""
        season_enum = Season(season.lower())
        climate_enum = Climate(climate.lower())
        
        table = self.WEATHER_TABLES[climate_enum][season_enum]
        
        # Roll weather
        condition = random.choices(table["conditions"], weights=table["weights"])[0]
        
        # Determine temperature
        temp_range = table["temp_range"]
        temperature = random.choice([temp_range[0], temp_range[1], temp_range[0]])
        
        # Wind
        wind = random.choice(self.WIND_LEVELS)
        
        # Precipitation chance based on condition
        precip_chance = {
            "Clear": 0, "Partly Cloudy": 5, "Cloudy": 10,
            "Light Rain": 80, "Heavy Rain": 95, "Thunderstorm": 100,
            "Snow": 80, "Heavy Snow": 95, "Blizzard": 100,
            "Fog": 50, "Sandstorm": 90
        }
        precipitation = "Yes" if random.randint(1, 100) <= precip_chance.get(condition, 0) else "No"
        
        # Visibility
        visibility_map = {
            "Clear": "Excellent", "Partly Cloudy": "Good", "Cloudy": "Good",
            "Fog": "Poor (30ft)", "Heavy Rain": "Poor", "Blizzard": "Near Zero",
            "Sandstorm": "Poor"
        }
        visibility = visibility_map.get(condition, "Good")
        
        # Effects
        effects = self.WEATHER_EFFECTS.get(condition, [])
        
        # Survival DC
        survival_dc = 10
        if condition in ["Blizzard", "Extreme Cold", "Extreme Heat", "Hurricane"]:
            survival_dc = 15
        elif condition in ["Heavy Snow", "Heavy Rain", "Heat Wave", "Freezing"]:
            survival_dc = 12
        
        return WeatherDay(
            day=day,
            season=season,
            temperature=temperature,
            condition=condition,
            precipitation=precipitation,
            wind=wind,
            visibility=visibility,
            effects=effects,
            survival_dc=survival_dc
        )

    def generate_forecast(
        self,
        days: int = 7,
        season: str = "spring",
        climate: str = "temperate",
        start_day: int = 1
    ) -> List[WeatherDay]:
        """Generate multi-day weather forecast."""
        self.forecast = []
        
        for i in range(days):
            day = self.generate_day(season, climate, start_day + i)
            self.forecast.append(day)
        
        logger.info(f"Generated {days}-day forecast for {season}/{climate}")
        return self.forecast

    def generate_extreme_event(self, season: str = "", climate: str = "") -> Dict[str, Any]:
        """Generate an extreme weather event."""
        events = [
            {
                "name": "Sudden Storm",
                "description": "A violent storm appears within minutes",
                "duration": "1d4 hours",
                "effects": ["Heavy rain", "Lightning", "Wind at disadvantage"],
                "save_dc": 15
            },
            {
                "name": "Flash Flood",
                "description": "Water levels rise rapidly in low areas",
                "duration": "2d6 hours",
                "effects": ["Difficult terrain", "Drowning risk", "Washes away objects"],
                "save_dc": 16
            },
            {
                "name": "Avalanche",
                "description": "Snow and debris cascade down mountainside",
                "duration": "Instant",
                "effects": ["Burial risk", "Bludgeoning damage", "Blocks passage"],
                "save_dc": 18
            },
            {
                "name": "Heat Mirage",
                "description": "Illusory water and objects appear in distance",
                "duration": "Until temperature drops",
                "effects": ["Navigation confusion", "False hope", "Wasted resources"],
                "save_dc": 14
            },
            {
                "name": "Black Ice",
                "description": "Invisible ice forms on surfaces",
                "duration": "Until melted",
                "effects": ["Slipping hazard", "Mounts frightened", "Difficult terrain"],
                "save_dc": 13
            },
            {
                "name": "Supernatural Fog",
                "description": "Magical fog with unusual properties",
                "duration": "1d6 hours",
                "effects": ["Vision reduced to 10ft", "Sounds muffled", "Possible encounters"],
                "save_dc": 15
            },
        ]
        
        return random.choice(events)

    def display_forecast(self, forecast: Optional[List[WeatherDay]] = None) -> str:
        """Display weather forecast in readable format."""
        if forecast is None:
            forecast = self.forecast
        
        if not forecast:
            return "No forecast generated"
        
        lines = []
        lines.append("=" * 70)
        lines.append("WEATHER FORECAST")
        lines.append("=" * 70)
        
        for day in forecast:
            lines.append(f"\nDay {day.day}: {day.condition}")
            lines.append(f"  Temperature: {day.temperature}")
            lines.append(f"  Wind: {day.wind}")
            lines.append(f"  Precipitation: {day.precipitation}")
            lines.append(f"  Visibility: {day.visibility}")
            lines.append(f"  Survival DC: {day.survival_dc}")
            if day.effects:
                lines.append(f"  Effects: {', '.join(day.effects)}")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    """CLI for weather generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD Weather Generator v1.0")
    parser.add_argument("-s", "--season", default="spring",
                        choices=["spring", "summer", "autumn", "winter"])
    parser.add_argument("-c", "--climate", default="temperate",
                        choices=["temperate", "tropical", "arctic", "desert", "mountain", "coastal"])
    parser.add_argument("-d", "--days", type=int, default=7, help="Days to forecast")
    parser.add_argument("--extreme", action="store_true", help="Generate extreme event")
    
    args = parser.parse_args()
    
    generator = WeatherGenerator()
    
    if args.extreme:
        event = generator.generate_extreme_event(args.season, args.climate)
        print(f"\n=== Extreme Weather Event ===")
        print(f"Event: {event['name']}")
        print(f"Description: {event['description']}")
        print(f"Duration: {event['duration']}")
        print(f"Save DC: {event['save_dc']}")
        print(f"Effects:")
        for effect in event['effects']:
            print(f"  • {effect}")
        return
    
    forecast = generator.generate_forecast(
        days=args.days,
        season=args.season,
        climate=args.climate
    )
    
    print(generator.display_forecast(forecast))


if __name__ == "__main__":
    main()
