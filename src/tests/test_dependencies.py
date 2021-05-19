import inspect
from typing import List, Optional
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel, ValidationError
from pydantic.color import Color

from src.event_processor.dependencies import (
    Depends,
    resolve,
    get_required_dependencies,
    call_with_injection,
    Event,
    get_event_dependencies,
    get_pydantic_dependencies,
    get_scalar_value_dependencies,
    resolve_scalar_value_dependencies_without_pydantic,
    resolve_scalar_value_dependencies_with_pydantic,
    resolve_scalar_value_dependencies,
)
from src.event_processor.exceptions import DependencyError


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


def test_call_with_injection_injects_dependencies():
    dependency = Mock()

    def fn(a: Mock = Depends(dependency)):
        a.method()

    call_with_injection(fn)

    dependency.return_value.method.assert_called_once()


def test_call_with_injection_injects_event_when_required():
    def fn(a: Event):
        return a

    event = Event({"a": "b"})

    result = call_with_injection(fn, event)

    assert result is event


def test_call_with_injection_returns_callable_value():
    callable_mock = Mock()

    result = call_with_injection(callable_mock)

    assert result is callable_mock.return_value


def test_resolve_calls_callable():
    mock_callable = Mock()
    dependency = Depends(mock_callable)

    resolve(dependency)

    mock_callable.assert_called_once()


def test_resolve_forwards_event_when_event_type_is_present_in_params():
    def fn(ev: Event):
        return ev

    dependency = Depends(fn)
    event = Event({"a": 0})

    resolved, _ = resolve(dependency, event)

    assert resolved is event


def test_resolve_injects_into_class_dependency():
    mock_service = Mock()
    event = Event({"a": 0})

    def dependency():
        return mock_service

    class Thing:
        def __init__(self, ev: Event, dep: Mock = Depends(dependency)):
            self.dep = dep
            self.ev = ev

    resolved, _ = resolve(Depends(Thing), event=event)

    assert resolved.ev == event
    assert resolved.dep is mock_service


def test_resolve_injects_pydantic_model_when_present_in_params():
    class Thing(BaseModel):
        id_: int
        items: List[str]

    def fn(thing: Thing):
        return thing

    resolved, _ = resolve(Depends(fn), event=Event({"id_": 1234, "items": ["a", "b"]}))

    assert resolved == Thing(id_=1234, items=["a", "b"])


def test_resolve_injects_scalar_dependencies_when_present_in_params():
    def fn(x: str):
        return x

    dependency = Depends(fn)
    event = Event({"x": "x-value"})

    resolved, _ = resolve(dependency, event)

    assert resolved == "x-value"


def test_resolve_does_not_resolve_scalar_values_for_previously_resolved_dependencies():
    mock_callable = Mock()

    class Thing(BaseModel):
        id_: int

    def fn(x: str, y: Event, z: Thing, w=Depends(mock_callable)):
        return x, y, z, w

    dependency = Depends(fn)
    event = Event({"id_": 0, "x": "x-value"})

    resolved, _ = resolve(dependency, event)

    assert resolved == ("x-value", event, Thing(id_=0), mock_callable.return_value)


def test_resolve_does_not_fail_when_the_event_contains_more_info_than_is_required():
    class Thing(BaseModel):
        id_: int
        items: List[str]

    def fn(thing: Thing):
        return thing

    resolved, _ = resolve(Depends(fn), event=Event({"id_": 1234, "items": ["a", "b"], "other": "stuff"}))

    assert resolved == Thing(id_=1234, items=["a", "b"])


def test_resolve_uses_cache_when_dependency_is_cached():
    dependency_mock = Mock()
    cache = {}

    dependency = Depends(dependency_mock)

    _resolved, _ = resolve(dependency, cache=cache)
    _resolved, _ = resolve(dependency, cache=cache)

    dependency_mock.assert_called_once()


def test_resolve_returns_callable_result():
    mock_callable = Mock()
    dependency = Depends(mock_callable)

    result, _ = resolve(dependency)

    assert result is mock_callable.return_value


