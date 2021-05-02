"""Contains many different filters to conveniently filter through events."""
from abc import ABC, abstractmethod
from typing import Any


class Filter(ABC):
    """Abstract filter to define the filter interface."""

    @abstractmethod
    def matches(self, event: dict) -> bool:
        """Test whether a given event matches an input event.

        :param event: The event to test
        :return: True if the event matches, False otherwise
        """

    def __and__(self, other: "Filter") -> "Filter":
        """Combine two filters with a logical AND between them.

        :param other: The other filter to combine
        :return: A new filter representing the combination of the two
        """
        return And(self, other)

    def __or__(self, other: "Filter") -> "Filter":
        """Combine two filters with a logical OR between them.

        :param other: The other filter to combine
        :return: A new filter representing the combination of the two
        """
        return Or(self, other)


class Accept(Filter):
    """Accept any event (good for default processors)."""

    def matches(self, _event: dict) -> bool:
        return True


class Exists(Filter):
    """Accept event where a given key exists."""

    def __init__(self, path: Any):
        self.path = path

    def matches(self, event: dict) -> bool:
        current_location = event
        for part in self.path.split("."):
            if current_location and part in current_location:
                current_location = current_location[part]
            else:
                return False

        return True


class Eq(Filter):
    """Accept events where a given value is present at the given key."""

    def __init__(self, path: Any, value: Any):
        self.path = path
        self.value = value

    def matches(self, event: dict) -> bool:
        if Exists(self.path).matches(event):
            current_location = event
            for part in self.path.split("."):
                current_location = current_location[part]

            return current_location == self.value

        return False


class And(Filter):
    """Accept events that get accepted by all specified filters."""

    def __init__(self, *args: Filter):
        self.filters = args

    def matches(self, event: dict) -> bool:
        return all(filter_.matches(event) for filter_ in self.filters)


class Or(Filter):
    """Accept events that get accepted by at least one specified filter."""

    def __init__(self, *args: Filter):
        self.filters = args

    def matches(self, event: dict) -> bool:
        return any(filter_.matches(event) for filter_ in self.filters)
