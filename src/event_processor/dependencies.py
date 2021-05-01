"""Dependency injection and management facilities."""
import inspect
from typing import Callable, Any, Optional, Dict, Tuple


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


def call_with_injection(callable_: Callable, cache: Optional[dict] = None, *args, **kwargs) -> Optional[Any]:
    """Call a callable and inject required dependencies.

    Note that keyword args that have the same name as the parameter used for a dependency will be overwritten with the
    dependency's injected value.

    :param callable_: The callable to call
    :param cache: The dependency cache to use
    :param args: The args to pass to the callable
    :param kwargs: The kwargs to pass to the callable
    :return: The return value of the callable
    """
    dependencies = get_required_dependencies(callable_)
    for arg_name, dependency in dependencies.items():
        kwargs[arg_name], cacheable = resolve(dependency, cache)

    return callable_(*args, **kwargs)


def resolve(dependency: Depends, cache: Optional[dict] = None) -> Tuple[Optional[Any], bool]:
    """Resolve a dependency into a value.

    The resulting values from dependencies are cached and re-used if a cache is supplied and the dependency itself
    does not explicitly state that it does not want to be cached. Also, any dependency that depends on another
    dependency where caching has been disabled will also not be cached (because the sub-value may change, which may in
    turn change the value of the current dependency).

    :param dependency: The dependency to resolve
    :param cache: The cache for previously resolved dependencies
    :return: The tuple (resolved_value, cacheable)
    """
    if cache and dependency in cache:
        return cache[dependency]

    cacheable = dependency.cache
    required_dependencies = get_required_dependencies(dependency.callable)
    for arg_name, required_dependency in required_dependencies.items():
        required_dependencies[arg_name], cacheable_dep = resolve(required_dependency, cache)
        cacheable = cacheable and cacheable_dep

    value = dependency.callable(**required_dependencies)

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
