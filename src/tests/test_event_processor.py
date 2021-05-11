from unittest.mock import Mock

import pytest

from src.event_processor.dependencies import Depends, Event
from src.event_processor.event_processor import EventProcessor, processor_params_are_valid
from src.event_processor.exceptions import (
    FilterError,
    InvocationError,
)
from src.event_processor.filters import Exists, Accept, Eq

MOD_PATH = "src.event_processor.event_processor"


@pytest.fixture
def event_processor():
    return EventProcessor()


def test_add_subprocessor_adds_subprocessor(event_processor):
    other_event_processor = EventProcessor()
    other_event_processor.processors[Accept(), 0] = lambda: 0

    event_processor.add_subprocessor(other_event_processor)

    assert len(event_processor.processors) == 1


def test_add_subprocessor_raises_for_existing_filters(event_processor):
    other_event_processor = EventProcessor()
    other_event_processor.processors[Accept(), 0] = lambda: 0
    event_processor.processors[Accept(), 0] = lambda: 1

    with pytest.raises(FilterError):
        event_processor.add_subprocessor(other_event_processor)


def test_processor_registers_a_processor(event_processor):
    filter_ = Exists("a")

    @event_processor.processor(filter_)
    def a_test():
        pass

    assert len(event_processor.processors) == 1


def test_processor_raises_exception_when_filter_exists(event_processor):
    filter_ = Exists("a")
    event_processor.processors[filter_, 0] = 0

    with pytest.raises(FilterError):

        @event_processor.processor(filter_)
        def a_test():
            pass


def test_processor_raises_exception_when_the_processor_takes_invalid_params(event_processor):

    with pytest.raises(FilterError):

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

    with pytest.raises(InvocationError):
        event_processor.invoke({"a": 0})


def test_invoke_returns_the_processor_return_value(event_processor):
    result_mock = Mock()
    event_processor.processors[Accept(), 0] = lambda: result_mock

    result = event_processor.invoke({"a": 0})

    assert result is result_mock


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


def test_invoke_calls_highest_ranking_processor(event_processor):
    event = {"a": 0}
    called_a = False
    called_b = False

    @event_processor.processor(Exists("a"))
    def fn_a():
        nonlocal called_a
        called_a = True

    @event_processor.processor(Eq("a", 0), rank=1)
    def fn_b():
        nonlocal called_b
        called_b = True

    event_processor.invoke(event)

    assert called_a is False
    assert called_b is True


def test_invoke_calls_negative_rank_as_fallback(event_processor):
    called_a = False
    called_b = False

    @event_processor.processor(Accept(), rank=-1)
    def fn_a():
        nonlocal called_a
        called_a = True

    @event_processor.processor(Exists("a"))
    def fn_b():
        nonlocal called_b
        called_b = True

    event_processor.invoke({"not-a": 0})

    assert called_a is True
    assert called_b is False


def test_processor_params_are_valid_returns_true_for_valid_params():
    def processor(_a: Event, _b: Event, _c=Depends(Mock())):
        pass

    assert processor_params_are_valid(processor) is True


def test_processor_params_are_valid_returns_false_for_invalid_params():
    def processor(_a: Event, _b: Event, _c=Depends(Mock()), _d=0):
        pass

    assert processor_params_are_valid(processor) is False
