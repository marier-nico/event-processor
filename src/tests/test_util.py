import typing
from unittest.mock import Mock, MagicMock

import pytest

from src.event_processor.util import get_value_at_path, py37_get_args, py37_get_origin, load_all_modules_in_package


def test_get_value_at_path_gets_the_value_when_it_exists():
    path = "a.b.c"
    mock_value = Mock()

    result = get_value_at_path({"a": {"b": {"c": mock_value}}}, path)

    assert result is mock_value


def test_get_value_at_path_raises_for_an_invalid_path():
    path = "a.b.c"

    with pytest.raises(KeyError):
        get_value_at_path({"a": {"b": {"not-c": None}}}, path)


def test_py37_get_args_returns_generic_for_generic_type():
    assert py37_get_args(typing.Generic) is typing.Generic


def test_py37_get_args_returns_type_args_when_type_is_not_generic():
    mock_type = MagicMock(__args__="some-args")

    result = py37_get_args(mock_type)

    assert result == "some-args"


def test_py37_get_origin_returns_origin_for_type():
    mock_type = MagicMock(__origin__="some-origin")

    result = py37_get_origin(mock_type)

    assert result == "some-origin"


def test_load_all_modules_in_package():
    from . import package_for_tests

    result = load_all_modules_in_package(package_for_tests)

    names = [mod.__name__.split(".")[-1] for mod in result]
    assert len(result) == 3
    assert "__init__" in names
    assert "a_module" in names
    assert "b_module" in names
