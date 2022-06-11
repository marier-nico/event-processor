.. _processors-detail:

Processors
==========

Processors are the least involved part of the library. All you have to do is register your processors into an event
processor so that events can be dispatched to it. For a basic example, see the :ref:`Core Concepts`.

Parameters
----------

You can't specify just any random parameters for your processors, event-processor needs to know what to do with them
when invoking your processor. The parameters that your processor can accept are documented in the :ref:`Dependencies`
section!

Invocation
----------

When you invoke your event processor, event-processor takes care of running the correct function (or functions,
depending on your invocation strategy). After running your function, it packs some information with the returned value
into a :ref:`Results` object and returns that to the calling code.

With the result, you can get the value returned by your function as well as the name of the processor that was invoked
(the name of your function).

The actual return value for the invocation depends on your invocation strategy. Whether you get a single value or a list
returned from the invocation should be very obvious from the invocation strategy you're using. Essentially, if the
strategy can call multiple processors, you get a list. If not, you get a single value.

Error Handling
--------------

Handling errors with a lot of processors can get pretty repetitive, especially if you want to ignore several errors.
This might happen when you want to run all matching processors, and you don't want an error in one processor to
interrupt the whole processing.

This is why you can use error handling strategies. Here's an example :

.. testcode::

    from event_processor import EventProcessor, ErrorHandlingStrategies
    from event_processor.filters import Accept

    processor = EventProcessor(error_handling_strategy=ErrorHandlingStrategies.CAPTURE)


    @processor(Accept())
    def my_failing_processor():
        raise RuntimeError("Oh no, I failed!")


    result = processor.invoke({})

    if result.has_exception:
        print(str(result.raised_exception))

.. testoutput::

    Oh no, I failed!

.. note::
    Notice that no exception was raised by ``invoke``, and instead a ``Result`` was returned that contained the raised
    exception.


Here is a list of error handling strategies and what they do :

Bubble (default)
________________

This strategy will bubble up exceptions to the caller of ``invoke``, this is just like if you called the processor
yourself without the library, this way you can handle errors however you like.

SpecificBubble
______________

This strategy will only bubble up *some* errors to the caller, so you can capture any exception *except* a few specific
ones. This could be used if only critical errors should be bubbled up.

Capture
_______

This strategy will capture errors that occur in processors and include them in the ``Result`` that is returned. This is
especially useful when using the :ref:`All Matches` invocation strategy, because it will ensure all processors are run
even if some of them raise exceptions.

SpecificCapture
_______________

This strategy will only capture *some* errors and let other bubble up to the caller, so it's possible to ignore only a
few specific errors instead of all of them.


Multiple Event Processors
-------------------------

Note that when you register a processor, it will be invoked only by the event processor for which it is registered.
For example,

.. testcode::

    from event_processor import EventProcessor, InvocationError
    from event_processor.filters import Accept

    processor = EventProcessor()
    other_processor = EventProcessor()


    @processor(Accept())
    def my_processor():
        pass


    processor.invoke({})  # This is fine, a processor exists for the event

    try:
        other_processor.invoke({})  # This will raise
    except InvocationError:
        print("Raised!")


.. testoutput::

    Raised!


Sub-Processors
--------------

In a big application, you might not want to have all your processors in the same module, so it's possible to setup
sub-processors which get merged with a main processor.

.. note::
    You can also add multiple sub-processors in a single function call with the ``add_subprocessors()`` method. This
    is really only for convenience and aesthetics, there's no functional difference with calling ``add_subprocessor()``
    multiple times.

``my_module.py``

.. testcode::

    from event_processor import EventProcessor
    from event_processor.filters import Accept

    sub_processor = EventProcessor()


    @sub_processor(Accept())
    def my_processor():
        pass


``main.py``

.. testsetup:: processors

    from event_processor import EventProcessor
    from event_processor.filters import Accept

    sub_processor = EventProcessor()


    @sub_processor(Accept())
    def my_processor():
        return "sub_processing!"

