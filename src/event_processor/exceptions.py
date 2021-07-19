"""Exceptions for event processor."""


class EventProcessorError(BaseException):
    """General exception for the event-processor library."""


class FilterError(EventProcessorError):
    """Exception for failures related to filters."""


class InvocationError(EventProcessorError):
    """Exception for failures in invocation."""


class DependencyError(EventProcessorError):
    """Exceptions for failures while resolving dependencies."""


class NoValueError(EventProcessorError):
    """Exception for when a value is not present in a given context."""
