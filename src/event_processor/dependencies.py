from typing import Callable, Any, Optional, List


class Depends:
    def __init__(self, callable_: Callable, cache: bool = True):
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


def resolve(dependency: Depends, cache: Optional[dict] = None) -> Optional[Any]:
    if cache and dependency in cache:
        return cache[dependency]

    value = dependency.callable()
    if cache is not None and dependency.cache:
        cache[dependency] = value

    return value


def get_required_dependencies(callable_: Callable) -> List[Depends]:
    return []
