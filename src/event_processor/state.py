"""Hold the state for event processors.

The state is made up of the currently registered processors and dependency factories.
"""
from typing import Dict, Tuple, Any, Callable
from dataclasses import dataclass


@dataclass
class Processor:
    """Represent a registered processor."""

    fn: Callable
    pre_processor: Callable
    dependencies: Dict[str, Tuple[str, ...]]


# Example: {(("key.sub.last", "value"), ("other.sub", "different")): Processor(...)}
PROCESSORS: Dict[Tuple[Tuple[str, Any], ...], Processor] = dict()

# Example {"boto_clients": lambda x: boto3.client(x)}
DEPENDENCY_FACTORIES: Dict[str, Callable] = dict()
