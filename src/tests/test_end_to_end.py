from unittest.mock import Mock

import pytest

from src.event_processor.dependencies import Event, Depends
from src.event_processor.event_processor import EventProcessor
from src.event_processor.filters import Eq, Exists, Accept


@pytest.fixture
def event_processor():
    return EventProcessor()


def test_simple_filtering(event_processor):
    @event_processor.processor(Eq("top.mid.low", "val"))
    def my_processor(event: Event):
        return event["top"]["mid"]["low"]

    result = event_processor.invoke({"top": {"mid": {"low": "val", "other": 1234}}})

    assert result == "val"


@pytest.mark.parametrize("test_event, ret", [({"key": "val"}, "val"), ({"key": 123}, 123), ({"key": None}, None)])
def test_any_filter(test_event, ret, event_processor):
    @event_processor.processor(Exists("key"))
    def my_processor(event: Event):
        return event["key"]

    result = event_processor.invoke(test_event)

    assert result == ret


def test_simple_pre_processing(event_processor):
    def pre_processor(event: Event):
        return event["user"]

    @event_processor.processor(Exists("user"))
    def my_processor(user_dict=Depends(pre_processor)):
        return user_dict

    result = event_processor.invoke({"user": {"name": "John"}})

    assert result == {"name": "John"}


def test_processor_with_dependencies(event_processor):
    dependency_mock = Mock()

    def get_dependency():
        return dependency_mock

    @event_processor.processor(Accept())
    def my_processor(_event: Event, dep: Mock = Depends(get_dependency)):
        return dep

    result = event_processor.invoke({})

    assert result is dependency_mock


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

    assert result is dependency_mock
