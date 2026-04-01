#!/usr/bin/env python3
"""
DnD Travel Tracker v1.0

Track overland journeys, supplies, encounters, and events.
Perfect for wilderness campaigns and exploration.

Features:
- Track travel days and distance
- Supply consumption
- Random encounter rolls
- Weather generation
- Foraging and hunting
- Exhaustion tracking
- Journey events
- Export journey log
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Traveler:
    """A traveling character."""
    name: str
    speed: int = 30  # feet per round, affects overland speed
    strength: int = 10
    constitution: int = 10
    wisdom_survival: int = 0  # Survival modifier
    exhaustion: int = 0
    carrying_capacity: float = 0  # in lbs
    
    def __post_init__(self):
        if self.carrying_capacity <= 0:
            self.carrying_capacity = self.strength * 15
    
    def overland_speed(self, terrain: str = "normal") -> float:
        """Calculate overland speed in miles per day."""
        base = self.speed / 5 * 2  # Convert to mph, then to miles per 8-hour day
        terrain_mods = {"normal": 1.0, "difficult": 0.5, "mountain": 0.75, "swamp": 0.5}
        return base * terrain_mods.get(terrain, 1.0)


@dataclass
class Journey:
    """A travel journey."""
    name: str
    origin: str
    destination: str
    total_distance: float  # miles
    travelers: List[Traveler] = field(default_factory=list)
    supplies: int = 0  # rations
    water: int = 0  # waterskins
    mounts: List[Dict[str, Any]] = field(default_factory=list)
    days_traveled: int = 0
    events: List[Dict[str, Any]] = field(default_factory=list)
    weather_log: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "origin": self.origin,
            "destination": self.destination,
            "total_distance": self.total_distance,
            "days_traveled": self.days_traveled,
            "supplies_remaining": self.supplies,
            "water_remaining": self.water,
            "events": self.events,
            "weather_log": self.weather_log
        }


class TravelTracker:
    """Track overland travel."""

    TERRAIN_TYPES = ["plains", "forest", "mountain", "desert", "swamp", "hills", "arctic"]
    
    WEATHER_TABLE = {
        "plains": ["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Storm", "Fog"],
        "forest": ["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Fog", "Wind"],
        "mountain": ["Clear", "Cloudy", "Snow", "Heavy Snow", "Wind", "Storm"],
        "desert": ["Clear", "Hot", "Sandstorm", "Clear", "Clear", "Hot"],
        "swamp": ["Fog", "Light Rain", "Heavy Rain", "Humid", "Storm", "Fog"],
        "arctic": ["Clear", "Snow", "Heavy Snow", "Blizzard", "Clear", "Extreme Cold"],
    }
    
    ENCOUNTER_TABLES = {
        "plains": ["Wandering herbivores", "Bandits", "Wolves", "Traveling merchants", "Nothing"],
        "forest": ["Wolves", "Goblins", "Owlbear", "Druid", "Nothing", "Fey creature"],
        "mountain": ["Mountain goats", "Giant eagle", "Ogre", "Rockslide", "Nothing"],
        "desert": ["Sandstorm", "Nomads", "Giant scorpion", "Mirage", "Nothing"],
        "swamp": ["Giant insects", "Lizardfolk", "Will-o'-wisp", "Quicksand", "Nothing"],
        "arctic": ["White dragon", "Yeti", "Frost giants", "Avalanche", "Nothing"],
    }

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.journeys: Dict[str, Journey] = {}
        self.current_journey: Optional[str] = None

    def start_journey(
        self,
        name: str,
        origin: str,
        destination: str,
        distance: float,
        travelers: Optional[List[Traveler]] = None,
        supplies: int = 0,
        water: int = 0
    ) -> Journey:
        """Start a new journey."""
        journey = Journey(
            name=name,
            origin=origin,
            destination=destination,
            total_distance=distance,
            travelers=travelers or [],
            supplies=supplies,
            water=water
        )
        self.journeys[name] = journey
        self.current_journey = name
        logger.info(f"Started journey: {name} ({distance} miles)")
        return journey

    def travel_day(
        self,
        terrain: str = "normal",
        fast_pace: bool = False,
        forage: bool = False
    ) -> Dict[str, Any]:
        """
        Travel for one day.
        
        Returns:
            Day summary dict
        """
        if not self.current_journey:
            return {"error": "No active journey"}
        
        journey = self.journeys[self.current_journey]
        day_result = {
            "day": journey.days_traveled + 1,
            "terrain": terrain,
            "weather": self._roll_weather(terrain),
            "events": [],
            "supplies_used": 0,
            "forage_result": None
        }
        
        # Calculate distance traveled
        if journey.travelers:
            min_speed = min(t.overland_speed(terrain) for t in journey.travelers)
        else:
            min_speed = 24  # Default
        
        if fast_pace:
            distance = min_speed * 1.33
        else:
            distance = min_speed
        
        # Consume supplies (1 per traveler per day)
        supplies_needed = len(journey.travelers) if journey.travelers else 1
        day_result["supplies_used"] = supplies_needed
        
        if journey.supplies >= supplies_needed:
            journey.supplies -= supplies_needed
        else:
            journey.supplies = 0
            day_result["events"].append("No food - travelers may gain exhaustion")
        
        # Foraging
        if forage and journey.travelers:
            forager = max(journey.travelers, key=lambda t: t.wisdom_survival)
            forage_dc = 15
            forage_roll = random.randint(1, 20) + forager.wisdom_survival
            
            if forage_roll >= forage_dc:
                food_found = random.randint(1, 4)
                journey.supplies += food_found
                day_result["forage_result"] = f"Found {food_found} rations"
            else:
                day_result["forage_result"] = "Found no food"
        
        # Random encounter
        if random.random() < 0.2:  # 20% chance
            encounter = self._roll_encounter(terrain)
            day_result["events"].append(f"Encounter: {encounter}")
            journey.events.append({"day": day_result["day"], "type": "encounter", "detail": encounter})
        
        # Weather effects
        weather = day_result["weather"]
        if weather in ["Storm", "Heavy Rain", "Blizzard", "Sandstorm"]:
            distance *= 0.5
            day_result["events"].append(f"Weather slowed travel: {weather}")
        
        journey.days_traveled += 1
        journey.weather_log.append(weather)
        day_result["distance_traveled"] = round(distance, 1)
        
        logger.info(f"Day {day_result['day']}: Traveled {distance} miles through {terrain}")
        return day_result

    def _roll_weather(self, terrain: str) -> str:
        """Roll for weather based on terrain."""
        # Map terrain to weather category
        weather_terrain = "plains"
        for t in self.WEATHER_TABLE:
            if t in terrain.lower():
                weather_terrain = t
                break
        
        return random.choice(self.WEATHER_TABLE.get(weather_terrain, self.WEATHER_TABLE["plains"]))

    def _roll_encounter(self, terrain: str) -> str:
        """Roll for random encounter."""
        encounter_terrain = "plains"
        for t in self.ENCOUNTER_TABLES:
            if t in terrain.lower():
                encounter_terrain = t
                break
        
        return random.choice(self.ENCOUNTER_TABLES.get(encounter_terrain, self.ENCOUNTER_TABLES["plains"]))

    def rest(self, rest_type: str = "short") -> Dict[str, Any]:
        """Take a rest during travel."""
        if not self.current_journey:
            return {"error": "No active journey"}
        
        journey = self.journeys[self.current_journey]
        result = {"rest_type": rest_type, "effects": []}
        
        if rest_type == "short":
            result["effects"].append("Recovered hit dice")
            result["effects"].append("Can use abilities that recharge on short rest")
        elif rest_type == "long":
            result["effects"].append("Recovered HP")
            result["effects"].append("Recovered spell slots")
            result["effects"].append("Reduced exhaustion by 1")
            
            # Reduce exhaustion for all travelers
            for traveler in journey.travelers:
                if traveler.exhaustion > 0:
                    traveler.exhaustion -= 1
        
        return result

    def gain_exhaustion(self, traveler_name: str, levels: int = 1) -> bool:
        """Add exhaustion levels to a traveler."""
        if not self.current_journey:
            return False
        
        journey = self.journeys[self.current_journey]
        for traveler in journey.travelers:
            if traveler.name.lower() == traveler_name.lower():
                traveler.exhaustion += levels
                logger.warning(f"{traveler_name} gained {levels} exhaustion")
                return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current journey status."""
        if not self.current_journey:
            return {"error": "No active journey"}
        
        journey = self.journeys[self.current_journey]
        remaining = journey.total_distance - (journey.days_traveled * 24)  # Approximate
        
        return {
            "journey": journey.name,
            "progress": f"{journey.days_traveled * 24:.0f} / {journey.total_distance} miles",
            "remaining_miles": max(0, remaining),
            "supplies": journey.supplies,
            "water": journey.water,
            "traveler_status": [
                {"name": t.name, "exhaustion": t.exhaustion}
                for t in journey.travelers
            ]
        }

    def export_journey(self, filepath: str) -> None:
        """Export journey log to JSON."""
        if not self.current_journey:
            return
        
        journey = self.journeys[self.current_journey]
        with open(filepath, 'w') as f:
            json.dump(journey.to_dict(), f, indent=2)
        logger.info(f"Exported journey to {filepath}")


