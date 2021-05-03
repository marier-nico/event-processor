"""Contains the EventProcessor class."""
import inspect
from typing import Dict, Callable, Any

from .dependencies import get_required_dependencies, get_event_dependencies, call_with_injection, Event
from .exceptions import (
    FilterError,
    InvocationError,
)
from .filters import Filter


class EventProcessor:
    def __init__(self):
        self.processors: Dict[Filter, Callable] = {}
        self.dependency_cache = {}

    def add_subprocessor(self, subprocessor: "EventProcessor"):
        for filter_, processor in subprocessor.processors.items():
            if filter_ in self.processors:
                raise FilterError(f"The filter '{filter_}' is already handled by another processor")
            self.processors[filter_] = processor

    def processor(self, event_filter: Filter):
        def decorate(fn):
            if not processor_params_are_valid(fn):
                raise FilterError(
                    f"The processor '{fn}' expects some invalid parameters "
                    f"(only dependencies and the event are allowed)"
                )
            if event_filter in self.processors:
                raise FilterError(f"The filter '{event_filter}' ia already handled by another processor")

            self.processors[event_filter] = fn
            return fn

        return decorate

    def invoke(self, event: Dict) -> Any:
        most_specific, specificity = None, 0
        for filter_, processor in self.processors.items():
            if filter_.matches(event):
                current_filter_specificity = filter_.get_match_specificity(event)

                if current_filter_specificity > specificity:
                    most_specific, specificity = processor, current_filter_specificity

        if most_specific is None:
            raise InvocationError(f"No matching processor for the event '{event}'")
        else:
            return call_with_injection(most_specific, event=Event(event), cache=self.dependency_cache)


def processor_params_are_valid(processor: Callable) -> bool:
    dependencies = get_required_dependencies(processor)
    event_dependencies = get_event_dependencies(processor)

    return len(dependencies) + len(event_dependencies) == len(inspect.signature(processor).parameters)
