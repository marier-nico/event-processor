from unittest.mock import Mock

import pytest

from src.event_processor.dependencies import Depends, Event
from src.event_processor.event_processor import EventProcessor, processor_params_are_valid
from src.event_processor.exceptions import (
    EventProcessorException,
    EventProcessorDecorationException,
    EventProcessorInvocationException,
)
from src.event_processor.filters import Exists, Accept

MOD_PATH = "src.event_processor.event_processor"


@pytest.fixture
def event_processor():
    return EventProcessor()


def test_add_subprocessor_adds_subprocessor(event_processor):
    other_event_processor = EventProcessor()
    other_event_processor.processors[Accept()] = lambda: 0

    event_processor.add_subprocessor(other_event_processor)

    assert len(event_processor.processors) == 1


def test_add_subprocessor_raises_for_existing_filters(event_processor):
    other_event_processor = EventProcessor()
    other_event_processor.processors[Accept()] = lambda: 0
    event_processor.processors[Accept()] = lambda: 1

    with pytest.raises(EventProcessorException):
        event_processor.add_subprocessor(other_event_processor)


def test_processor_registers_a_processor(event_processor):
    filter_ = Exists("a")

    @event_processor.processor(filter_)
    def a_test():
        pass

    assert len(event_processor.processors) == 1


def test_processor_raises_exception_when_filter_exists(event_processor):
    filter_ = Exists("a")
    event_processor.processors[filter_] = 0

    with pytest.raises(EventProcessorDecorationException):

        @event_processor.processor(filter_)
        def a_test():
            pass


def test_processor_raises_exception_when_the_processor_takes_invalid_params(event_processor):

    with pytest.raises(EventProcessorDecorationException):

        @event_processor.processor(Accept())
        def fn(_x):
            pass


def test_invoke_calls_matching_processor(event_processor):
    filter_ = Exists("a")
    called = False

    @event_processor.processor(filter_)
    def a_test():
        nonlocal called
        called = True

    event_processor.invoke({"a": 0})
    assert called is True


def test_invoke_raises_for_no_matching_processors(event_processor):

    with pytest.raises(EventProcessorInvocationException):
        event_processor.invoke({"a": 0})


def test_invoke_returns_the_processor_return_value(event_processor):
    result_mock = Mock()
    event_processor.processors[Accept()] = lambda: result_mock

    result = event_processor.invoke({"a": 0})

    assert result is result_mock


def test_invoke_invokes_the_most_specific_matching_processor(event_processor):
    event_processor.processors[Accept()] = lambda: 0
    event_processor.processors[Exists("a") & Exists("b")] = lambda: 1
    event_processor.processors[Exists("a") | Exists("b") | Exists("c")] = lambda: 2

    result = event_processor.invoke({"a": 0, "b": 1})

    assert result is 1


def test_invoke_injects_event_into_processor(event_processor):
    event = {"a": 0}
    received_event = False

    @event_processor.processor(Accept())
    def fn(ev: Event):
        nonlocal received_event
        received_event = ev == event

    event_processor.invoke(event)

    assert received_event is True


def test_invoke_injects_dependencies_into_processor(event_processor):
    event = {"a": 0}
    dependency_result = Mock()

    @event_processor.processor(Accept())
    def fn(dep: Mock = Depends(lambda: dependency_result)):
        dep.method()

    event_processor.invoke(event)

    dependency_result.method.assert_called_once()


def test_processor_params_are_valid_returns_true_for_valid_params():
    def processor(_a: Event, _b: Event, _c=Depends(Mock())):
        pass

    assert processor_params_are_valid(processor) is True


def test_processor_params_are_valid_returns_false_for_invalid_params():
    def processor(_a: Event, _b: Event, _c=Depends(Mock()), _d=0):
        pass

    assert processor_params_are_valid(processor) is False
