import pytest
from unittest.mock import Mock

from src.event_processor.exceptions import InvocationError
from src.event_processor.invocation_strategies import FirstMatch, AllMatches, NoMatches, NoMatchesStrict


def test_first_match_invokes_first_matching_processor():
    processor_a, processor_b = Mock(), Mock()

    FirstMatch.invoke([processor_a, processor_b])

    processor_a.assert_called_once()
    processor_b.assert_not_called()


def test_all_matches_invokes_all_matching_processors():
    processor_a, processor_b = Mock(), Mock()

    AllMatches.invoke([processor_a, processor_b])

    processor_a.assert_called_once()
    processor_b.assert_called_once()


def test_no_matches_invokes_no_matching_processors_on_multiple_matches():
    processor_a, processor_b = Mock(), Mock()

    NoMatches.invoke([processor_a, processor_b])

    processor_a.assert_not_called()
    processor_b.assert_not_called()


def test_no_matches_invokes_the_matching_processor_on_a_single_match():
    processor_a = Mock()

    NoMatches.invoke([processor_a])

    processor_a.assert_called_once()


def test_no_matches_strict_raises_when_multiple_processors_match():
    processor_a, processor_b = Mock(), Mock()

    with pytest.raises(InvocationError):
        NoMatchesStrict.invoke([processor_a, processor_b])


def test_no_matches_strict_invokes_the_matching_processor_on_a_single_match():
    processor_a = Mock()

    NoMatchesStrict.invoke([processor_a])

    processor_a.assert_called_once()
