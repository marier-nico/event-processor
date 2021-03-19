from typing import Dict, Tuple, Any, Callable
from dataclasses import dataclass


@dataclass
class Processor:
    fn: Callable
    pre_processor: Callable
    dependencies: Dict[str, Tuple[str, ...]]


# Example: {(("key.sub.last", "value"), ("other.sub", "different")): Processor(...)}
PROCESSORS: Dict[Tuple[Tuple[str, Any], ...], Processor] = dict()

# Example {"boto_clients": lambda x: boto3.client(x)}
DEPENDENCY_FACTORIES: Dict[str, Callable] = dict()
