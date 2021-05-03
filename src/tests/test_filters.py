from unittest.mock import Mock

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


def test_accept_filter_is_equal_to_other_accept_filters():
    a_filter = Accept()
    b_filter = Accept()

    assert a_filter == b_filter


def test_accept_filter_is_not_equal_to_other_object():
    a_filter = Accept()
    b_filter = 3

    assert a_filter != b_filter


def test_accept_filter_hash_returns_class_hash():
    filter_ = Accept()

    assert hash(filter_) == hash(filter_.__class__)


def test_accept_filter_get_match_specificity_returns_one():
    assert Accept().get_match_specificity({"a": 0, "b": 1}) == 1


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


def test_exists_filter_is_equal_to_other_exists_filter_with_the_same_path():
    a_filter = Exists("a")
    b_filter = Exists("a")

    assert a_filter == b_filter


def test_exists_filter_is_not_equal_to_other_types():
    a_filter = Exists("a")
    b_filter = 0

    assert a_filter != b_filter


def test_exists_filter_is_not_equal_to_different_path():
    a_filter = Exists("a")
    b_filter = Exists("b")

    assert a_filter != b_filter


def test_exists_filter_hash_is_path_hash():
    filter_ = Exists("a")

    assert hash(filter_) == hash((Exists, "a"))


def test_exists_filter_get_match_specificity_returns_one_when_there_is_a_match():
    filter_ = Exists("a")

    assert filter_.get_match_specificity({"a": 0}) == 1


def test_exists_filter_get_match_specificity_returns_zero_when_there_is_no_match():
    filter_ = Exists("a")

    assert filter_.get_match_specificity({"b": 0}) == 0


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


def test_eq_filter_is_equal_to_other_exists_filter_with_the_same_path_and_same_value():
    a_filter = Eq("a", 0)
    b_filter = Eq("a", 0)

    assert a_filter == b_filter


def test_eq_filter_is_not_equal_to_other_types():
    a_filter = Eq("a", 0)
    b_filter = 0

    assert a_filter != b_filter


def test_eq_filter_is_not_equal_to_different_path():
    a_filter = Eq("a", 0)
    b_filter = Eq("b", 0)

    assert a_filter != b_filter


def test_eq_filter_is_not_equal_to_different_value():
    a_filter = Eq("a", 0)
    b_filter = Eq("a", 1)

    assert a_filter != b_filter


def test_eq_filter_hash_hashes_path_and_value():
    filter_ = Eq("a", 0)

    assert hash(filter_) == hash((Eq, ("a", 0)))


def test_eq_filter_get_match_specificity_returns_one_when_there_is_a_match():
    filter_ = Eq("a", 0)

    assert filter_.get_match_specificity({"a": 0}) == 1


def test_eq_filter_get_match_specificity_returns_zero_when_there_is_no_match():
    filter_ = Eq("a", 0)

    assert filter_.get_match_specificity({"a": 1}) == 0


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


def test_and_filter_is_equal_when_sub_filters_are_equal():
    a_filter = Mock()
    a_filter.__eq__ = lambda _, x: x is a_filter
    b_filter = Mock()
    b_filter.__eq__ = lambda _, x: x is b_filter

    and_filter_1 = And(a_filter, b_filter)
    and_filter_2 = And(b_filter, a_filter)

    assert and_filter_1 == and_filter_2


def test_and_filter_is_not_equal_when_sub_filters_are_different():
    a_filter = Mock()
    a_filter.__eq__ = lambda _, x: x is a_filter
    b_filter = Mock()
    b_filter.__eq__ = lambda _, x: x is b_filter

    and_filter_1 = And(a_filter, b_filter)
    and_filter_2 = And(b_filter)
    and_filter_3 = And(a_filter)

    assert and_filter_1 != and_filter_2
    assert and_filter_2 != and_filter_3


def test_and_filter_is_not_equal_when_other_is_not_a_filter():
    a_filter = And(Mock())

    assert a_filter != 0


def test_and_filter_hash_is_hash_of_all_sub_filters():
    a_filter = Exists("a")
    b_filter = Exists("b")

    and_hash = hash(And(a_filter, b_filter))

    assert and_hash == hash((And, (a_filter, b_filter)))


def test_and_filter_get_filter_specificity_is_two_more_than_the_sum_of_matching_sub_filters():
    a_filter = Exists("a")
    b_filter = Exists("b")
    c_filter = Exists("c")

    and_filter = And(a_filter, b_filter, c_filter)

    assert and_filter.get_match_specificity({"a": 0, "b": 1, "c": 2}) == 3 + 2


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


def test_or_filter_is_equal_when_sub_filters_are_equal():
    a_filter = Mock()
    a_filter.__eq__ = lambda _, x: x is a_filter
    b_filter = Mock()
    b_filter.__eq__ = lambda _, x: x is b_filter

    or_filter_1 = Or(a_filter, b_filter)
    or_filter_2 = Or(b_filter, a_filter)

    assert or_filter_1 == or_filter_2


def test_or_filter_is_not_equal_when_sub_filters_are_different():
    a_filter = Mock()
    a_filter.__eq__ = lambda _, x: x is a_filter
    b_filter = Mock()
    b_filter.__eq__ = lambda _, x: x is b_filter

    or_filter_1 = Or(a_filter, b_filter)
    or_filter_2 = Or(b_filter)
    or_filter_3 = Or(a_filter)

    assert or_filter_1 != or_filter_2
    assert or_filter_2 != or_filter_3


def test_or_filter_is_not_equal_when_other_is_not_a_filter():
    a_filter = Or(Mock())

    assert a_filter != 0


def test_or_filter_hash_is_hash_of_all_sub_filters():
    a_filter = Exists("a")
    b_filter = Exists("b")

    or_hash = hash(Or(a_filter, b_filter))

    assert or_hash == hash((Or, (a_filter, b_filter)))


def test_or_filter_get_filter_specificity_is_one_more_than_the_sum_of_matching_sub_filters():
    a_filter = Exists("a")
    b_filter = Exists("b")
    c_filter = Exists("c")

    or_filter = Or(a_filter, b_filter, c_filter)

    assert or_filter.get_match_specificity({"a": 0, "b": 1, "c": 2}) == 3 + 1


def test_and_filter_is_more_specific_than_or_filter_with_same_sub_filters():
    a_filter = Exists("a")
    b_filter = Exists("b")
    c_filter = Exists("c")
    event = {"a": 0, "b": 1, "c": 2}

    or_filter = Or(a_filter, b_filter, c_filter)
    and_filter = And(a_filter, b_filter, c_filter)

    assert and_filter.get_match_specificity(event) > or_filter.get_match_specificity(event)
