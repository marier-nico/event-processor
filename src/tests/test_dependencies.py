from unittest.mock import Mock

from event_processor.dependencies import Depends, resolve, get_required_dependencies


def test_depends_init_sets_values():
    def fn():
        pass

    result = Depends(fn, False)

    assert result.callable is fn
    assert result.cache is False


def test_depends_eq_compares_correctly():
    def fn():
        pass

    def other_fn():
        pass

    depends_fn = Depends(fn)
    depends_fn_again = Depends(fn)
    depends_fn_without_cache = Depends(fn, cache=False)
    depends_other_fn = Depends(other_fn)

    assert depends_fn == depends_fn_again
    assert depends_fn != depends_other_fn
    assert depends_fn != depends_fn_without_cache
    assert depends_fn != "not a depends"


def test_resolve_calls_callable():
    mock_callable = Mock()
    dependency = Depends(mock_callable)

    resolve(dependency)

    mock_callable.assert_called_once()


def test_resolve_returns_callable_result():
    mock_callable = Mock()
    dependency = Depends(mock_callable)

    result = resolve(dependency)

    assert result is mock_callable.return_value


def test_resolve_uses_cache_for_same_dependencies():
    mock_callable = Mock()
    dependency = Depends(mock_callable)
    cache = {}

    resolve(dependency, cache)
    resolve(dependency, cache)

    mock_callable.assert_called_once()


def test_resolve_does_not_use_cache_with_caching_disabled():
    mock_callable = Mock()
    dependency = Depends(mock_callable, cache=False)
    cache = {}

    resolve(dependency, cache)
    resolve(dependency, cache)

    assert len(mock_callable.mock_calls) == 2


def test_get_required_dependencies_returns_empty_list_for_no_dependencies():
    def fn():
        pass

    dependencies = get_required_dependencies(fn)

    assert dependencies == []


def test_get_required_dependencies_returns_all_specified_dependencies():
    dependency = Depends(lambda: 0)

    def fn(a=dependency):
        pass

    dependencies = get_required_dependencies(fn)

    assert dependencies == [dependency]
