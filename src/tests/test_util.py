from unittest.mock import Mock

import pytest

from src.event_processor.util import get_value_at_path


def test_get_value_at_path_gets_the_value_when_it_exists():
    path = "a.b.c"
    mock_value = Mock()

    result = get_value_at_path({"a": {"b": {"c": mock_value}}}, path)

    assert result is mock_value


def test_get_value_at_path_raises_for_an_invalid_path():
    path = "a.b.c"

    with pytest.raises(KeyError):
        get_value_at_path({"a": {"b": {"not-c": None}}}, path)
