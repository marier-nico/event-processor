"""Contains functions used for invoking processors for events."""
from typing import Dict, Any, Tuple

from .exceptions import EventProcessorInvocationException, EventProcessorDependencyException
from .state import PROCESSORS, Processor, DEPENDENCY_FACTORIES


def invoke(event: Dict) -> Any:
    """Invoke an event processor for the given event.

    The correct processor will automatically be selected based on the event, and its dependencies will be automatically
    created and injected.

    :param event: The raw event.
    :return: The value returned by the processor.
    :raises EventProcessorInvocationException: When no processor is found for the event.
    :raises EventProcessorDependencyException: When a factory required by a processor was not registered.
    :raises EventProcessorDependencyException: When the processor does not accept the right number of args.
    :raises EventProcessorDependencyException: When the pre-processor does not accept the right number of args.
    """
    processor = find_processor_for_event(event)
    dependencies = get_dependencies_for_processor(processor)

    acceptable_number_of_args = {1, 1 + len(dependencies)}
    if processor.pre_processor.__code__.co_argcount not in acceptable_number_of_args:
        raise EventProcessorDependencyException(
            "Wrong number of arguments for pre-processor", processor.pre_processor, processor.dependencies
        )
    if processor.fn.__code__.co_argcount not in acceptable_number_of_args:
        raise EventProcessorDependencyException(
            "Wrong number of arguments for processor", processor.fn, processor.dependencies
        )

    processor_dependencies = dependencies if processor.fn.__code__.co_argcount != 1 else ()
    pre_processor_dependencies = dependencies if processor.pre_processor.__code__.co_argcount != 1 else ()

    return processor.fn(processor.pre_processor(event, *pre_processor_dependencies), *processor_dependencies)


def find_processor_for_event(event: Dict) -> Processor:
    """Find the processor that should process a given event.

    To be selected, a processor's filters must all match the event. If multiple processors match the event, the
    processor with more filters will be selected (which means the most specific processor will be used). When multiple
    processors with the same number of filters match, the first one to have been registered will be used. This is
    dependendant on Python's import system.

    :param event: The raw event.
    :return: The processor to call.
    :raises EventProcessorInvocationException: When no processor is found for the event.
    """
    longest_match, best_processor = -1, None
    for filters, processor in PROCESSORS.items():
        if len(filters) > longest_match and event_matches_filters(event, filters):
            longest_match, best_processor = len(filters), processor

    if best_processor is None:
        raise EventProcessorInvocationException("No processor found for the event", event)

    return best_processor


def event_matches_filters(event: Dict, filters: Tuple[Tuple[str, Any], ...]) -> bool:
    """Verify that an event matches a set of filters.

    If the value in a filter is :py:class:`typing.Any`, any value in the event will be accepted, regardless of what it
    is, as long as it exists at the filter's path.

    :param event: The raw event.
    :param filters: The filters to check on the event.
    :return: True when the filters match the event, False otherwise.
    """
    for path, value in filters:

        current_value = event
        for path_component in path.split("."):
            try:
                current_value = current_value[path_component]
            except (TypeError, KeyError):
                return False

        if value is not Any and current_value != value:
            return False

    return True


def get_dependencies_for_processor(processor: Processor) -> Tuple[Any, ...]:
    """Create the dependencies for a processor.

    Simply create an instance for each dependency by passing the dependency names to the factory and storing the result.

    :param processor: The processor to create dependencies for.
    :return: A tuple of all the dependencies.
    :raises EventProcessorDependencyException: When a dependency factory does not exist.
    """
    dependencies = []
    for dependency_factory_name, dependency_names in processor.dependencies.items():

        factory = DEPENDENCY_FACTORIES.get(dependency_factory_name)
        if factory is None:
            raise EventProcessorDependencyException(
                f"Nonexistent factory '{dependency_factory_name}'", processor.fn, processor.dependencies
            )

        for dependency_name in dependency_names:
            dependencies.append(factory(dependency_name))

    return tuple(dependencies)
