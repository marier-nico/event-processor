Public API
==========

While it's possible to access any internal module of this package, it's advisable to only stick to the features
exported at the top level, as this makes up the public API as it was intended to be used.

Decorators
----------

You can use the following decorators:

- :py:func:`event_processor.processor`
- :py:func:`event_processor.dependency_factory`

.. code-block:: python

    from event_processor import processor, dependency_factory

    ...

Functions
---------

You can use the following functions:

- :py:func:`event_processor.invoke`
- :py:func:`event_processor.passthrough`

.. code-block:: python

    from event_processor import invoke, passthrough

    ...

Exceptions
----------

You can use the following exceptions:

- :py:class:`event_processor.EventProcessorException`
- :py:class:`event_processor.EventProcessorDependencyException`
- :py:class:`event_processor.EventProcessorInvocationException`
- :py:class:`event_processor.EventProcessorDecorationException`

.. code-block:: python

    from event_processor import (
        EventProcessorException,
        EventProcessorDependencyException,
        EventProcessorInvocationException,
        EventProcessorDecorationException,
    )

    ...
