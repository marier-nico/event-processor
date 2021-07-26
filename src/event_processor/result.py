from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Result:
    """A result is what gets returned after an invocation.

    It contains information about the processor as well as its return value.
    """

    processor_name: str
    returned_value: Optional[Any] = None
    raised_exception: Optional[Exception] = None

    def has_value(self) -> bool:
        return not self.has_exception()

    def has_exception(self) -> bool:
        return self.raised_exception is not None
