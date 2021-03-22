"""Contains the EventProcessor class."""
from typing import Dict, Callable, Any, Tuple

from .exceptions import (
    EventProcessorDecorationException,
    EventProcessorDependencyException,
    EventProcessorInvocationException,
)
from .pre_processors import passthrough
from .processor import Processor


class EventProcessor:
    def __init__(self):
        self.processors: Dict[Tuple[Tuple[str, Any], ...], Processor] = dict()
        self.dependency_factories: Dict[str, Callable] = dict()

    def processor(self, filter_expr: Dict[str, Any], pre_processor: Callable[[Dict], Any] = passthrough, **kwargs):
        """Decorate event processors.

        Filter expressions are used to determine when a given processor should be called. A processor will be called when
        a specific value is found at a given path in the input event. The key for filter expressions should be a
        dot-separated string to reach different levels of nesting in the input event. For example, the filter expression
        ``{"top.middle.lower": "val"}`` will match the event ``{"top": {"middle": {"lower": "val"}}}``.

        **Filter Values**

        - Basic Python type: The processor will be invoked if the value in the filter is equal to the value at the path \
            given by the filter key, in the input event.
        - typing.Any: The processor will be invoked if a value exists at the path given by the filter key (regardless of \
            what it is).

        **Default Processor**

        It's possible to create a processor with a filter expression that will match any event. Simply pass in an empty
        dict, and the processor will act as a fallback to call any time other processors do not match. This is important
        if you want default processing, because otherwise an exception is raised when no processor is found.

        Pre-processors are just functions that will transform the input event. By default, no transformation occurs, so the
        input event is directly passed through to the processor, but it's possible to do anything with them. For example,
        create an instance of a dataclass. In that case, the processor will not be called with the input event, it will be
        passed the output of the pre-processor.

        The additional keyword arguments are used to specify dependencies to be injected into the processor's arguments.
        The format should be ``<dependency_factory_name>=(<client_name1>, <client_name2>)``. The dependency factory name
        needs to have been previously registered through :py:func:`dependency_factory`. For example :

        .. code-block:: python

            @dependency_factory
            def boto_clients(client_name: str):
                return boto3.client(client_name)

            @processor({"deep.deep.down", "value"}, boto_clients=("ssm",))
            def my_processor(event, ssm_client):
                pass

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

        The correct processor will automatically be selected based on the event, and its dependencies will be automatically
        created and injected.

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
        processor with more filters will be selected (which means the most specific processor will be used). When multiple
        processors with the same number of filters match, the first one to have been registered will be used. This is
        dependendant on Python's import system.

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

    def _get_dependencies_for_processor(self, processor: Processor) -> Tuple[Any, ...]:
        """Create the dependencies for a processor.

        Simply create an instance for each dependency by passing the dependency names to the factory and storing the result.

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
