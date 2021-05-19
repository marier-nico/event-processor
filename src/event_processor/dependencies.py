"""Dependency injection and management facilities."""
import inspect
import typing
from typing import Callable, Any, Optional, Dict, Tuple, List

from .exceptions import DependencyError

try:
    from pydantic import BaseModel, create_model

    _has_pydantic = True
except ImportError:  # pragma: no cover
    _has_pydantic = False

try:
    from typing import get_args, get_origin  # type: ignore
except ImportError:  # pragma: no cover
    from src.event_processor.util import py37_get_origin as get_origin
    from src.event_processor.util import py37_get_args as get_args


class Event(dict):
    """Type to wrap a dict to be used as a dependency."""

    def __init__(self, dict_event: dict):
        super().__init__(dict_event)


class Depends:
    """Class to designate a dependency"""

    def __init__(self, callable_: Callable, cache: bool = True):
        """Create a dependency.

        :param callable_: The callable on which there is a dependency
        :param cache: Whether or not to cache the value resulting from this dependency
        """
        self.callable = callable_
        self.cache = cache

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.callable is other.callable and self.cache is other.cache:
                return True
        return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.callable, self.cache))


def call_with_injection(
    callable_: Callable, event: Optional[Event] = None, cache: Optional[dict] = None
) -> Optional[Any]:
    """Call a callable and inject required dependencies.

    Note that keyword args that have the same name as the parameter used for a dependency will be overwritten with the
    dependency's injected value.

    :param callable_: The callable to call
    :param event: The event for the current invocation
    :param cache: The dependency cache to use
    :return: The return value of the callable
    """
    value, _cacheable = resolve(Depends(callable_, cache=False), event=event, cache=cache)
    return value


def resolve(
    dependency: Depends, event: Optional[Event] = None, cache: Optional[dict] = None
) -> Tuple[Optional[Any], bool]:
    """Resolve a dependency into a value.

    The resulting values from dependencies are cached and re-used if a cache is supplied and the dependency itself
    does not explicitly state that it does not want to be cached. Also, any dependency that depends on another
    dependency where caching has been disabled will also not be cached (because the sub-value may change, which may in
    turn change the value of the current dependency).

    :param dependency: The dependency to resolve
    :param event: The event for the current invocation
    :param cache: The cache for previously resolved dependencies
    :return: The tuple (resolved_value, cacheable)
    :raises: pydantic.error_wrappers.ValidationError if the event cannot be parsed into a pydantic model
    """
    if cache and dependency in cache:
        return cache[dependency], True
    cacheable = dependency.cache

    resolved_dependencies: Dict[str, Any] = {}
    for arg_name in get_event_dependencies(dependency.callable):
        resolved_dependencies[arg_name] = event

    for arg_name, model in get_pydantic_dependencies(dependency.callable).items():
        resolved_dependencies[arg_name] = model.parse_obj(event)

    for arg_name, required_dependency in get_required_dependencies(dependency.callable).items():
        resolved_dependencies[arg_name], cacheable_dep = resolve(required_dependency, event=event, cache=cache)
        cacheable = cacheable and cacheable_dep

    scalar_dependencies = [
        dependency
        for dependency in get_scalar_value_dependencies(dependency.callable)
        if dependency.name not in resolved_dependencies
    ]
    resolved_scalar_dependencies = resolve_scalar_value_dependencies(scalar_dependencies, event=event)
    resolved_dependencies.update(resolved_scalar_dependencies)

    value = dependency.callable(**resolved_dependencies)

    if cache is not None and cacheable:
        cache[dependency] = value

    return value, cacheable


def get_required_dependencies(callable_: Callable) -> Dict[str, Depends]:
    """Get the required dependencies for a callable.

    :param callable_: The callable for which to get dependencies
    :return: A mapping of callable argument names to dependencies
    """
    signature = inspect.signature(callable_)
    required_dependencies = {
        name: arg.default
        for name, arg in signature.parameters.items()
        if arg.default is not inspect.Parameter.empty and isinstance(arg.default, Depends)
    }
    return required_dependencies


