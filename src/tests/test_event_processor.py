from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.event_processor.event_processor import EventProcessor
from src.event_processor.exceptions import (
    EventProcessorException,
    EventProcessorDecorationException,
    EventProcessorInvocationException,
    EventProcessorDependencyException,
    EventProcessorSubprocessorException,
)

MOD_PATH = "src.event_processor.event_processor"


@pytest.fixture
def event_processor():
    return EventProcessor()


@patch(f"{MOD_PATH}.Processor")
def test_processor_registers_a_processor(processor_mock, event_processor):
    pre_processor_mock = MagicMock()
    dependency_mock = MagicMock()

    @event_processor.processor({"key": "value"}, pre_processor=pre_processor_mock, dependency=dependency_mock)
    def a_test():
        pass

    assert len(event_processor.processors) == 1
    processor_mock.assert_called_once_with(
        fn=a_test, pre_processor=pre_processor_mock, dependencies={"dependency": dependency_mock}
    )


def test_processor_raises_for_already_registered_filter_expression(event_processor):
    @event_processor.processor({"key": "value"})
    def a_test():
        pass

    with pytest.raises(EventProcessorDecorationException):

        @event_processor.processor({"key": "value"})
        def b_test():
            pass


def test_processor_registers_a_processor_with_multiple_filters(event_processor):
    @event_processor.processor({"key": "value", "key2": "value2"})
    def a_test():
        pass

    assert len(event_processor.processors) == 1


def test_processor_does_not_raise_for_different_filters_that_overlap(event_processor):
    @event_processor.processor({"key": "value", "key2": "value2"})
    def a_test():
        pass

    @event_processor.processor({"key": "value", "key3": "value3"})
    def b_test():
        pass

    assert len(event_processor.processors) == 2


def test_add_subprocessor_adds_subprocessors_to_main_processor(event_processor):
    subprocessor = EventProcessor()

    @subprocessor.processor({"key": "value"})
    def a_test(_event):
        pass

    event_processor.add_subprocessor(subprocessor)

    assert len(event_processor.processors) == 1


def test_add_subprocessor_adds_dependency_factories_to_main_processor(event_processor):
    subprocessor = EventProcessor()

    @subprocessor.dependency_factory
    def some_factory(_client_name):
        pass

    event_processor.add_subprocessor(subprocessor)

    assert len(event_processor.dependency_factories) == 1


def test_add_subprocessor_raises_for_duplicate_filters(event_processor):
    subprocessor = EventProcessor()

    @event_processor.processor({"key": "value"})
    def a_test(_event):
        pass

    @subprocessor.processor({"key": "value"})
    def b_test(_event):
        pass

    with pytest.raises(EventProcessorSubprocessorException):
        event_processor.add_subprocessor(subprocessor)


def test_add_subprocessor_raises_for_duplicate_filters_with_some_non_overlapping_processors(event_processor):
    subprocessor = EventProcessor()

    @event_processor.processor({"key": "value"})
    def a_test(_event):
        pass

    @event_processor.processor({"key": "value1"})
    def b_test(_event):
        pass

    @subprocessor.processor({"key": "value"})
    def c_test(_event):
        pass

    @subprocessor.processor({"key": "value2"})
    def c_test(_event):
        pass

    with pytest.raises(EventProcessorSubprocessorException):
        event_processor.add_subprocessor(subprocessor)


def test_add_subprocessor_does_not_add_existing_factories_to_main_processor(event_processor):
    subprocessor = EventProcessor()

    @event_processor.dependency_factory
    def some_factory(_dependency_name):
        pass

    @subprocessor.dependency_factory
    def some_factory(_dependency_name):
        pass

    event_processor.add_subprocessor(subprocessor)

    assert len(event_processor.dependency_factories) == 1


def test_processor_raises_for_identical_filters_in_a_different_order(event_processor):
    @event_processor.processor({"key": "value", "key2": "value2"})
    def a_test():
        pass

    with pytest.raises(EventProcessorException):

        @event_processor.processor({"key2": "value2", "key": "value"})
        def b_test():
            pass


def test_dependency_factory_registeres_functions_under_the_right_name(event_processor):
    @event_processor.dependency_factory
    def a_test(_name):
        pass

    assert event_processor.dependency_factories["a_test"] is a_test


def test_dependency_factory_raises_for_existing_factory(event_processor):
    @event_processor.dependency_factory
    def a_test(_name):
        pass

    with pytest.raises(EventProcessorException):

        @event_processor.dependency_factory
        def a_test(_name):
            pass


def test_dependency_factory_raises_with_wrong_number_of_args(event_processor):
    with pytest.raises(EventProcessorException):

        @event_processor.dependency_factory
        def a_test():
            pass

    with pytest.raises(EventProcessorException):

        @event_processor.dependency_factory
        def a_test(_a, _b):
            pass


def test_invoke_calls_a_matching_processor(event_processor):
    called = False

    @event_processor.processor({"key.value": "value"})
    def a_test(_event):
        nonlocal called
        called = True

    event_processor.invoke({"key": {"value": "value"}})

    assert called is True


def test_invoke_calls_a_matching_processor_when_a_non_matching_one_exists(event_processor):
    called_good = False
    called_bad = False

    @event_processor.processor({"key.value": "value"})
    def a_test(_event):
        nonlocal called_good
        called_good = True

    @event_processor.processor({"key.value": "valuen't"})
    def b_test(_event):
        nonlocal called_bad
        called_bad = True

    event_processor.invoke({"key": {"value": "value"}})

    assert called_good is True
    assert called_bad is False


