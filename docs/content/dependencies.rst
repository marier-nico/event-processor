.. _dependencies-detail:

Dependencies
============

Dependency injection is a useful tool that you can use to keep your code clean and testable, which is why this library
offers simple dependency injection out of the box. The current offering was heavily inspired by the excellent
`FastAPI <https://fastapi.tiangolo.com/tutorial/dependencies/>`_ framework.

Functional Dependencies
-----------------------

This type of dependency is the most flexible and powerful. It essentially allows you to inject a value into your
processor which will be computed from the result of another function of your choice.

.. note::
    These dependencies are cached by default, so if that's something you don't want, be sure to specify ``cache=False``
    in your dependency.

Simple Example
______________

.. testcode::

    from event_processor import EventProcessor, Depends
    from event_processor.filters import Accept

    event_processor = EventProcessor()


    def get_my_value():
        return 42


    @event_processor.processor(Accept())
    def my_processor(my_value : int = Depends(get_my_value)):
        print(my_value)


    event_processor.invoke({})

.. testoutput::

    42

Caching Example
_______________

If a value should always be dynamic, caching can easily be disabled. Note that two dependencies can refer to the same
callable to get a value, and will still honor the caching decision. That is, one call to the callable may be cached,
whereas another may not.

.. testcode::

    from event_processor import EventProcessor, Depends
    from event_processor.filters import Accept, Exists

    event_processor = EventProcessor()
    numeric_value = 0


    def get_my_value():
        global numeric_value
        numeric_value = numeric_value + 1
        return numeric_value


    @event_processor.processor(Accept())
    def my_processor_with_caching(my_value : int = Depends(get_my_value)):
        print(my_value)


    # Note the rank is required because otherwise Accept() will match anything
    @event_processor.processor(Exists("a"), rank=1)
    def my_processor_with_caching(my_value : int = Depends(get_my_value, cache=False)):
        print(my_value)


    event_processor.invoke({})
    event_processor.invoke({})
    event_processor.invoke({"a": 0})

.. testoutput::

    1
    1
    2

Nesting Example
_______________

You can also nest dependencies as deep as you want to go, so you can easily re-use them.

.. testcode::

    from event_processor import EventProcessor, Depends
    from event_processor.filters import Accept

    event_processor = EventProcessor()


    def get_zero():
        return 0


    # This dependency can itself depend on another value
    def get_my_value(zero: int = Depends(get_zero)):
        return zero + 1


    @event_processor.processor(Accept())
    def my_processor_with_caching(my_value : int = Depends(get_my_value)):
        print(my_value)


    event_processor.invoke({})

.. testoutput::

    1

Class Dependencies
__________________

Classes themselves are also callables. By default, their init method will be called when you call them, so you can use
classes as dependencies as well.

.. testcode::

    from event_processor import EventProcessor, Depends, Event
    from event_processor.filters import Exists

    event_processor = EventProcessor()


    class MyThing:
        def __init__(self, event: Event):
            self.username = event["username"]

        def get_username(self):
            return self.username


    @event_processor.processor(Exists("username"))
    def my_processor_with_caching(my_thing : MyThing = Depends(MyThing)):
        print(my_thing.get_username())


    event_processor.invoke({"username": "someone"})

.. testoutput::

    someone

Event Dependencies
------------------

Sometimes it's useful for processors to receive a copy of the event that triggered their invocation, so you can easily
signal that it is required by your processor by having a parameter annotated with the ``Event`` type.

.. note::
    Event dependencies follow the same rules as other dependencies in that other dependencies can depend on the event,
    allowing dynamic fetching of data or just creation of a convenient type for the event.

Here's an example of a simple event dependency :

.. testcode::

    from event_processor import EventProcessor, Event
    from event_processor.filters import Accept

    event_processor = EventProcessor()


    @event_processor.processor(Accept())
    def my_processor_with_caching(event: Event):
        print(event)


    event_processor.invoke({"hello": "world"})

.. testoutput::

    {'hello': 'world'}

And here's an example where a dependency depends on the event :

.. testcode::

    from event_processor import EventProcessor, Event
    from event_processor.filters import Exists

    event_processor = EventProcessor()


    # This function could also query a database (in which case it might depend
    # on another function that will return a connection from a connection pool).
    def extract_email(event: Event):
        return event["email"]


    @event_processor.processor(Exists("email"))
    def my_processor_with_caching(email: str = Depends(extract_email)):
        print(email)


    event_processor.invoke({"email": "someone@example.com"})

.. testoutput::

    someone@example.com
