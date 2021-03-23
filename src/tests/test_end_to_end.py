from typing import Any

import pytest

from src.event_processor.event_processor import EventProcessor


@pytest.fixture
def event_processor():
    return EventProcessor()


def test_simple_filtering(event_processor):
    @event_processor.processor({"top.mid.low": "val"})
    def my_processor(event):
        return event["top"]["mid"]["low"]

    result = event_processor.invoke({"top": {"mid": {"low": "val", "other": 1234}}})

    assert result == "val"


@pytest.mark.parametrize("test_event, ret", [({"key": "val"}, "val"), ({"key": 123}, 123), ({"key": None}, None)])
def test_any_filter(test_event, ret, event_processor):
    @event_processor.processor({"key": Any})
    def my_processor(event):
        return event["key"]

    result = event_processor.invoke(test_event)

    assert result == ret


def test_simple_pre_processing(event_processor):
    def pre_processor(event):
        return event["user"]

    @event_processor.processor({"user": Any}, pre_processor=pre_processor)
    def my_processor(user_dict):
        return user_dict

    result = event_processor.invoke({"user": {"name": "John"}})

    assert result == {"name": "John"}


def test_processor_with_dependencies(event_processor):
    @event_processor.dependency_factory
    def dep_factory(dep_name):
        return dep_name

    @event_processor.processor({}, dep_factory=("dep",))
    def my_processor(_event, dep):
        return dep

    result = event_processor.invoke({})

    assert result == "dep"


def test_pre_processor_with_dependencies(event_processor):
    @event_processor.dependency_factory
    def dep_factory(dep_name):
        return dep_name

    def pre_processor(_event, dep):
        return dep

    @event_processor.processor({}, pre_processor=pre_processor, dep_factory=("dep",))
    def my_processor(dep_from_pre_processor):
        return dep_from_pre_processor

    result = event_processor.invoke({})

    assert result == "dep"
