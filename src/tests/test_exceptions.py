from src.event_processor.exceptions import (
    EventProcessorException,
    EventProcessorDecorationException,
    EventProcessorInvocationException,
    EventProcessorDependencyException,
)


def test_event_processor_exception():
    exc = EventProcessorException("Some message")

    exc_repr = str(exc)

    assert "Some message" in exc_repr


def test_event_processor_decoration_exception():
    exc = EventProcessorDecorationException("Some message", lambda: None)

    exc_repr = str(exc)

    assert "Some message" in exc_repr
    assert "lambda" in exc_repr


def test_event_processor_invocation_exception():
    exc = EventProcessorInvocationException("Some message", {"key": "value"})

    exc_repr = str(exc)

    assert "Some message" in exc_repr
    assert "key" in exc_repr and "value" in exc_repr


def test_event_processor_dependency_exception():
    exc = EventProcessorDependencyException("Some message", lambda: None, {"factory": ("a",)})

    exc_repr = str(exc)

    assert "Some message" in exc_repr
    assert "lambda" in exc_repr
    assert "factory" in exc.dependencies
