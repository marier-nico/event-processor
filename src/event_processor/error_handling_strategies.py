from abc import ABC, abstractmethod
from enum import Enum
from typing import Type, Callable

from .result import Result


class ErrorHandlingStrategy(ABC):
    """Defines the interface of an error handling strategy."""

    @abstractmethod
    def invoke(self, callable_name: str, callable_: Callable) -> Result:
        """Invoke the callable with the error handling strategy.

        :param callable_name: The name of the callable to invoke
        :param callable_: The callable to invoke
        :return: A Result containing the result or error
        :raises: Potentially any exception coming from a processor
        """


class Bubble(ErrorHandlingStrategy):
    """Strategy to let errors bubble up to the invoker."""

    def invoke(self, callable_name: str, callable_: Callable) -> Result:
        """Invoke the bubble error handling strategy.

        :param callable_name: The name of the callable to execute
        :param callable_: The callable to execute
        :return: A Result containing the callable's return value if there was no exception
        :raises: Any exception that was raised in the callable
        """
        return Result(processor_name=callable_name, returned_value=callable_())


class SpecificBubble(ErrorHandlingStrategy):
    """Strategy to let specific errors bubble up to the invoker."""

    def __init__(self, *bubble_errors: Type[Exception]):
        self.bubble_errors = bubble_errors

    def invoke(self, callable_name: str, callable_: Callable) -> Result:
        """Invoke the specific bubble error handling strategy.

        :param callable_name: The name of the callable to execute
        :param callable_: The callable to execute
        :return: A Result containing the callable's return value or an exception that should not be bubbled
        :raises: Any exception that was passed in the constructor to be bubbled
        """
        try:
            return Result(processor_name=callable_name, returned_value=callable_())
        except Exception as e:
            for to_bubble in self.bubble_errors:
                if isinstance(e, to_bubble):
                    raise e

            return Result(processor_name=callable_name, raised_exception=e)


class Capture(ErrorHandlingStrategy):
    """Strategy to capture errors and add them to the returned result."""

    def invoke(self, callable_name: str, callable_: Callable) -> Result:
        """Invoke the capture error handling strategy.

        :param callable_name: The name of the callable to execute
        :param callable_: The callable to execute
        :return: A Result containing the callable's return value or an exception that was raised by the callable
        """
        try:
            return Result(processor_name=callable_name, returned_value=callable_())
        except Exception as e:
            return Result(processor_name=callable_name, raised_exception=e)


class SpecificCapture(ErrorHandlingStrategy):
    """Strategy to capture specific errors only."""

    def __init__(self, *capture_errors: Type[Exception]):
        self.capture_errors = capture_errors

    def invoke(self, callable_name: str, callable_: Callable) -> Result:
        """Invoke the specific capture error handling strategy.

        :param callable_name: The name of the callable to execute
        :param callable_: The callable to execute
        :return: A Result containing the callable's return value or an exception that should be captured
        :raises: Any exception that was not explicitly captured
        """
        try:
            return Result(processor_name=callable_name, returned_value=callable_())
        except Exception as e:
            for to_capture in self.capture_errors:
                if isinstance(e, to_capture):
                    return Result(processor_name=callable_name, raised_exception=e)

            raise e


class ErrorHandlingStrategies(Enum):
    """Enumeration of available error handling strategies."""

    BUBBLE = Bubble
    SPECIFIC_BUBBLE = SpecificBubble
    CAPTURE = Capture
    SPECIFIC_CAPTURE = SpecificCapture