def main():
    """CLI for travel tracker."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DnD Travel Tracker v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python travel_tracker.py --demo
  python travel_tracker.py --journey "To Waterdeep" --distance 100
  python travel_tracker.py --travel --terrain forest
  python travel_tracker.py --status
        """
    )
    
    parser.add_argument("--demo", action="store_true", help="Run demo journey")
    parser.add_argument("--journey", type=str, help="Journey name")
    parser.add_argument("--distance", type=float, help="Total distance in miles")
    parser.add_argument("--origin", type=str, default="Starting Point", help="Origin location")
    parser.add_argument("--destination", type=str, default="Destination", help="Destination")
    parser.add_argument("--travel", action="store_true", help="Travel one day")
    parser.add_argument("--terrain", type=str, default="plains", help="Terrain type")
    parser.add_argument("--forage", action="store_true", help="Attempt to forage")
    parser.add_argument("--fast", action="store_true", help="Travel at fast pace")
    parser.add_argument("--status", action="store_true", help="Show journey status")
    parser.add_argument("--export", type=str, help="Export journey to file")
    
    args = parser.parse_args()
    
    tracker = TravelTracker()
    
    if args.demo:
        print("=== Demo Journey ===\n")
        
        # Create travelers
        travelers = [
            Traveler(name="Thorin", speed=25, strength=16, wisdom_survival=3),
            Traveler(name="Elara", speed=30, strength=10, wisdom_survival=5),
        ]
        
        # Start journey
        tracker.start_journey(
            name="To the Mountain",
            origin="Riverside Inn",
            destination="Iron Peak",
            distance=120,
            travelers=travelers,
            supplies=10,
            water=10
        )
        
        # Travel for 5 days
        terrains = ["plains", "forest", "forest", "mountain", "mountain"]
        for i, terrain in enumerate(terrains, 1):
            print(f"\n--- Day {i} ---")
            result = tracker.travel_day(terrain=terrain, forage=(i == 3))
            print(f"Weather: {result['weather']}")
            print(f"Terrain: {result['terrain']}")
            print(f"Distance: {result['distance_traveled']} miles")
            if result['forage_result']:
                print(f"Foraging: {result['forage_result']}")
            if result['events']:
                print(f"Events: {', '.join(result['events'])}")
        
        print("\n" + "=" * 50)
        status = tracker.get_status()
        print(f"Journey: {status['journey']}")
        print(f"Progress: {status['progress']}")
        print(f"Supplies: {status['supplies']}")
        
        return
    
    if args.journey and args.distance:
        tracker.start_journey(
            name=args.journey,
            origin=args.origin,
            destination=args.destination,
            distance=args.distance,
            supplies=args.distance // 10,  # Default supplies
            water=args.distance // 10
        )
        print(f"Started journey: {args.journey}")
        print(f"Distance: {args.distance} miles")
    
    if args.travel:
        result = tracker.travel_day(terrain=args.terrain, forage=args.forage, fast_pace=args.fast)
        print(f"\nDay {result.get('day', 1)}")
        print(f"Weather: {result.get('weather', 'Unknown')}")
        print(f"Distance: {result.get('distance_traveled', 0)} miles")
        if result.get('events'):
            print(f"Events: {', '.join(result['events'])}")
    
    if args.status:
        status = tracker.get_status()
        if "error" not in status:
            print(f"\nJourney: {status['journey']}")
            print(f"Progress: {status['progress']}")
            print(f"Supplies: {status['supplies']} rations")
            print(f"Water: {status['water']} waterskins")
    
    if args.export:
        tracker.export_journey(args.export)
        print(f"Exported to {args.export}")


if __name__ == "__main__":
    main()
