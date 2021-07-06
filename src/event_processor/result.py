from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    """A result is what gets returned after an invocation.

    It contains information about the processor as well as its return value.
    """

    processor_name: str
    returned_value: Any