def test_resolve_uses_cache_for_same_dependencies():
    mock_callable = Mock()
    dependency = Depends(mock_callable)
    cache = {}

    resolve(dependency, cache=cache)
    resolve(dependency, cache=cache)

    mock_callable.assert_called_once()


def test_resolve_does_not_use_cache_with_caching_disabled():
    mock_callable = Mock()
    dependency = Depends(mock_callable, cache=False)
    cache = {}

    resolve(dependency, cache=cache)
    resolve(dependency, cache=cache)

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
    resolve(top_level_caching, cache=cache)

    assert cached_dependency in cache
    assert no_cache_dependency not in cache
    assert top_level_caching not in cache  # Because it depends on a value that shouldn't be cached


def test_get_required_dependencies_returns_empty_list_for_no_dependencies():
    def fn():
        pass

    dependencies = get_required_dependencies(fn)

    assert dependencies == {}


def test_get_required_dependencies_returns_empty_list_for_non_dependency_param():
    def fn(_: Optional[str] = Optional[str]):
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


def test_get_event_dependencies_returns_dependant_param_names():
    def fn(_a: Event, _b: Event):
        pass

    param = get_event_dependencies(fn)

    assert param == ["_a", "_b"]


def test_get_event_dependencies_returns_empty_list_for_no_event_dependencies():
    callable_mock = Mock()

    param = get_event_dependencies(callable_mock)

    assert param == []


def test_get_event_dependencies_returns_empty_list_for_non_event_dependencies():
    def fn(_: Optional[str]):
        pass

    param = get_event_dependencies(fn)

    assert param == []


def test_get_pydantic_dependencies_returns_dependencies_when_they_are_specified():
    class Thing(BaseModel):
        pass

    def fn(_a: Thing):
        pass

    dependencies = get_pydantic_dependencies(fn)

    assert dependencies == {"_a": Thing}


def test_get_pydantic_dependencies_returns_no_dependencies_when_none_are_specified():
    def fn():
        pass

    dependencies = get_pydantic_dependencies(fn)

    assert dependencies == {}


def test_get_pydantic_dependencies_returns_no_dependencies_for_non_pydantic_dependencies():
    def fn(_: Optional[str]):
        pass

    dependencies = get_pydantic_dependencies(fn)

    assert dependencies == {}


@patch("src.event_processor.dependencies._has_pydantic", False)
def test_get_pydantic_dependencies_returns_none_even_when_present_if_pydantic_is_not_installed():
    def fn(_a: BaseModel):
        pass

    dependencies = get_pydantic_dependencies(fn)

    assert dependencies == {}


@patch("src.event_processor.dependencies._has_pydantic", False)
@patch("src.event_processor.dependencies.resolve_scalar_value_dependencies_without_pydantic")
def test_resolve_scalar_value_dependencies_resolves_without_pydantic_when_pydantic_is_not_installed(resolve_mock):
    params = [inspect.Parameter("x", kind=inspect.Parameter.POSITIONAL_ONLY)]

    resolve_scalar_value_dependencies(params, Event({}))

    resolve_mock.assert_called_once_with(params, {})


@patch("src.event_processor.dependencies._has_pydantic", True)
@patch("src.event_processor.dependencies.resolve_scalar_value_dependencies_with_pydantic")
def test_resolve_scalar_value_dependencies_resolves_with_pydantic_when_pydantic_is_installed(resolve_mock):
    params = [inspect.Parameter("x", kind=inspect.Parameter.POSITIONAL_ONLY)]

    resolve_scalar_value_dependencies(params, Event({}))

    resolve_mock.assert_called_once_with(params, {})


def test_get_scalar_value_dependencies_returns_empty_dict_for_no_dependencies():
    def fn():
        pass

    dependencies = get_scalar_value_dependencies(fn)

    assert dependencies == []


def test_get_scalar_value_dependencies_does_not_return_variable_arguments():
    def fn(_x, *_args, **_kwargs):
        pass

    dependencies = get_scalar_value_dependencies(fn)

    assert len(dependencies) == 1


