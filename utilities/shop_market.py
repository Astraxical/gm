#!/usr/bin/env python3
"""
DnD Shop & Market Generator v1.0

Generate magic item shops, pricing, and inventory.
Track economy and item availability.

Features:
- Magic item shop generation
- Dynamic pricing
- Item availability by tier
- Buy/sell tracking
- Regional variations
"""

import json
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ShopItem:
    """Item for sale."""
    name: str
    type: str
    rarity: str
    base_price: int
    current_price: int
    quantity: int = 1
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "rarity": self.rarity,
            "price": self.current_price,
            "quantity": self.quantity,
            "description": self.description
        }


@dataclass
class Shop:
    """A magic item shop."""
    name: str
    owner: str
    location: str
    tier: int = 1  # 1-5 based on settlement size
    inventory: List[ShopItem] = field(default_factory=list)
    gold_available: int = 1000
    markup: float = 1.0
    discount: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "owner": self.owner,
            "location": self.location,
            "tier": self.tier,
            "inventory": [i.to_dict() for i in self.inventory],
            "gold_available": self.gold_available
        }


class ShopGenerator:
    """Generate magic item shops."""

    RARITY_PRICES = {
        "common": (50, 100),
        "uncommon": (100, 500),
        "rare": (500, 5000),
        "very_rare": (5000, 50000),
        "legendary": (50000, 500000)
    }

    ITEM_TABLES = {
        "common": [
            ("Potion of Healing", "potion", "Restores 2d4+2 HP"),
            ("Alchemist's Fire", "consumable", "Deals 1d4 fire damage"),
            ("Holy Water", "consumable", "Damages undead/fiends"),
            ("Smoke Stick", "consumable", "Creates smoke cloud"),
        ],
        "uncommon": [
            ("Potion of Greater Healing", "potion", "Restores 4d4+4 HP"),
            ("Weapon +1", "weapon", "+1 to attack and damage"),
            ("Armor +1", "armor", "+1 to AC"),
            ("Ring of Protection", "ring", "+1 to AC and saves"),
            ("Cloak of Protection", "wondrous", "+1 to AC and saves"),
        ],
        "rare": [
            ("Potion of Superior Healing", "potion", "Restores 8d4+8 HP"),
            ("Weapon +2", "weapon", "+2 to attack and damage"),
            ("Armor +2", "armor", "+2 to AC"),
            ("Amulet of Health", "wondrous", "CON = 19"),
            ("Flame Tongue", "weapon", "Extra fire damage"),
        ],
        "very_rare": [
            ("Potion of Supreme Healing", "potion", "Restores 10d4+20 HP"),
            ("Weapon +3", "weapon", "+3 to attack and damage"),
            ("Armor +3", "armor", "+3 to AC"),
            ("Ring of Spell Storing", "ring", "Stores spells"),
        ],
        "legendary": [
            ("Potion of Invulnerability", "potion", "Resistant to all damage"),
            ("Holy Avenger", "weapon", "Legendary paladin sword"),
            ("Staff of the Magi", "staff", "Powerful wizard staff"),
        ]
    }

    SHOP_NAMES = [
        "The Magic Emporium", "Wondrous Items", "The Enchanted Bazaar",
        "Mystic Mercantile", "The Arcane Market", "Spellbound Shops",
        "The Gilded Wand", "Potions & Curiosities", "The Dragon's Hoard"
    ]

    OWNER_NAMES = [
        "Elara the Wise", "Gimble Goldhand", "Madame Mystica",
        "Fenwick the Merchant", "Lady Silverstone", "Old Tom's Treasures"
    ]

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_shop(
        self,
        tier: int = 1,
        location: str = "City",
        name: Optional[str] = None
    ) -> Shop:
        """
        Generate a magic item shop.
        
        Args:
            tier: Shop tier (1-5)
            location: Settlement type
            name: Optional shop name
            
        Returns:
            Generated Shop
        """
        shop = Shop(
            name=name or random.choice(self.SHOP_NAMES),
            owner=random.choice(self.OWNER_NAMES),
            location=location,
            tier=tier,
            gold_available=tier * 1000 * random.randint(1, 3)
        )

        # Generate inventory based on tier - ensure valid range
        num_items = random.randint(3, max(3, tier * 2))
        
        for _ in range(num_items):
            item = self._generate_item(tier)
            shop.inventory.append(item)
        
        # Apply random markup/discount
        shop.markup = random.uniform(0.8, 1.3)
        if random.random() < 0.2:
            shop.discount = random.uniform(0.05, 0.2)
        
        logger.info(f"Generated shop: {shop.name} (Tier {tier})")
        return shop

    def _generate_item(self, tier: int) -> ShopItem:
        """Generate a single shop item."""
        # Determine rarity based on tier
        rarity_weights = {
            1: {"common": 70, "uncommon": 30},
            2: {"common": 40, "uncommon": 50, "rare": 10},
            3: {"common": 20, "uncommon": 50, "rare": 25, "very_rare": 5},
            4: {"uncommon": 30, "rare": 50, "very_rare": 15, "legendary": 5},
            5: {"rare": 30, "very_rare": 50, "legendary": 20},
        }
        
        weights = rarity_weights.get(tier, rarity_weights[1])
        rarity = random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
        
        # Select item
        items = self.ITEM_TABLES.get(rarity, self.ITEM_TABLES["common"])
        item_data = random.choice(items)
        
        # Calculate price
        price_range = self.RARITY_PRICES.get(rarity, (100, 500))
        base_price = random.randint(price_range[0], price_range[1])
        
        return ShopItem(
            name=item_data[0],
            type=item_data[1],
            rarity=rarity,
            base_price=base_price,
            current_price=base_price,
            quantity=random.randint(1, 3) if rarity in ["common", "uncommon"] else 1,
            description=item_data[2] if len(item_data) > 2 else ""
        )

    def buy_item(self, shop: Shop, item_index: int) -> Optional[ShopItem]:
        """Buy an item from the shop."""
        if item_index >= len(shop.inventory):
            return None
        
        item = shop.inventory[item_index]
        price = int(item.current_price * shop.markup * (1 - shop.discount))
        
        if price > shop.gold_available:
            logger.warning("Shop cannot afford to buy this item")
            return None
        
        shop.gold_available -= price
        shop.inventory.pop(item_index)
        
        logger.info(f"Bought {item.name} for {price} gp")
        return item

    def sell_item(self, shop: Shop, item: ShopItem) -> int:
        """Sell an item to the shop."""
        # Shop buys at 50-75% of base price
        buy_price = int(item.base_price * random.uniform(0.5, 0.75))
        
        if buy_price > shop.gold_available:
            logger.warning("Shop cannot afford this item")
            return 0
        
        shop.gold_available -= buy_price
        item.current_price = buy_price
        shop.inventory.append(item)
        
        logger.info(f"Shop bought {item.name} for {buy_price} gp")
        return buy_price

    def restock(self, shop: Shop) -> int:
        """Restock the shop inventory."""
        added = 0
        while len(shop.inventory) < shop.tier * 2:
            item = self._generate_item(shop.tier)
            shop.inventory.append(item)
            added += 1
        
        logger.info(f"Restocked {added} items")
        return added

    def display_shop(self, shop: Shop) -> str:
        """Display shop inventory."""
        lines = []
        lines.append(f"=== {shop.name} ===")
        lines.append(f"Owner: {shop.owner}")
        lines.append(f"Location: {shop.location}")
        lines.append(f"Gold Available: {shop.gold_available} gp")
        lines.append("")
        lines.append("Inventory:")
        lines.append("-" * 60)
        
        for i, item in enumerate(shop.inventory, 1):
            price = int(item.current_price * shop.markup * (1 - shop.discount))
            discount_str = f" ({int((1-shop.discount)*100)}% off)" if shop.discount > 0 else ""
            lines.append(f"{i}. {item.name} ({item.rarity})")
            lines.append(f"   Price: {price} gp{discount_str} | Qty: {item.quantity}")
            if item.description:
                lines.append(f"   {item.description}")
            lines.append("")
        
        return "\n".join(lines)


def main():
    """CLI for shop generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DnD Shop Generator v1.0")
    parser.add_argument("-t", "--tier", type=int, default=2, help="Shop tier (1-5)")
    parser.add_argument("-l", "--location", default="City", help="Location type")
    parser.add_argument("--name", type=str, help="Shop name")
    parser.add_argument("--seed", type=int, help="Random seed")
    
    args = parser.parse_args()
    
    generator = ShopGenerator(seed=args.seed)
    shop = generator.generate_shop(tier=args.tier, location=args.location, name=args.name)
    
    print(generator.display_shop(shop))


if __name__ == "__main__":
    main()
