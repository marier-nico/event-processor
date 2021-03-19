from unittest.mock import MagicMock

from src.event_processor.pre_processors import passthrough


def test_passthrough_passes_event_through_unmodified():
    event_mock = MagicMock()

    result = passthrough(event_mock)

    assert result is event_mock
    event_mock.assert_not_called()
