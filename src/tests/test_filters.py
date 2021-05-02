import pytest

from src.event_processor.filters import Exists, Accept, Eq, And, Or


def test_filter_and_creates_and_filter():
    a_filter = Exists("a")
    b_filter = Exists("b")
    c_filter = Exists("c")

    combined = a_filter & b_filter & c_filter

    assert isinstance(combined, And)
    assert combined.filters[0].filters[0] is a_filter
    assert combined.filters[0].filters[1] is b_filter
    assert combined.filters[1] is c_filter


def test_filter_or_creates_or_filter():
    a_filter = Exists("a")
    b_filter = Exists("b")
    c_filter = Exists("c")

    combined = a_filter | b_filter | c_filter

    assert isinstance(combined, Or)
    assert combined.filters[0].filters[0] is a_filter
    assert combined.filters[0].filters[1] is b_filter
    assert combined.filters[1] is c_filter


def test_filter_operators_when_combined_respect_priority_of_operations_and_commutativity():
    a_filter = Exists("a")
    b_filter = Exists("b")
    c_filter = Exists("c")

    combined_1 = a_filter & (b_filter | c_filter)
    combined_1_commutativity = (b_filter | c_filter) & a_filter
    combined_2 = a_filter | (b_filter & c_filter)
    combined_2_commutativity = (b_filter & c_filter) | a_filter

    assert combined_1.matches({"a": 0, "c": 0})
    assert combined_1_commutativity.matches({"a": 0, "c": 0})
    assert combined_2.matches({"a": 0})
    assert combined_2_commutativity.matches({"a": 0})


@pytest.mark.parametrize("event", [{}, {"key": "value"}, {"top": {"middle": {"lower": ""}}}, None])
def test_accept_filter_matches_any_event(event):
    result = Accept().matches(event)

    assert result is True


def test_exists_filter_matches_event_with_existing_top_level_value():
    test_filter = Exists("top-level")

    result = test_filter.matches({"top-level": "value"})

    assert result is True


def test_exists_filter_matches_event_with_existing_nested_value():
    test_filter = Exists("top.mid.low")

    result = test_filter.matches({"top": {"mid": {"low": "val"}}})

    assert result is True


def test_exists_filter_does_not_match_empty_event():
    test_filter = Exists("key")

    result = test_filter.matches({})

    assert result is False


def test_eq_filter_matches_equal_top_level_value():
    test_filter = Eq("top-level", "expected-value")

    result = test_filter.matches({"top-level": "expected-value"})

    assert result is True


def test_eq_filter_matches_equal_nested_value():
    test_filter = Eq("top.mid.low", "expected-value")

    result = test_filter.matches({"top": {"mid": {"low": "expected-value"}}})

    assert result is True


def test_eq_filter_does_not_match_not_equal_values():
    test_filter = Eq("top", "value")

    result = test_filter.matches({"top": "not-value"})

    assert result is False


def test_eq_filter_does_not_match_nonexistent_key():
    test_filter = Eq("key", "value")

    result = test_filter.matches({})

    assert result is False


def test_and_filter_matches_when_all_filters_match():
    test_filter = And(Exists("a"), Exists("b"), Eq("c", "d"))

    result = test_filter.matches({"a": 0, "b": 0, "c": "d"})

    assert result is True


def test_and_filter_matches_when_all_nested_filters_match():
    test_filter = And(And(Exists("a"), Exists("b")), Eq("c", "d"))

    result = test_filter.matches({"a": 0, "b": 0, "c": "d"})

    assert result is True


def test_and_filter_does_not_match_when_one_filter_does_not_match():
    test_filter = And(Exists("a"), Exists("b"))

    result = test_filter.matches({"a": 0})

    assert result is False


def test_or_filter_matches_when_one_filter_matches():
    test_filter = Or(Exists("a"), Eq("", "y"), Exists("0"))

    result = test_filter.matches({"": "y"})

    assert result is True


def test_or_filter_matches_when_one_nested_filter_matches():
    test_filter = Or(Or(Exists("a"), Eq("", "y")), Exists("0"))

    result = test_filter.matches({"": "y"})

    assert result is True


def test_or_filter_does_not_match_when_no_filters_match():
    test_filter = Or(Exists("a"), Eq("x", "y"))

    result = test_filter.matches({"x": "not-y"})

    assert result is False