def test_get_scalar_value_dependencies_returns_dependencies_when_they_are_specified():
    def fn(_a: str):
        pass

    dependencies = get_scalar_value_dependencies(fn)

    assert dependencies[0].annotation == str


def test_resolve_scalar_value_dependencies_without_pydantic_fetches_values_from_event():
    event = {"x": 0}
    scalar_dependencies = [inspect.Parameter("x", kind=inspect.Parameter.POSITIONAL_ONLY)]

    result = resolve_scalar_value_dependencies_without_pydantic(scalar_dependencies, Event(event))

    assert result == {"x": 0}


def test_resolve_scalar_value_dependencies_without_pydantic_does_not_fail_on_none_value():
    event = {"x": None}
    scalar_dependencies = [inspect.Parameter("x", kind=inspect.Parameter.POSITIONAL_ONLY)]

    result = resolve_scalar_value_dependencies_without_pydantic(scalar_dependencies, Event(event))

    assert result == {"x": None}


def test_resolve_scalar_value_dependencies_without_pydantic_raises_on_missing_arg_value():
    event = {"not-x": 0}
    scalar_dependencies = [inspect.Parameter("x", annotation=int, kind=inspect.Parameter.POSITIONAL_ONLY)]

    with pytest.raises(DependencyError):
        resolve_scalar_value_dependencies_without_pydantic(scalar_dependencies, Event(event))


def test_resolve_scalar_value_dependencies_with_pydantic_fetches_values_from_event():
    event = {"x": 0}
    scalar_dependencies = [inspect.Parameter("x", annotation=int, kind=inspect.Parameter.POSITIONAL_ONLY)]

    result = resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, Event(event))

    assert result == {"x": 0}


def test_resolve_scalar_value_dependencies_with_pydantic_raises_on_missing_arg_value():
    event = {"not-x": 0}
    scalar_dependencies = [inspect.Parameter("x", annotation=int, kind=inspect.Parameter.POSITIONAL_ONLY)]

    with pytest.raises(ValidationError):
        resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, Event(event))


def test_resolve_scalar_value_dependencies_with_pydantic_raises_on_validation_errors():
    event = {"x": "not-an-int"}
    scalar_dependencies = [inspect.Parameter("x", annotation=int, kind=inspect.Parameter.POSITIONAL_ONLY)]

    with pytest.raises(ValidationError):
        resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, Event(event))


def test_resolve_scalar_value_dependencies_with_pydantic_raises_on_validation_errors_for_pydantic_field_types():
    event = {"x": "not-an-int"}
    scalar_dependencies = [inspect.Parameter("x", annotation=Color, kind=inspect.Parameter.POSITIONAL_ONLY)]

    with pytest.raises(ValidationError):
        resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, Event(event))


@pytest.mark.parametrize("event_val", ["some-string", {"a": "dict"}])
def test_resolve_scalar_value_dependencies_with_pydantic_accepts_any_without_annotations(event_val):
    event = {"x": event_val}
    scalar_dependencies = [inspect.Parameter("x", kind=inspect.Parameter.POSITIONAL_ONLY)]

    result = resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, Event(event))

    assert result["x"] == event_val


def test_resolve_scalar_value_dependencies_with_pydantic_makes_values_required_when_no_default_is_provided():
    scalar_dependencies = [inspect.Parameter("x", kind=inspect.Parameter.POSITIONAL_ONLY)]

    with pytest.raises(ValidationError):
        resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, Event({}))


def test_resolve_scalar_value_dependencies_with_pydantic_makes_values_optional_when_a_default_is_provided():
    scalar_dependencies = [inspect.Parameter("x", default="default", kind=inspect.Parameter.POSITIONAL_ONLY)]

    result = resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, Event({}))

    assert result["x"] == "default"


def test_resolve_scalar_value_dependencies_with_pydantic_passes_none_to_unfilled_optionals():
    scalar_dependencies = [inspect.Parameter("x", annotation=Optional[str], kind=inspect.Parameter.POSITIONAL_ONLY)]

    result = resolve_scalar_value_dependencies_with_pydantic(scalar_dependencies, Event({}))

    assert result["x"] is None
