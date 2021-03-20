from typing import Any
from unittest.mock import patch

import pytest

from src.event_processor.state import PROCESSORS, DEPENDENCY_FACTORIES
from src.event_processor.processor_decorator import processor, dependency_factory
from src.event_processor.processor_invoker import invoke


@patch.dict(PROCESSORS, clear=True)
@patch.dict(DEPENDENCY_FACTORIES, clear=True)
def test_simple_filtering():
    @processor({"top.mid.low": "val"})
    def my_processor(event):
        return event["top"]["mid"]["low"]

    result = invoke({"top": {"mid": {"low": "val", "other": 1234}}})

    assert result == "val"


@patch.dict(PROCESSORS, clear=True)
@patch.dict(DEPENDENCY_FACTORIES, clear=True)
@pytest.mark.parametrize("test_event, ret", [({"key": "val"}, "val"), ({"key": 123}, 123), ({"key": None}, None)])
def test_any_filter(test_event, ret):
    @processor({"key": Any})
    def my_processor(event):
        return event["key"]

    result = invoke(test_event)

    assert result == ret


@patch.dict(PROCESSORS, clear=True)
@patch.dict(DEPENDENCY_FACTORIES, clear=True)
def test_simple_pre_processing():
    def pre_processor(event):
        return event["user"]

    @processor({"user": Any}, pre_processor=pre_processor)
    def my_processor(user_dict):
        return user_dict

    result = invoke({"user": {"name": "John"}})

    assert result == {"name": "John"}


@patch.dict(PROCESSORS, clear=True)
@patch.dict(DEPENDENCY_FACTORIES, clear=True)
def test_processor_with_dependencies():
    @dependency_factory
    def dep_factory(dep_name):
        return dep_name

    @processor({}, dep_factory=("dep",))
    def my_processor(_event, dep):
        return dep

    result = invoke({})

    assert result == "dep"


@patch.dict(PROCESSORS, clear=True)
@patch.dict(DEPENDENCY_FACTORIES, clear=True)
def test_pre_processor_with_dependencies():
    @dependency_factory
    def dep_factory(dep_name):
        return dep_name

    def pre_processor(_event, dep):
        return dep

    @processor({}, pre_processor=pre_processor, dep_factory=("dep",))
    def my_processor(dep_from_pre_processor):
        return dep_from_pre_processor

    result = invoke({})

    assert result == "dep"
