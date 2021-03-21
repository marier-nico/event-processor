from typing import Dict, Callable, Any

from .exceptions import EventProcessorDecorationException
from .pre_processors import passthrough
from .state import PROCESSORS, Processor, DEPENDENCY_FACTORIES


def processor(filter_expr: Dict[str, Any], pre_processor: Callable[[Dict], Any] = passthrough, **kwargs):
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
        if set(search) in (set(elm) for elm in PROCESSORS.keys()):
            raise EventProcessorDecorationException(
                f"The pattern '{filter_expr}' is already handled by another processor", fn
            )

        PROCESSORS[search] = Processor(fn=fn, pre_processor=pre_processor, dependencies=kwargs)
        return fn

    return decorate


def dependency_factory(fn: Callable):
    """Register a dependency factory.

    The name of the function will be the name of the factory, so this is what must be used in processor decorators.
    Also, the function must take a single string parameter and return a dependency based on that.

    :param fn: The function that will act as a factory.
    :raises EventProcessorDecorationException: When a factory is already registered for that name.
    :raises EventProcessorDecorationException: When the decorated function does not have a single argument.
    """
    factory_name = fn.__code__.co_name
    if factory_name in DEPENDENCY_FACTORIES.keys():
        raise EventProcessorDecorationException(
            f"There is already a registered dependency factory named '{factory_name}'", fn
        )
    if fn.__code__.co_argcount != 1:
        raise EventProcessorDecorationException("The function does not accept a single argument", fn)

    DEPENDENCY_FACTORIES[factory_name] = fn
    return fn