.. testcode:: processors

    from event_processor import EventProcessor
    from event_processor.filters import Accept

    # from my_module import sub_processor

    main_processor = EventProcessor()
    main_processor.add_subprocessor(sub_processor)

    # Note that we are invoking on the main processor,
    # but the event will be dispatched to the sub-processor.
    result = main_processor.invoke({})

    print(result.returned_value)

.. testoutput:: processors

    sub_processing!

Package Sub-Processors
----------------------

When your application grows even further, you might end up with a larger collection of event processors spread across
several modules. In this case, it becomes tedious to import each event processor from each of the modules manually. To
make it easy to appropriately separate your processors, it's possible to automatically add all the processors found in
all the modules contained within a given package.

With the following directory structure, this is how it would work :

.. code-block:: bash

    project-root
    └── src
        └── processors
            ├── my_module_1.py
            ├── my_module_2.py
            └── file4
                └── my_module_3.py

.. code-block:: python

    from event_processor import EventProcessor

    from src import processors

    event_processor = EventProcessor()
    event_processor.add_subprocessors_in_package(processors)

.. note::
    It's important not to just use a package name here, you need to use the actual package that you've imported. Also,
    this will cause all the modules in the package to be imported, so be mindful of circular imports when using this
    feature!


Ranking Processors
------------------

.. note::
    It's not always necessary to use ranking. Take a look at the warning on the :ref:`Filters<filters-detail>` page to
    learn more and see if it's something you need to be concerned about.

Since it's not possible for the library to guess what should happen to a particular event matching multiple filters,
figuring that out is left up to the user. In most cases, it's as simple as not worrying about it, but sometimes, dealing
with ambiguous filters is just unavoidable.

This is when you should use processor ranking. A processor's rank is basically an indicator of how much priority it has
with regards to other processors. It's what helps the library call the right processor for an event that might match
multiple processors.

Here's an example of how you can use ranking :

.. note::
    The default rank for processors is ``0``. The matching processor with the highest rank will be called. **To learn
    how to specify what to do when multiple processors match with the same rank, see** :ref:`Invocation Strategy`.

    Another useful thing to think about is that you can use the ``-1`` rank to make a processor be called last when
    there are multiple matches. This is especially useful when coupled with the :ref:`Accept` filter.

.. testcode:: processors

    from event_processor import EventProcessor
    from event_processor.filters import Exists, Eq

    processor = EventProcessor()


    @processor(Exists("a"))
    def processor_a():
        print("Processor a!")


    @processor(Eq("a", "b"), rank=1)
    def processor_b():
        print("Processor b!")


    processor.invoke({"a": "b"})
    processor.invoke({"a": "not b"})

.. testoutput:: processors

    Processor b!
    Processor a!


Invocation Strategy
-------------------

To choose how to invoke your processor(s) in the case that multiple processors with the same rank all match a given
event, you have to choose an invocation strategy.

.. note::
    The default invocation strategy is the :ref:`First Match` strategy.

First Match
___________

This strategy calls the first matching processor (among those with the highest rank). It returns a simple
:ref:`Result<Results>`.

All Matches
___________

This strategy calls all the matching processors (that have the highest rank). It returns a list of
:ref:`Result<Results>`, one for each matching processor (even if only a single match occurred).

No Matches
__________

This strategy calls none of the matching processors if there are more than one (and returns a :ref:`Result<Results>`
with a ``None`` value). Otherwise, it calls the single matching processor and returns a :ref:`Result<Results>` with that
result.

No Matches Strict
_________________

This strategy calls none of the matching processors if there are more than one, and it raises an exception. Otherwise,
it calls the single matching processors and returns a :ref:`Result<Results>` with the returned value.

Example
_______

To use a non-default invocation strategy, use the provided ``InvocationStrategies`` enum like so :

.. testcode::

    from event_processor import EventProcessor, InvocationStrategies
    from event_processor.filters import Exists, Eq

    processor = EventProcessor(invocation_strategy=InvocationStrategies.ALL_MATCHES)


    @processor(Exists("a"))
    def processor_a():
        print("Processor a!")


    @processor(Eq("a", "b"))
    def processor_b():
        print("Processor b!")


    processor.invoke({"a": "b"})

.. testoutput::

    Processor a!
    Processor b!
