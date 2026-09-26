"""
Deterministic core: optimizer, rule engine, events.

Quantities never originate here except by calling the Nutrient Ledger
(`ledger.convert_gap_to_products`) through HeuristicOptimizer.
"""

from .events import Event, EventType
from .event_bus import EventBus, InMemoryEventBus, get_bus
from .optimizer import Optimizer, HeuristicOptimizer, OptimizerPlan
from .rules import RuleEngine, Violation

__all__ = [
    "Event",
    "EventType",
    "EventBus",
    "InMemoryEventBus",
    "get_bus",
    "Optimizer",
    "HeuristicOptimizer",
    "OptimizerPlan",
    "RuleEngine",
    "Violation",
]
