"""
Data models for the AI Food Logger.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class NutritionalInfo:
    """A standardized set of nutritional facts."""
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float = 0.0
    sugar: float = 0.0
    sodium: float = 0.0
    potassium: float = 0.0
    vitamin_c: float = 0.0
    calcium: float = 0.0
    iron: float = 0.0

@dataclass
class ServingSize:
    """Represents a serving amount and unit."""
    amount: float
    unit: str

@dataclass
class StandardServing:
    """A structured representation of a standard serving size and its nutrition."""
    size: ServingSize
    alt_size: Optional[ServingSize]
    nutrition: NutritionalInfo

@dataclass
class Consumed:
    """Represents what the user consumed, including the calculated nutrition."""
    size: ServingSize
    standard_servings: float
    nutrition: NutritionalInfo

@dataclass
class ProcessedFood:
    """A food item with all relevant data."""
    food_name: str
    user_description: str
    standard_serving: StandardServing
    consumed: Consumed
    confidence_score: float
    source_notes: str
    food_id: Optional[str] = None

@dataclass
class MealAnalysis:
    """The deterministic, calculated results of a meal analysis."""
    processed_foods: List[ProcessedFood]
    totals: NutritionalInfo

    def to_dict(self):
        """Converts the object to a dictionary for comparison."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MealAnalysis':
        """Creates a MealAnalysis object from a dictionary."""
        processed_foods = [
            ProcessedFood(
                standard_serving=StandardServing(
                    size=ServingSize(**food['standard_serving']['size']),
                    alt_size=ServingSize(**food['standard_serving']['alt_size']) if food['standard_serving']['alt_size'] else None,
                    nutrition=NutritionalInfo(**food['standard_serving']['nutrition'])
                ),
                consumed=Consumed(
                    size=ServingSize(**food['consumed']['size']),
                    standard_servings=food['consumed']['standard_servings'],
                    nutrition=NutritionalInfo(**food['consumed']['nutrition'])
                ),
                **{k: v for k, v in food.items() if k not in ['standard_serving', 'consumed']}
            ) for food in data['processed_foods']
        ]
        totals = NutritionalInfo(**data['totals'])
        return cls(processed_foods=processed_foods, totals=totals)

@dataclass
class FinalResult:
    """The final wrapper object including non-deterministic metadata."""
    analysis: MealAnalysis
    avg_confidence: float
    timestamp: datetime