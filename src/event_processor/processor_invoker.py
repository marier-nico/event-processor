from typing import Dict, Any, Tuple, Optional

from src.event_processor.state import PROCESSORS, Processor, DEPENDENCY_FACTORIES
from src.event_processor.exceptions import EventProcessorInvocationException, EventProcessorDependencyException


def invoke(event: Dict):
    processor = find_processor_for_event(event)
    dependencies = get_dependencies_for_processor(processor)

    return processor.fn(processor.pre_processor(event), *dependencies)


def find_processor_for_event(event: Dict) -> Processor:
    longest_match, best_processor = -1, None
    for filters, processor in PROCESSORS.items():
        if len(filters) > longest_match and event_matches_filters(event, filters):
            longest_match, best_processor = len(filters), processor

    if best_processor is None:
        raise EventProcessorInvocationException("No processor found for the event", event)

    return best_processor


def event_matches_filters(event: Dict, filters: Tuple[Tuple[str, Any], ...]) -> bool:
    for path, value in filters:

        current_value: Optional[Dict] = event
        for path_component in path.split("."):
            if current_value is None:
                return False

            current_value = current_value.get(path_component)

        if value is not Any and current_value != value:
            return False

    return True


def get_dependencies_for_processor(processor: Processor) -> Tuple[Any, ...]:
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
