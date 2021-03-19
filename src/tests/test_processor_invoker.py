from typing import Any
from unittest.mock import patch, MagicMock

import pytest

from src.event_processor.state import Processor
from src.event_processor.exceptions import EventProcessorInvocationException, EventProcessorDependencyException
from src.event_processor.processor_decorator import processor, dependency_factory
from src.event_processor.processor_invoker import (
    event_matches_filters,
    find_processor_for_event,
    get_dependencies_for_processor,
    invoke,
)

MOD_PATH = "src.event_processor.processor_invoker"


def test_event_matches_filters_with_top_level_filter_matches_correctly():
    event = {"key": "value", "other_key": "other_value"}
    filters = (("key", "value"), ("other_key", "other_value"))

    result = event_matches_filters(event, filters)

    assert result is True


def test_event_matches_filters_with_any_value_matches_correctly():
    event = {"key": 123}
    filters = (("key", Any),)

    result = event_matches_filters(event, filters)

    assert result is True


def test_event_matches_filters_with_nested_events_matches_correctly():
    event = {"key": {"sub": 123, "othersub": "asdf"}, "other": {"sub": {"other": 321}}}
    filters = (("key.sub", 123), ("key.othersub", "asdf"), ("other.sub.other", 321))

    result = event_matches_filters(event, filters)

    assert result is True


def test_event_matches_filters_with_different_value_does_not_match():
    event = {"key": "value"}
    filters = (("key", "valuen't"),)

    result = event_matches_filters(event, filters)

    assert result is False


def test_event_matches_filters_with_nonexistent_key_does_not_match():
    event = {"key": "value"}
    filters = (("keyn't", "value"),)

    result = event_matches_filters(event, filters)

    assert result is False


def test_event_matches_filters_with_nonexistent_key_and_longer_path_does_not_match():
    event = {"key": "value"}
    filters = (("keyn't.sub", "value"),)

    result = event_matches_filters(event, filters)

    assert result is False


def test_event_matches_filters_with_empty_filters_always_matches():
    event = {"key": "value"}
    filters = tuple()

    result = event_matches_filters(event, filters)

    assert result is True


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
def test_find_handler_for_event_finds_handler():
    event = {"key": "value"}

    @processor({"key": "value"})
    def a_test(_event):
        pass

    result = find_processor_for_event(event)

    assert result.fn is a_test


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
def test_find_handler_for_event_with_multiple_registered_handlers_finds_handler():
    event = {"key": "value"}

    @processor({"key": "value"})
    def a_test(_event):
        pass

    @processor({"key": "valuen't"})
    def b_test(_event):
        pass

    result = find_processor_for_event(event)

    assert result.fn is a_test


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
def test_find_handler_for_event_with_multiple_registered_handlers_chooses_most_specific_matching_handler():
    event = {"key": "value", "other_key": "other_value"}

    @processor({"key": "value"})
    def a_test(_event):
        pass

    @processor({"key": "value", "other_key": "other_value"})
    def b_test(_event):
        pass

    result = find_processor_for_event(event)

    assert result.fn is b_test


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
def test_find_handler_for_event_raises_when_no_processor_is_found():
    event = {"key": "value"}

    with pytest.raises(EventProcessorInvocationException):
        find_processor_for_event(event)


@patch.dict(f"{MOD_PATH}.DEPENDENCY_FACTORIES")
def test_get_dependencies_for_processor_return_empty_tuple_for_no_dependencies():
    p = Processor(fn=lambda: None, pre_processor=lambda: None, dependencies={})

    dependencies = get_dependencies_for_processor(p)

    assert dependencies is ()


@patch.dict(f"{MOD_PATH}.DEPENDENCY_FACTORIES")
def test_get_dependencies_for_processor_raises_for_nonexistent_factory():
    p = Processor(fn=lambda: None, pre_processor=lambda: None, dependencies={"some_factory": ("a",)})

    with pytest.raises(EventProcessorDependencyException):
        get_dependencies_for_processor(p)


def test_get_dependencies_for_processor_creates_dependencies():
    p = Processor(
        fn=lambda: None, pre_processor=lambda: None, dependencies={"factory_a": ("a", "b"), "factory_b": ("c",)}
    )

    @dependency_factory
    def factory_a(name: str):
        return name

    @dependency_factory
    def factory_b(name: str):
        return name

    dependencies = get_dependencies_for_processor(p)

    assert dependencies == ("a", "b", "c")


@patch(f"{MOD_PATH}.get_dependencies_for_processor")
@patch(f"{MOD_PATH}.find_processor_for_event")
def test_invoke_gets_processor_and_dependencies_and_calls_processor(find_processor_mock, get_dependencies_mock):
    event = {"key": "value"}
    processor_mock = MagicMock()
    find_processor_mock.return_value = processor_mock

    invoke(event)

    processor_mock.pre_processor.assert_called_once_with(event)
    processor_mock.fn.asert_called_once_with(
        processor_mock.pre_processor.return_value, *get_dependencies_mock.return_value
    )
