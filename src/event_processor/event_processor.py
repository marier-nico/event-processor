"""Contains the EventProcessor class."""
import inspect
from types import ModuleType
from typing import Dict, Callable, Any, Tuple

from .dependencies import (
    get_required_dependencies,
    get_event_dependencies,
    Event,
    Depends,
    get_pydantic_dependencies,
    get_scalar_value_dependencies,
)
from .exceptions import (
    FilterError,
    InvocationError,
)
from .filters import Filter
from .invocation_strategies import InvocationStrategies
from .util import load_all_modules_in_package


class EventProcessor:
    """A self-contained event processor."""

    def __init__(self, invocation_strategy: InvocationStrategies = InvocationStrategies.FIRST_MATCH):
        self.processors: Dict[Tuple[Filter, int], Callable] = {}
        self.dependency_cache: Dict[Depends, Any] = {}
        self.invocation_strategy = invocation_strategy

    def add_subprocessors_in_package(self, package: ModuleType):
        """Add all the processors found in all modules of a package as subprocessors.

        Note that you should specify an actual package, and not just the name of a package.

        :param package: The package that should be searched for event processors
        """
        modules_in_package = load_all_modules_in_package(package)
        for module in modules_in_package:
            module_contents = dir(module)
            for item_name in module_contents:
                item = getattr(module, item_name)
                if isinstance(item, EventProcessor):
                    self.add_subprocessor(item)

    def add_subprocessors(self, *subprocessors: "EventProcessor"):
        """Add multiple subprocessors at once.

        :param subprocessors: The tuple of subprocessors
        """
        for subprocessor in subprocessors:
            self.add_subprocessor(subprocessor)

    def add_subprocessor(self, subprocessor: "EventProcessor"):
        """Add a subprocessor to this event processor

        :param subprocessor: The other event processor to add
        """
        for filter_with_rank, processor in subprocessor.processors.items():
            if filter_with_rank in self.processors:
                raise FilterError(f"The filter '{filter_with_rank[0]}' is already handled by another processor")
            self.processors[filter_with_rank] = processor

    def processor(self, event_filter: Filter, rank: int = 0):
        """Register a new processor with the given filter and rank.

        :param event_filter: The filter for which to match events
        :param rank: This processor's rank (when there are multiple matches for a single event)
        """

        def decorate(fn):
            if not processor_params_are_valid(fn):
                raise FilterError(
                    f"The processor '{fn}' expects some invalid parameters "
                    f"(only dependencies, the event and pydantic models (if pydantic is installed) are allowed)"
                )
            if (event_filter, rank) in self.processors:
                raise FilterError(f"The filter '{event_filter}' ia already handled by another processor")

            self.processors[(event_filter, rank)] = fn
            return fn

        return decorate

    def invoke(self, event: Dict) -> Any:
        """Invoke the correct processor for an event.

        There may be multiple processors invoked, depending on the invocation strategy.

        :param event: The event to find a processor for
        :return: The return value of the processor
        """
        matching, highest_rank = [], float("-inf")
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
    """Verify that a processor's params are valid.

    :param processor: The processor to check
    :return: True if they are valid, False otherwise
    """
    dependencies = get_required_dependencies(processor)
    event_dependencies = get_event_dependencies(processor)
    pydantic_dependencies = get_pydantic_dependencies(processor)
    scalar_dependencies = get_scalar_value_dependencies(processor)

    non_scalars = len(dependencies) + len(event_dependencies) + len(pydantic_dependencies)
    scalars = len(scalar_dependencies) - non_scalars

    return scalars + non_scalars == len(inspect.signature(processor).parameters)
