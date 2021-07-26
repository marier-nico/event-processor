import pytest

from src.event_processor.error_handling_strategies import Bubble, Capture, SpecificBubble, SpecificCapture


def test_bubble_raises_exceptions_from_callables():
    strategy = Bubble()
    some_array = []

    with pytest.raises(Exception):
        strategy.invoke("lambda", lambda: some_array[0])


def test_bubble_returns_result_containing_return_value_when_there_is_no_error():
    strategy = Bubble()
    some_array = ["a-value"]

    result = strategy.invoke("lambda", lambda: some_array[0])

    assert result.returned_value == "a-value"


def test_capture_returns_result_with_returned_value_when_there_is_no_error():
    strategy = Capture()
    some_array = ["a-value"]

    result = strategy.invoke("lambda", lambda: some_array[0])

    assert result.returned_value == "a-value"


def test_capture_returns_result_with_raised_exception_when_there_is_an_error():
    strategy = Capture()
    some_array = []

    result = strategy.invoke("lambda", lambda: some_array[0])

    assert result.returned_value is None
    assert isinstance(result.raised_exception, IndexError)


def test_specific_bubble_bubbles_specified_exception():
    strategy = SpecificBubble(IndexError)
    some_array = []

    with pytest.raises(IndexError):
        strategy.invoke("lambda", lambda: some_array[0])


def test_specific_bubble_does_not_bubble_unrelated_exceptions():
    strategy = SpecificBubble(KeyError)
    some_array = []

    result = strategy.invoke("lambda", lambda: some_array[0])

    assert isinstance(result.raised_exception, IndexError)


def test_specific_capture_captures_specified_exception():
    strategy = SpecificCapture(IndexError)
    some_array = []

    result = strategy.invoke("lambda", lambda: some_array[0])

    assert isinstance(result.raised_exception, IndexError)


def test_specific_capture_does_not_capture_unrelated_exceptions():
    strategy = SpecificCapture(KeyError)
    some_array = []

    with pytest.raises(IndexError):
        strategy.invoke("lambda", lambda: some_array[0])
