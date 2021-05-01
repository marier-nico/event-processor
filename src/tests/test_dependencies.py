from unittest.mock import Mock

from event_processor.dependencies import Depends, resolve, get_required_dependencies, call_with_injection


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


def test_call_with_injection_calls_callable():
    callable_mock = Mock()

    call_with_injection(callable_mock)

    callable_mock.assert_called_once()


def test_call_with_injection_passes_parameters():
    callable_mock = Mock()

    call_with_injection(callable_mock, None, 1, 2, x=3)

    callable_mock.assert_called_once_with(1, 2, x=3)


def test_call_with_injection_injects_dependencies():
    dependency = Mock()

    def fn(a: Mock = Depends(dependency)):
        a.method()

    call_with_injection(fn)

    dependency.return_value.method.assert_called_once()


def test_call_with_injection_returns_callable_value():
    callable_mock = Mock()

    result = call_with_injection(callable_mock)

    assert result is callable_mock.return_value


def test_resolve_calls_callable():
    mock_callable = Mock()
    dependency = Depends(mock_callable)

    resolve(dependency)

    mock_callable.assert_called_once()


def test_resolve_returns_callable_result():
    mock_callable = Mock()
    dependency = Depends(mock_callable)

    result, _ = resolve(dependency)

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


def test_resolve_injects_required_dependencies_for_nested_dependencies():
    mock_callable = Mock()
    dependency = Depends(mock_callable, cache=False)

    def fn(a: Mock = dependency):
        return a

    nested_dependency = Depends(fn)
    result, _ = resolve(nested_dependency)

    assert result is mock_callable.return_value


def test_resolve_only_caches_values_that_require_other_cached_values():
    mock_callable = Mock()
    cached_dependency = Depends(mock_callable, cache=True)

    def fn(_=cached_dependency):
        pass

    no_cache_dependency = Depends(fn, cache=False)

    def no_cache_fn(_=no_cache_dependency):
        pass

    top_level_caching = Depends(no_cache_fn, cache=True)

    cache = {}
    resolve(top_level_caching, cache)

    assert cached_dependency in cache
    assert no_cache_dependency not in cache
    assert top_level_caching not in cache  # Because it depends on a value that shouldn't be cached


def test_get_required_dependencies_returns_empty_list_for_no_dependencies():
    def fn():
        pass

    dependencies = get_required_dependencies(fn)

    assert dependencies == {}


def test_get_required_dependencies_returns_all_specified_dependencies():
    dependency = Depends(lambda: 0)
    other_dependency = Depends(lambda: 1)

    def fn(_a=dependency, _b=other_dependency):
        pass

    dependencies = get_required_dependencies(fn)

    assert dependencies == {"_a": dependency, "_b": other_dependency}
