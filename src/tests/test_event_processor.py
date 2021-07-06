from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel

from src.event_processor.invocation_strategies import InvocationStrategies
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


@patch(f"{MOD_PATH}.load_all_modules_in_package", return_value=[])
def test_add_subprocessors_in_package_does_nothing_for_an_empty_package(event_processor):
    event_processor.add_subprocessors_in_package(Mock())

    assert len(event_processor.processors) == 0


def test_add_subprocessors_in_package_adds_subprocessors_contained_in_modules(event_processor):
    event_processor_1 = EventProcessor()
    event_processor_2 = EventProcessor()
    event_processor_1.processors[Accept(), 0] = [lambda: 0]
    event_processor_2.processors[Accept(), 1] = [lambda: 0]
    mock_modules = [Mock(x=event_processor_1), Mock(y=event_processor_2)]

    with patch(f"{MOD_PATH}.load_all_modules_in_package", return_value=mock_modules):
        event_processor.add_subprocessors_in_package(Mock())

    assert len(event_processor.processors) == 2


def test_add_subprocessor_adds_subprocessor(event_processor):
    other_event_processor = EventProcessor()
    other_event_processor.processors[Accept(), 0] = [lambda: 0]

    event_processor.add_subprocessor(other_event_processor)

    assert len(event_processor.processors) == 1


def test_add_subprocessor_adds_all_processors_with_matching_filters_and_ranks(event_processor):
    event_processor.processors[Accept(), 0] = [lambda: 0]
    other_event_processor = EventProcessor()
    other_event_processor.processors[Accept(), 0] = [lambda: 1, lambda: 2]

    event_processor.add_subprocessor(other_event_processor)

    assert len(event_processor.processors[Accept(), 0]) == 3


def test_add_subprocessors_can_add_multiple_subprocessors_at_once(event_processor):
    event_processor_1 = EventProcessor()
    event_processor_2 = EventProcessor()
    event_processor_1.processors[Accept(), 0] = [lambda: 0]
    event_processor_2.processors[Accept(), 1] = [lambda: 0]

    event_processor.add_subprocessors(event_processor_1, event_processor_2)

    assert len(event_processor.processors) == 2


def test_processor_registers_a_processor(event_processor):
    filter_ = Exists("a")

    @event_processor.processor(filter_)
    def a_test():
        pass

    assert len(event_processor.processors) == 1


def test_processor_registers_multiple_processors_with_identical_filters(event_processor):
    filter_a = Accept()
    filter_b = Accept()

    @event_processor.processor(filter_a)
    def a_test():
        pass

    @event_processor.processor(filter_b)
    def b_test():
        pass

    assert len(event_processor.processors) == 1
    assert len(event_processor.processors[Accept(), 0]) == 2


def test_processor_raises_exception_when_the_processor_takes_invalid_params(event_processor):

    with pytest.raises(FilterError):

        @event_processor.processor(Accept())
        def fn(*_args):
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
    event_processor.processors[Accept(), 0] = [lambda: result_mock]

    result = event_processor.invoke({"a": 0})

    assert result.returned_value is result_mock


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


def test_invoke_result_contains_processor_names():
    event_processor = EventProcessor(InvocationStrategies.ALL_MATCHES)

    @event_processor.processor(Exists("a"))
    def fn_a():
        pass

    @event_processor.processor(Exists("b"))
    def fn_b():
        pass

    results = event_processor.invoke({"a": 0, "b": 0})

    assert "fn_a" == results[0].processor_name
    assert "fn_b" == results[1].processor_name


def test_invoke_only_caches_for_each_invocation(event_processor):
    counter = 0

    def my_dependency():
        nonlocal counter
        counter = counter + 1
        return counter

    @event_processor.processor(Accept())
    def fn_a(counter_dependency: int = Depends(my_dependency, cache=True)):
        return counter_dependency

    result_1 = event_processor.invoke({})
    result_2 = event_processor.invoke({})

    assert result_1.returned_value == 1
    assert result_2.returned_value == 2


def test_processor_params_are_valid_returns_true_for_valid_params():
    def processor(_a: Event, _b: Event, _c: BaseModel, _d: str, _e=Depends(Mock())):
        pass

    assert processor_params_are_valid(processor) is True


def test_processor_params_are_valid_returns_false_for_invalid_params():
    def processor(_a: Event, _b: Event, _c: BaseModel, _d=Depends(Mock()), *_args, **_kwargs):
        pass

    assert processor_params_are_valid(processor) is False
