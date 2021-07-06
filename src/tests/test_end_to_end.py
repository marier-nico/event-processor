from unittest.mock import Mock

import pytest
from pydantic.color import Color

from src.event_processor.dependencies import Event, Depends
from src.event_processor.event_processor import EventProcessor
from src.event_processor.filters import Eq, Exists, Accept, Dyn
from src.event_processor.invocation_strategies import InvocationStrategies


@pytest.fixture
def event_processor():
    return EventProcessor()


def test_simple_filtering(event_processor):
    @event_processor.processor(Eq("top.mid.low", "val"))
    def my_processor(event: Event):
        return event["top"]["mid"]["low"]

    result = event_processor.invoke({"top": {"mid": {"low": "val", "other": 1234}}})

    assert result.returned_value == "val"


@pytest.mark.parametrize("test_event, ret", [({"key": "val"}, "val"), ({"key": 123}, 123), ({"key": None}, None)])
def test_any_filter(test_event, ret, event_processor):
    @event_processor.processor(Exists("key"))
    def my_processor(event: Event):
        return event["key"]

    result = event_processor.invoke(test_event)

    assert result.returned_value == ret


def test_simple_pre_processing(event_processor):
    def pre_processor(event: Event):
        return event["user"]

    @event_processor.processor(Exists("user"))
    def my_processor(user_dict=Depends(pre_processor)):
        return user_dict

    result = event_processor.invoke({"user": {"name": "John"}})

    assert result.returned_value == {"name": "John"}


def test_processor_with_dependencies(event_processor):
    dependency_mock = Mock()

    def get_dependency():
        return dependency_mock

    @event_processor.processor(Accept())
    def my_processor(_event: Event, dep: Mock = Depends(get_dependency)):
        return dep

    result = event_processor.invoke({})

    assert result.returned_value is dependency_mock


def test_pre_processor_with_dependencies(event_processor):
    dependency_mock = Mock()

    def dep_factory():
        return dependency_mock

    def pre_processor(_event: Event, dep=Depends(dep_factory)):
        return dep

    @event_processor.processor(Accept())
    def my_processor(dep_from_pre_processor=Depends(pre_processor)):
        return dep_from_pre_processor

    result = event_processor.invoke({})

    assert result.returned_value is dependency_mock


def test_ambiguous_filters_with_rank(event_processor):
    mock_a = Mock()
    mock_b = Mock()

    @event_processor.processor(Exists("a"))
    def a_processor():
        mock_a()

    @event_processor.processor(Eq("a", "b"), rank=1)
    def b_processor():
        mock_b()

    event_processor.invoke({"a": "b"})

    mock_a.assert_not_called()
    mock_b.assert_called_once()


def test_ambiguous_filters_with_no_rank(event_processor):
    mock_a = Mock()
    mock_b = Mock()

    @event_processor.processor(Exists("a"))
    def a_processor():
        mock_a()

    @event_processor.processor(Eq("a", "b"))
    def b_processor():
        mock_b()

    event_processor.invoke({"a": "b"})

    mock_a.assert_called_once()
    mock_b.assert_not_called()


def test_ambiguous_filters_with_no_rank_and_non_default_invocation_strategy():
    event_processor = EventProcessor(invocation_strategy=InvocationStrategies.NO_MATCHES)
    mock_a = Mock()
    mock_b = Mock()

    @event_processor.processor(Exists("a"))
    def a_processor():
        mock_a()

    @event_processor.processor(Eq("a", "b"))
    def b_processor():
        mock_b()

    event_processor.invoke({"a": "b"})

    mock_a.assert_not_called()
    mock_b.assert_not_called()


def test_dynamic_filters_with_lambda_function(event_processor):
    filter_a = Dyn(lambda e: e["messages"][0].get("process") is True)
    mock_a = Mock()
    mock_b = Mock()

    @event_processor.processor(Accept(), rank=-1)
    def default_processor():
        mock_b()

    @event_processor.processor(filter_a)
    def a_processor():
        mock_a()

    event_processor.invoke({"messages": [{"process": True}]})
    event_processor.invoke({"messages": [{"process": False}]})

    mock_a.assert_called_once()
    mock_b.assert_called_once()


def test_dynamic_filters_with_dedicated_function(event_processor):
    mock_a = Mock()
    mock_b = Mock()

    def some_dependency():
        return 0

    def my_filter(event: Event, dep_value: int = Depends(some_dependency)):
        return event["key"] == dep_value

    @event_processor.processor(Dyn(my_filter))
    def my_processor():
        mock_a()

    @event_processor.processor(Accept(), rank=-1)
    def default_processor():
        mock_b()

    event_processor.invoke({"key": 0})
    event_processor.invoke({"key": 1})

    mock_a.assert_called_once()
    mock_b.assert_called_once()


def test_scalar_dependencies_for_basic_values(event_processor):
    @event_processor.processor(Accept())
    def my_processor(my_value: str):
        return my_value

    result = event_processor.invoke({"my_value": "asdf"})

    assert result.returned_value == "asdf"


def test_scalar_dependencies_for_pydantic_field_types(event_processor):
    @event_processor.processor(Accept())
    def my_processor(my_color: Color):
        return my_color

    result = event_processor.invoke({"my_color": "#ffffff"})

    assert result.returned_value.as_named() == "white"
