from unittest.mock import MagicMock, patch

import pytest

from src.event_processor.processor_decorator import processor
from src.event_processor.exceptions import EventProcessorException
from src.event_processor.processor_decorator import dependency_factory
from src.event_processor.state import PROCESSORS, DEPENDENCY_FACTORIES

MOD_PATH = "src.event_processor.processor_decorator"


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
@patch(f"{MOD_PATH}.Processor")
def test_processor_registers_a_processor(processor_mock):
    pre_processor_mock = MagicMock()
    dependency_mock = MagicMock()

    @processor({"key": "value"}, pre_processor=pre_processor_mock, dependency=dependency_mock)
    def a_test():
        pass

    assert len(PROCESSORS) == 1
    processor_mock.assert_called_once_with(
        fn=a_test, pre_processor=pre_processor_mock, dependencies={"dependency": dependency_mock}
    )


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
def test_processor_raises_for_already_registered_filter_expression():
    @processor({"key": "value"})
    def a_test():
        pass

    with pytest.raises(EventProcessorException):

        @processor({"key": "value"})
        def b_test():
            pass


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
def test_processor_registers_a_processor_with_multiple_filters():
    @processor({"key": "value", "key2": "value2"})
    def a_test():
        pass

    assert len(PROCESSORS) == 1


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
def test_processor_does_not_raise_for_different_filters_that_overlap():
    @processor({"key": "value", "key2": "value2"})
    def a_test():
        pass

    @processor({"key": "value", "key3": "value3"})
    def b_test():
        pass

    assert len(PROCESSORS) == 2


@patch.dict(f"{MOD_PATH}.PROCESSORS", clear=True)
def test_processor_raises_for_identical_filters_in_a_different_order():
    @processor({"key": "value", "key2": "value2"})
    def a_test():
        pass

    with pytest.raises(EventProcessorException):

        @processor({"key2": "value2", "key": "value"})
        def b_test():
            pass


@patch.dict(f"{MOD_PATH}.DEPENDENCY_FACTORIES", clear=True)
def test_dependency_factory_registeres_functions_under_the_right_name():
    @dependency_factory
    def a_test(_name):
        pass

    assert DEPENDENCY_FACTORIES["a_test"] is a_test


@patch.dict(f"{MOD_PATH}.DEPENDENCY_FACTORIES", clear=True)
def test_dependency_factory_raises_for_existing_factory():
    @dependency_factory
    def a_test(_name):
        pass

    with pytest.raises(EventProcessorException):

        @dependency_factory
        def a_test(_name):
            pass


@patch.dict(f"{MOD_PATH}.DEPENDENCY_FACTORIES", clear=True)
def test_dependency_factory_raises_with_wrong_number_of_args():
    with pytest.raises(EventProcessorException):

        @dependency_factory
        def a_test():
            pass

    with pytest.raises(EventProcessorException):

        @dependency_factory
        def a_test(_a, _b):
            pass
