"""Contains the EventProcessor class."""
from typing import Dict, Callable, Any, Tuple

from .exceptions import (
    EventProcessorDecorationException,
    EventProcessorDependencyException,
    EventProcessorInvocationException,
    EventProcessorSubprocessorException,
)
from .pre_processors import passthrough
from .processor import Processor


class EventProcessor:
    def __init__(self):
        self.processors: Dict[Tuple[Tuple[str, Any], ...], Processor] = dict()
        self.dependency_factories: Dict[str, Callable] = dict()

    def add_subprocessor(self, subprocessor: "EventProcessor"):
        """Add a subprocessor for events.

        This will update the current event processor with all the processors of the subprocesor, which means that
        invoking the main processor with an event will have the same effect as invoking the correct subprocessor.

        Note that filters defined in subprocessors must not already exist in the main processor, otherwise an error
        will be raised.

        :param subprocessor: The subprocessor to add to the current processor.
        :raises EventProcessorSubprocessorException: When there is an overlap in filter expressions between the
            processor and subprocessor.
        """
        intersection = set(self.processors.keys()).intersection(subprocessor.processors.keys())
        if intersection != set():
            raise EventProcessorSubprocessorException("Overlap in subprocessor events", intersection)

        self.processors.update(subprocessor.processors)
        for factory_name, factory_fn in subprocessor.dependency_factories.items():
            if factory_name not in self.dependency_factories:
                self.dependency_factories[factory_name] = factory_fn

    def processor(self, filter_expr: Dict[str, Any], pre_processor: Callable[[Dict], Any] = passthrough, **kwargs):
        """Decorate event processors.

        **Important Considerations**

        - The keyword arg in the decorator must match the dependency factory function's name.
        - The arguments are passed in the following order : event, dependencies.
        - All dependencies for a factory are passed before moving onto the next factory.
        - The argument names are not important, but the order must be followed.

        :param filter_expr: A dict containing path-value pairs to call the right event processor.
        :param pre_processor: A pre-processor function to transform the event into another type.
        :param kwargs: A mapping of dependency-factory to tuple of dependencies for that factory.
        :raises EventProcessorDecorationException: When the filter expression is already associated to a handler.
        """

        def decorate(fn):
            search = tuple(elm for elm in filter_expr.items())
            if set(search) in (set(elm) for elm in self.processors.keys()):
                raise EventProcessorDecorationException(
                    f"The pattern '{filter_expr}' is already handled by another processor", fn
                )

            self.processors[search] = Processor(fn=fn, pre_processor=pre_processor, dependencies=kwargs)
            return fn

        return decorate

    def dependency_factory(self, fn: Callable):
        """Register a dependency factory.

        The name of the function will be the name of the factory, so this is what must be used in processor decorators.
        Also, the function must take a single string parameter and return a dependency based on that.

        :param fn: The function that will act as a factory.
        :raises EventProcessorDecorationException: When a factory is already registered for that name.
        :raises EventProcessorDecorationException: When the decorated function does not have a single argument.
        """
        factory_name = fn.__code__.co_name
        if factory_name in self.dependency_factories.keys():
            raise EventProcessorDecorationException(
                f"There is already a registered dependency factory named '{factory_name}'", fn
            )
        if fn.__code__.co_argcount != 1:
            raise EventProcessorDecorationException("The function does not accept a single argument", fn)

        self.dependency_factories[factory_name] = fn
        return fn

    def invoke(self, event: Dict) -> Any:
        """Invoke an event processor for the given event.

        The correct processor will automatically be selected based on the event, and its dependencies will be
        automatically created and injected.

        :param event: The raw event.
        :return: The value returned by the processor.
        :raises EventProcessorInvocationException: When no processor is found for the event.
        :raises EventProcessorDependencyException: When a factory required by a processor was not registered.
        :raises EventProcessorDependencyException: When the processor does not accept the right number of args.
        :raises EventProcessorDependencyException: When the pre-processor does not accept the right number of args.
        """
        processor = self._find_processor_for_event(event)
        dependencies = self._get_dependencies_for_processor(processor)

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

    def _find_processor_for_event(self, event: Dict) -> Processor:
        """Find the processor that should process a given event.

        To be selected, a processor's filters must all match the event. If multiple processors match the event, the
        processor with more filters will be selected (which means the most specific processor will be used). When
        multiple processors with the same number of filters match, the first one to have been registered will be used.
        This is dependendant on Python's import system.

        :param event: The raw event.
        :return: The processor to call.
        :raises EventProcessorInvocationException: When no processor is found for the event.
        """
        longest_match, best_processor = -1, None
        for filters, processor in self.processors.items():
            if len(filters) > longest_match and self._event_matches_filters(event, filters):
                longest_match, best_processor = len(filters), processor

        if best_processor is None:
            raise EventProcessorInvocationException("No processor found for the event", event)

        return best_processor

    @staticmethod
    def _event_matches_filters(event: Dict, filters: Tuple[Tuple[str, Any], ...]) -> bool:
        """Verify that an event matches a set of filters.

        If the value in a filter is :py:class:`typing.Any`, any value in the event will be accepted, regardless of what
        it is, as long as it exists at the filter's path.

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

    def _get_dependencies_for_processor(self, processor: Processor) -> Tuple[Any, ...]:
        """Create the dependencies for a processor.

        Simply create an instance for each dependency by passing the dependency names to the factory and storing the
        result.

        :param processor: The processor to create dependencies for.
        :return: A tuple of all the dependencies.
        :raises EventProcessorDependencyException: When a dependency factory does not exist.
        """
        dependencies = []
        for dependency_factory_name, dependency_names in processor.dependencies.items():

            factory = self.dependency_factories.get(dependency_factory_name)
            if factory is None:
                raise EventProcessorDependencyException(
                    f"Nonexistent factory '{dependency_factory_name}'", processor.fn, processor.dependencies
                )

            for dependency_name in dependency_names:
                dependencies.append(factory(dependency_name))

        return tuple(dependencies)
