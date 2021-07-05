from src.event_processor.result import Result


def test_result_accepts_expected_parameters():
    result = Result(processor_name="some-processor", returned_value=42)

    assert result.processor_name == "some-processor"
    assert result.returned_value == 42
