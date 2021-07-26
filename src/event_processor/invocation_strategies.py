"""Contains the different invocation strategies for calling processors."""
from functools import partial
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, List, Callable, Any, Union

from .dependencies import call_with_injection, Event
from .error_handling_strategies import ErrorHandlingStrategy, Bubble
from .exceptions import InvocationError
from .result import Result


def _get_processor_name(processor: Any) -> str:
    try:
        return processor.__name__
    except AttributeError:
        return "unavailable"


class InvocationStrategy(ABC):
    """Class defining an abstract invocation strategy."""

    def __init__(self, error_handling_strategy: ErrorHandlingStrategy = Bubble()):
        self.error_handling_strategy = error_handling_strategy

    @abstractmethod
    def invoke(
        self, matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None
    ) -> Union[Result, List[Result]]:
        """Invoke one or multiple matching processors."""


class FirstMatch(InvocationStrategy):
    """Strategy calling the first matching processor."""

    def invoke(self, matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None) -> Result:
        return self.error_handling_strategy.invoke(
            callable_name=_get_processor_name(matching[0]),
            callable_=partial(call_with_injection, matching[0], event=event, cache=cache),
        )


class AllMatches(InvocationStrategy):
    """Strategy calling all matching processors."""

    def invoke(
        self, matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None
    ) -> List[Result]:
        results = []
        for match in matching:
            results.append(
                self.error_handling_strategy.invoke(
                    callable_name=_get_processor_name(match),
                    callable_=partial(call_with_injection, match, event=event, cache=cache),
                )
            )

        return results


class NoMatches(InvocationStrategy):
    """Strategy not calling any matching processors."""

    def invoke(self, matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None) -> Result:
        if len(matching) >= 2:
            return Result(processor_name=_get_processor_name(None), returned_value=None)

        return FirstMatch().invoke(matching, event=event, cache=cache)


class NoMatchesStrict(InvocationStrategy):
    """Strategy failing when there are multiple matching."""

    def invoke(self, matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None) -> Result:
        if len(matching) >= 2:
            raise InvocationError("Multiple matching processors of the same rank")

        return FirstMatch().invoke(matching, event=event, cache=cache)


class InvocationStrategies(Enum):
    """Enumeration of available invocation strategies."""

    FIRST_MATCH = FirstMatch
    ALL_MATCHES = AllMatches
    NO_MATCHES = NoMatches
    NO_MATCHES_STRICT = NoMatchesStrict
