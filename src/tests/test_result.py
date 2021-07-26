from src.event_processor.result import Result


def test_result_accepts_expected_parameters():
    result = Result(processor_name="some-processor", returned_value=42, raised_exception=RuntimeError("some-error"))

    assert result.processor_name == "some-processor"
    assert result.returned_value == 42
    assert isinstance(result.raised_exception, RuntimeError)


def test_has_exception_returns_true_and_has_value_returns_false_when_there_is_an_exception():
    result = Result(processor_name="some-processor", raised_exception=RuntimeError("some-error"))

    assert result.has_value() is False
    assert result.has_exception() is True


def test_has_exception_returns_false_and_has_value_returns_true_when_there_is_no_exception():
    result = Result(processor_name="some-processor", returned_value="some-value")

    assert result.has_value() is True
    assert result.has_exception() is False