def get_event_dependencies(callable_: Callable) -> List[str]:
    """Get the parameter names for event dependencies.

    :param callable_: The callable for which to get dependencies
    :return: A list of the parameters requiring the event
    """
    signature = inspect.signature(callable_)
    return [name for name, arg in signature.parameters.items() if arg.annotation is Event]


def get_pydantic_dependencies(callable_: Callable) -> Dict[str, "BaseModel"]:
    """Get the required models and their parameter names for a callable.

    :param callable_: The callable for which to get dependencies
    :return: A mapping of argument names to pydantic model types
    """
    if _has_pydantic:
        signature = inspect.signature(callable_)
        return {
            name: arg.annotation
            for name, arg in signature.parameters.items()
            if inspect.isclass(arg.annotation) and issubclass(arg.annotation, BaseModel)
        }
    else:
        return {}


def get_scalar_value_dependencies(callable_: Callable) -> List[inspect.Parameter]:
    """Get the scalar value dependencies for a callable.

    :param callable_: The callable for which to get dependencies
    :return: A view of the parameters that represent dependencies
    """
    signature = inspect.signature(callable_)
    return [
        param for param in signature.parameters.values() if param.kind not in {param.VAR_POSITIONAL, param.VAR_KEYWORD}
    ]


def resolve_scalar_value_dependencies(
    scalar_dependencies: List[inspect.Parameter], event: Optional[Event]
) -> Dict[str, Any]:
    """Resolve the scalar dependencies to values contained in the event.

    Values will be resolved differently depending on whether or not pydantic is installed.

    :param scalar_dependencies: The dependencies to resolve
    :param event: The event from which to get values
    :return: A new dict with resolved dependency values
    """
    if event is None:
        event = Event({})

    if _has_pydantic:
        return resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, event)
    else:
        return resolve_scalar_value_dependencies_without_pydantic(scalar_dependencies, event)


def resolve_scalar_value_dependencies_without_pydantic(
    scalar_dependencies: List[inspect.Parameter], event: Event
) -> Dict[str, Any]:
    """Resolve the scalar dependencies to values contained in the event without using pydantic.

    This function does not validate the types of values passed into the event to ensure they match
    the type annotations of the dependencies. To get validation for those types, make sure pydantic
    is installed.

    :param scalar_dependencies: The dependencies to resolve
    :param event: The event from which to get values
    :return: A new dict with resolved dependency values
    """
    resolved = {}
    for param in scalar_dependencies:
        try:
            resolved[param.name] = event[param.name]
        except KeyError:
            raise DependencyError(f"No value found in event for param '{param.name}'")

    return resolved


def resolve_scalar_value_dependencies_with_pydantic(
    scalar_dependencies: List[inspect.Parameter], event: Event
) -> Dict[str, Any]:
    """Resolve the scalar dependencies to values contained in the event with pydantic.

    This function does validation for the types of values passed into the event. Since this uses
    pydantic, it's possible to use any pydantic types such as PaymentCardNumber, for example.

    :param scalar_dependencies: The dependencies to resolve
    :param event: The event from which to get values
    :return: A new dict with resolved and validated dependency values
    """
    model_params = {}
    for param in scalar_dependencies:
        param_type = Any if param.annotation is inspect.Parameter.empty else param.annotation
        if param.default is inspect.Parameter.empty:
            if get_origin(param_type) is typing.Union and type(None) in get_args(param_type):
                param_default = None
            else:
                param_default = ...
        else:
            param_default = param.default

        model_params[param.name] = (param_type, param_default)

    pydantic_model = create_model("ScalarDependencies", **model_params)  # type: ignore
    filled_model = pydantic_model(**event)

    return filled_model.dict()
