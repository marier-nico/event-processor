.. _processors-detail:

Processors
==========

Processors are the least involved part of the library. All you have to do is register your processors into an event
processor so that events can be dispatched to it.

Multiple Event Processors
-------------------------

Note that when you register a processor, it will be invoked only by the event processor for which it is registered.
For example,

.. testcode::

    from event_processor import EventProcessor, InvocationError
    from event_processor.filters import Accept

    event_processor = EventProcessor()
    other_event_processor = EventProcessor()


    @event_processor.processor(Accept())
    def my_processor():
        pass


    event_processor.invoke({})  # This is fine, a processor exists for the event

    try:
        other_event_processor.invoke({})  # This will raise
    except InvocationError:
        print("Raised!")


.. testoutput::

    Raised!


Sub-Processors
--------------

In a big application, you might not want to have all your processors in the same module, so it's possible to setup
sub-processors which get merged with a main processor.

``my_module.py``

.. testcode::

    from event_processor import EventProcessor
    from event_processor.filters import Accept

    sub_processor = EventProcessor()


    @sub_processor.processor(Accept())
    def my_processor():
        pass


``main.py``

.. testsetup:: processors

    from event_processor import EventProcessor
    from event_processor.filters import Accept

    sub_processor = EventProcessor()


    @sub_processor.processor(Accept())
    def my_processor():
        return "sub_processing!"

.. testcode:: processors

    from event_processor import EventProcessor
    from event_processor.filters import Accept

    # from my_module.py import sub_processor

    main_processor = EventProcessor()
    main_processor.add_subprocessor(sub_processor)

    # Note that we are invoking on the main processor,
    # but the event will be dispatched to the sub-processor.
    result = main_processor.invoke({})

    print(result)

.. testoutput:: processors

    sub_processing!

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

.. testcode:: processors

    from event_processor import EventProcessor
    from event_processor.filters import Exists, Eq

    event_processor = EventProcessor()


    @event_processor.processor(Exists("a"))
    def processor_a():
        print("Processor a!")


    @event_processor.processor(Eq("a", "b"), rank=1)
    def processor_b():
        print("Processor b!")


    event_processor.invoke({"a": "b"})
    event_processor.invoke({"a": "not b"})

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

This strategy calls the first matching processor (among those with the highest rank). It returns the processor's return
value as-is.

All Matches
___________

This strategy calls all the matching processors (that have the highest rank). It returns a tuple of results for all the
processors (even if only a single match occurred).

No Matches
__________

This strategy calls none of the matching processors if there are more than one (and returns none). Otherwise, it calls
the single matching processor and returns its value as-is.

No Matches Strict
_________________

This strategy calls none of the matching processors if there are more than one, and it raises an exception. Otherwise,
it calls the single matching processors and returns its value as-is.

Example
_______

To use a non-default invocation strategy, use the provided ``InvocationStrategies`` enum like so :

.. testcode::

    from event_processor import EventProcessor, InvocationStrategies
    from event_processor.filters import Exists, Eq

    event_processor = EventProcessor(invocation_strategy=InvocationStrategies.ALL_MATCHES)


    @event_processor.processor(Exists("a"))
    def processor_a():
        print("Processor a!")


    @event_processor.processor(Eq("a", "b"))
    def processor_b():
        print("Processor b!")


    event_processor.invoke({"a": "b"})

.. testoutput::

    Processor a!
    Processor b!

Caveats
-------

The main things to keep in mind for processors are :

* The same filter can only be used by one processor.
* It's possible to have ambiguous filters and those should be resolved with ranking.
* Invocation strategies are used when the rank doesn't resolve ambiguous filters.

