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

- Call first
- Call all
- Call none (raise)

Caveats
-------

- Same filter can only be used by one processor
- Will try to get the most specific processor for an event
- Best effort, but try to be careful