def test_invoke_calls_the_most_specific_matching_processor(event_processor):
    called_good = False
    called_bad = False

    @event_processor.processor({"key.value": "value", "key.other": "specific"})
    def a_test(_event):
        nonlocal called_good
        called_good = True

    @event_processor.processor({"key.value": "value"})
    def b_test(_event):
        nonlocal called_bad
        called_bad = True

    event_processor.invoke({"key": {"value": "value", "other": "specific"}})

    assert called_good is True
    assert called_bad is False


def test_invoke_raises_when_no_processor_is_found_for_an_event(event_processor):
    with pytest.raises(EventProcessorInvocationException):
        event_processor.invoke({"a": "b"})


def test_invoke_does_not_call_a_processor_with_the_wrong_value_at_a_key(event_processor):
    @event_processor.processor({"key": "value"})
    def a_test(_event):
        pass

    with pytest.raises(EventProcessorInvocationException):
        event_processor.invoke({"key": "not_value"})


def test_invoke_does_not_pass_in_dependencies_when_none_are_required(event_processor):
    number_of_args = None

    @event_processor.processor({"key": "value"})
    def a_test(_event, *args):
        nonlocal number_of_args
        number_of_args = len(args)

    event_processor.invoke({"key": "value"})

    assert number_of_args == 0


def test_invoke_raises_for_nonexistent_dependency_factory(event_processor):
    @event_processor.processor({"key": "value"}, some_factory=("asdf",))
    def a_test(_event):
        pass

    with pytest.raises(EventProcessorDependencyException):
        event_processor.invoke({"key": "value"})


def test_invoke_creates_dependencies_with_factory_when_a_factory_is_provided(event_processor):
    created_dependencies = []

    @event_processor.dependency_factory
    def some_factory(dep_name):
        nonlocal created_dependencies
        created_dependencies.append(dep_name)

    @event_processor.processor({"key": "value"}, some_factory=("asdf",))
    def a_test(_event):
        pass

    event_processor.invoke({"key": "value"})

    assert created_dependencies == ["asdf"]


def test_invoke_returns_processor_return_value(event_processor):
    @event_processor.processor({"key": "value"})
    def a_test(_event):
        return 1234

    result = event_processor.invoke({"key": "value"})

    assert result == 1234


def test_invoke_raises_for_processor_with_bad_arg_count(event_processor):
    @event_processor.processor({"key": "value"})
    def a_test():
        pass

    with pytest.raises(EventProcessorDependencyException):
        event_processor.invoke({"key": "value"})


def test_invoke_raises_for_pre_processor_with_bad_arg_count(event_processor):
    @event_processor.processor({"key": "value"}, pre_processor=lambda: None)
    def a_test(_event):
        pass

    with pytest.raises(EventProcessorDependencyException):
        event_processor.invoke({"key": "value"})


def test_invoke_passes_dependencies_to_processor(event_processor):
    dependency_passed_in = False

    @event_processor.dependency_factory
    def some_factory(dep_name):
        return dep_name

    @event_processor.processor({"key": "value"}, some_factory=("asdf",))
    def a_test(_event, some_dependency):
        nonlocal dependency_passed_in
        if some_dependency == "asdf":
            dependency_passed_in = True

    event_processor.invoke({"key": "value"})

    assert dependency_passed_in is True


def test_invoke_passes_dependencies_to_pre_processor(event_processor):
    dependency_passed_in = False

    @event_processor.dependency_factory
    def some_factory(dep_name):
        return dep_name

    def pre_processor(_event, some_dependency):
        nonlocal dependency_passed_in
        if some_dependency == "asdf":
            dependency_passed_in = True

    @event_processor.processor({"key": "value"}, pre_processor=pre_processor, some_factory=("asdf",))
    def a_test(_event):
        pass

    event_processor.invoke({"key": "value"})

    assert dependency_passed_in is True


@pytest.mark.parametrize("value", [123, None, "asdf", MagicMock()])
def test_invoke_calls_processor_with_any_matching_value_type(event_processor, value):
    event = {"key": value}
    called = False

    @event_processor.processor({"key": value})
    def a_test(_event):
        nonlocal called
        called = True

    event_processor.invoke(event)

    assert called is True


def test_invoke_calls_processor_with_deeply_nested_values(event_processor):
    called = False

    @event_processor.processor({"key.deep.deep.value": "value"})
    def a_test(_event):
        nonlocal called
        called = True

    event_processor.invoke({"key": {"deep": {"deep": {"value": "value"}}}})

    assert called is True


def test_invoke_calls_default_processor_when_no_other_processors_match(event_processor):
    called_good = False
    called_bad = False

    @event_processor.processor({"key": "value"})
    def a_test(_event):
        nonlocal called_bad
        called_bad = True

    @event_processor.processor({})
    def b_test(_event):
        nonlocal called_good
        called_good = True

    event_processor.invoke({"not_key": "value"})

    assert called_good is True
    assert called_bad is False


def test_invoke_does_not_call_processor_with_bad_key_and_any_value(event_processor):
    @event_processor.processor({"key": Any})
    def a_test(_event):
        pass

    with pytest.raises(EventProcessorInvocationException):
        event_processor.invoke({"not_key": "value"})


def test_invoke_does_not_call_processor_with_bad_nested_key_and_any_value(event_processor):
    @event_processor.processor({"key.deeper": Any})
    def a_test(_event):
        pass

    with pytest.raises(EventProcessorInvocationException):
        event_processor.invoke({"key.not_deeper": "value"})
