"""Exceptions for event processor."""
from typing import Callable, Dict, Tuple


class EventProcessorException(BaseException):
    """General exception for the event-processor library."""

    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg

    def __repr__(self):
        return f"An error occured related to event processors: {self.msg}"

    def __str__(self):
        return self.__repr__()


class EventProcessorDecorationException(EventProcessorException):
    """Exception for failures while wrapping processors."""

    def __init__(self, msg: str, wrapped_fn: Callable):
        super().__init__(msg)
        self.wrapped_fn = wrapped_fn

    def __repr__(self):
        return f"Event processor decoration error for function '{self.wrapped_fn.__code__.co_name}': {self.msg}"

    def __str__(self):
        return self.__repr__()


class EventProcessorInvocationException(EventProcessorException):
    """Exception for failures in invocation."""

    def __init__(self, msg: str, event: Dict):
        super().__init__(msg)
        self.event = event

    def __repr__(self):
        return f"Event processor invocation error for event '{self.event}': {self.msg}"

    def __str__(self):
        return self.__repr__()


class EventProcessorDependencyException(EventProcessorException):
    """Exception for failures in dependencies."""

    def __init__(self, msg: str, wrapped_fn: Callable, dependencies: Dict[str, Tuple[str, ...]]):
        super().__init__(msg)
        self.wrapped_fn = wrapped_fn
        self.dependencies = dependencies

    def __repr__(self):
        return f"Dependency error in function '{self.wrapped_fn.__code__.co_name}': {self.msg}"

    def __str__(self):
        return self.__repr__()
