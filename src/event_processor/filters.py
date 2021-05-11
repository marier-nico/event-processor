"""Contains many different filters to conveniently filter through events."""
from abc import ABC, abstractmethod
from typing import Any, Union, Callable

from .util import get_value_at_path


class Filter(ABC):
    """Abstract filter to define the filter interface."""

    @abstractmethod
    def matches(self, event: dict) -> bool:
        """Test whether a given event matches an input event.

        :param event: The event to test
        :return: True if the event matches, False otherwise
        """

    @abstractmethod
    def __hash__(self):
        """Hash a filter for storage in a dict or set."""

    @abstractmethod
    def __eq__(self, other) -> bool:
        """Test if two filters are equal.

        :param other: The other filter to test
        :return: True if the filters are equal, False otherwise
        """

    def __ne__(self, other) -> bool:
        """Test if two filters are different.

        :param other: The other filter to test
        :return: True if the filters are different, False otherwise
        """

        return not (self == other)

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

    def __hash__(self):
        return hash(self.__class__)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__)


class Exists(Filter):
    """Accept event where a given key exists."""

    def __init__(self, path: Any):
        self.path = path

    def matches(self, event: dict) -> bool:
        try:
            get_value_at_path(event, self.path)
        except KeyError:
            return False

        return True

    def __hash__(self):
        return hash((self.__class__, self.path))

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self.path == other.path
        return False


class Eq(Filter):
    """Accept events where a given value is present at the given key."""

    def __init__(self, path: Any, value: Any):
        self.path = path
        self.value = value

    def matches(self, event: dict) -> bool:
        try:
            return self.value == get_value_at_path(event, self.path)
        except KeyError:
            return False

    def __hash__(self):
        return hash((self.__class__, (self.path, self.value)))

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self.path == other.path and self.value == other.value
        return False


class NumCmp(Filter):
    """Accept events when the comparator returns True.

    If you use this processor, make sure that you don't use equal (and not identical) comparators for the same path.
    For example, don't use the same lambda in two different places. Instead, use a function, and pass a reference to
    that function. If you don't do that, the filters will effectively be different (even if they match the same thing),
    leading to perhaps unexpected results.
    """

    def __init__(self, path: Any, comparator: Callable[[float, float], bool], target: float):
        self.path = path
        self.comparator = comparator
        self.target = target

    def matches(self, event: dict) -> bool:
        try:
            found_value = get_value_at_path(event, self.path)
            float_value = float(found_value)
        except (KeyError, ValueError):
            return False

        return self.comparator(float_value, self.target)

    def __hash__(self):
        return hash((self.__class__, (self.path, self.comparator, self.target)))

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self.path == other.path and self.comparator == other.comparator and self.target == other.target
        return False


class Lt(NumCmp):
    """Accept events where the value at the given path exists and is less than the specified value."""

    def __init__(self, path: Any, value: Union[int, float]):
        float_value = float(value)
        super().__init__(path, self._compare, float_value)

    @staticmethod
    def _compare(event_value: float, target_value: float) -> bool:
        return event_value < target_value


class Leq(NumCmp):
    """Accept events where the value at the given path exists is less than or equal to the specified value."""

    def __init__(self, path: Any, value: Union[int, float]):
        float_value = float(value)
        super().__init__(path, self._compare, float_value)

    @staticmethod
    def _compare(event_value: float, target_value: float) -> bool:
        return event_value <= target_value


class Gt(NumCmp):
    """Accept events where the value exists and is greater than the specified value."""

    def __init__(self, path: Any, value: Union[int, float]):
        float_value = float(value)
        super().__init__(path, self._compare, float_value)

    @staticmethod
    def _compare(event_value: float, target_value: float) -> bool:
        return event_value > target_value


class Geq(NumCmp):
    """Accept events where the value exists and is greater than or equal to the specified value."""

    def __init__(self, path: Any, value: Union[int, float]):
        float_value = float(value)
        super().__init__(path, self._compare, float_value)

    @staticmethod
    def _compare(event_value: float, target_value: float) -> bool:
        return event_value >= target_value


class And(Filter):
    """Accept events that get accepted by all specified filters."""

    def __init__(self, *args: Filter):
        self.filters = args

    def matches(self, event: dict) -> bool:
        return all(filter_.matches(event) for filter_ in self.filters)

    def __hash__(self):
        return hash((self.__class__, self.filters))

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            self_in_other = all(filter_ in other.filters for filter_ in self.filters)
            other_in_self = all(filter_ in self.filters for filter_ in other.filters)
            return self_in_other and other_in_self
        return False


class Or(Filter):
    """Accept events that get accepted by at least one specified filter."""

    def __init__(self, *args: Filter):
        self.filters = args

    def matches(self, event: dict) -> bool:
        return any(filter_.matches(event) for filter_ in self.filters)

    def __hash__(self):
        return hash((self.__class__, self.filters))

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            self_in_other = all(filter_ in other.filters for filter_ in self.filters)
            other_in_self = all(filter_ in self.filters for filter_ in other.filters)
            return self_in_other and other_in_self
        return False
