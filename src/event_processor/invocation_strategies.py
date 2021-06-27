"""Contains the different invocation strategies for calling processors."""
from abc import ABC
from enum import Enum
from typing import Dict, Optional, List, Callable, Any, Tuple

from .dependencies import call_with_injection, Event
from .exceptions import InvocationError


def _get_processor_name(processor: Any) -> str:
    try:
        return processor.__name__
    except AttributeError:
        return "unavailable"


class InvocationStrategy(ABC):
    """Class defining an abstract invocation strategy."""

    @staticmethod
    def invoke(
        matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None
    ) -> List[Tuple[str, Any]]:
        """Invoke one or multiple matching processors."""


class FirstMatch(InvocationStrategy):
    """Strategy calling the first matching processor."""

    @staticmethod
    def invoke(
        matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None
    ) -> List[Tuple[str, Any]]:
        return [(_get_processor_name(matching[0]), call_with_injection(matching[0], event=event, cache=cache))]


class AllMatches(InvocationStrategy):
    """Strategy calling all matching processors."""

    @staticmethod
    def invoke(
        matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None
    ) -> List[Tuple[str, Any]]:
        results = []
        for match in matching:
            results.append((_get_processor_name(match), call_with_injection(match, event=event, cache=cache)))

        return results


class NoMatches(InvocationStrategy):
    """Strategy not calling any matching processors."""

    @staticmethod
    def invoke(
        matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None
    ) -> List[Tuple[str, Any]]:
        if len(matching) >= 2:
            return [(_get_processor_name(None), None)]

        return FirstMatch.invoke(matching, event=event, cache=cache)


class NoMatchesStrict(InvocationStrategy):
    """Strategy failing when there are multiple matching."""

    @staticmethod
    def invoke(
        matching: List[Callable], event: Optional[Event] = None, cache: Optional[Dict] = None
    ) -> List[Tuple[str, Any]]:
        if len(matching) >= 2:
            raise InvocationError("Multiple matching processors of the same rank")

        return FirstMatch.invoke(matching, event=event, cache=cache)


class InvocationStrategies(Enum):
    """Enumeration of available invocation strategies."""

    FIRST_MATCH = FirstMatch
    ALL_MATCHES = AllMatches
    NO_MATCHES = NoMatches
    NO_MATCHES_STRICT = NoMatchesStrict
