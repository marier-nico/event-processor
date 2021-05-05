"""Contains the EventProcessor class."""
import inspect
from typing import Dict, Callable, Any, Tuple

from .dependencies import get_required_dependencies, get_event_dependencies, Event, Depends
from .exceptions import (
    FilterError,
    InvocationError,
)
from .filters import Filter
from .invocation_strategies import InvocationStrategies


class EventProcessor:
    def __init__(self, invocation_strategy: InvocationStrategies = InvocationStrategies.FIRST_MATCH):
        self.processors: Dict[Tuple[Filter, int], Callable] = {}
        self.dependency_cache: Dict[Depends, Any] = {}
        self.invocation_strategy = invocation_strategy

    def add_subprocessor(self, subprocessor: "EventProcessor"):
        for filter_with_rank, processor in subprocessor.processors.items():
            if filter_with_rank in self.processors:
                raise FilterError(f"The filter '{filter_with_rank[0]}' is already handled by another processor")
            self.processors[filter_with_rank] = processor

    def processor(self, event_filter: Filter, rank: int = 0):
        def decorate(fn):
            if not processor_params_are_valid(fn):
                raise FilterError(
                    f"The processor '{fn}' expects some invalid parameters "
                    f"(only dependencies and the event are allowed)"
                )
            if (event_filter, rank) in self.processors:
                raise FilterError(f"The filter '{event_filter}' ia already handled by another processor")

            self.processors[(event_filter, rank)] = fn
            return fn

        return decorate

    def invoke(self, event: Dict) -> Any:
        matching, highest_rank = [], 0
        for (filter_, rank), processor in self.processors.items():
            if filter_.matches(event):
                if rank > highest_rank:
                    matching, highest_rank = [processor], rank
                elif rank == highest_rank:
                    matching.append(processor)

        if matching:
            return self.invocation_strategy.value.invoke(matching, event=Event(event), cache=self.dependency_cache)
        else:
            raise InvocationError(f"No matching processor for the event '{event}'")


def processor_params_are_valid(processor: Callable) -> bool:
    dependencies = get_required_dependencies(processor)
    event_dependencies = get_event_dependencies(processor)

    return len(dependencies) + len(event_dependencies) == len(inspect.signature(processor).parameters)
