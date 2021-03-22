"""Contains a class which represents an event processor."""
from dataclasses import dataclass
from typing import Dict, Tuple, Callable


@dataclass
class Processor:
    """Represent a registered processor."""

    fn: Callable
    pre_processor: Callable
    dependencies: Dict[str, Tuple[str, ...]]
