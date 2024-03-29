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

.. warning::
    Caching happens per-invocation, so if a sub-dependency is used by many dependencies, it will only be resolved once
    per invocation. If you invoke the same processor again, the dependency will be invoked again.

    If you want something to be cached permanently, you should look at
    `python's cache decorator <https://docs.python.org/3/library/functools.html#functools.cache>`_.

Simple Example
______________

.. testcode::

    from event_processor import EventProcessor, Depends
    from event_processor.filters import Accept

    processor = EventProcessor()


    def get_my_value():
        return 42


    @processor(Accept())
    def my_processor(my_value : int = Depends(get_my_value)):
        print(my_value)


    processor.invoke({})

.. testoutput::

    42

Nesting Example
_______________

You can also nest dependencies as deep as you want to go, so you can easily re-use them.

.. testcode::

    from event_processor import EventProcessor, Depends
    from event_processor.filters import Accept

    processor = EventProcessor()


    def get_zero():
        return 0


    # This dependency can itself depend on another value
    def get_my_value(zero: int = Depends(get_zero)):
        return zero + 1


    @processor(Accept())
    def my_processor_with_caching(my_value : int = Depends(get_my_value)):
        print(my_value)


    processor.invoke({})

.. testoutput::

    1

Class Dependencies
__________________

Classes themselves are also callables. By default, their init method will be called when you call them, so you can use
classes as dependencies as well.

.. testcode::

    from event_processor import EventProcessor, Depends, Event
    from event_processor.filters import Exists

    processor = EventProcessor()


    class MyThing:
        def __init__(self, event: Event):
            self.username = event["username"]

        def get_username(self):
            return self.username


    @processor(Exists("username"))
    def my_processor_with_caching(my_thing : MyThing = Depends(MyThing)):
        print(my_thing.get_username())


    processor.invoke({"username": "someone"})

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

    processor = EventProcessor()


    @processor(Accept())
    def my_processor_with_caching(event: Event):
        print(event)


    processor.invoke({"hello": "world"})

.. testoutput::

    {'hello': 'world'}

And here's an example where a dependency depends on the event :

.. testcode::

    from event_processor import EventProcessor, Event
    from event_processor.filters import Exists

    processor = EventProcessor()


    # This function could also query a database (in which case it might depend
    # on another function that will return a connection from a connection pool).
    def extract_email(event: Event):
        return event["email"]


    @processor(Exists("email"))
    def my_processor_with_caching(email: str = Depends(extract_email)):
        print(email)


    processor.invoke({"email": "someone@example.com"})

.. testoutput::

    someone@example.com

Pydantic Dependencies
---------------------

`Pydantic <https://pydantic-docs.helpmanual.io/>`_ is a library which helps with data validation and settings management
using python type annotations. You can leverage it in event processors to benefit from both the convenience of
automatically parsing an event into a given type and having it fully validated. Pydantic can also provide detailed and
friendly error messages to users for validation errors.

Here's a simple example to illustrate how the event might be parsed for use in a processor :

.. testcode::

    from event_processor import EventProcessor
    from event_processor.filters import Eq
    from pydantic import BaseModel

    processor = EventProcessor()


    class CreateUserQuery(BaseModel):
        email: str
        password: str


    @processor(Eq("query", "create_user"))
    def handle_user_creation(query: CreateUserQuery):
        print(query.email)
        print(query.password)


    processor.invoke(
        {"query": "create_user", "email": "someone@example.com", "password": "hunter2"}
    )

.. testoutput::

    someone@example.com
    hunter2

You can also add custom validations for fields using `validators <https://pydantic-docs.helpmanual.io/usage/validators/>`_
as well as many other things. Take a look at the pydantic docs to learn more!


Scalar Dependencies
-------------------

Sometimes, you don't need many parts of an input event, just one or two fields, so depending on the whole event or
having to make a pydantic model just for a few fields might feel excessive. This is what scalar dependencies are good
for.

.. warning::
    If you want to benefit from type validation for your scalar dependencies, you need to have pydantic installed. If
    you don't have pydantic, no types will be validated for scalar dependencies (really, not even basic ones).

    Also, if you *do* use pydantic, but don't specify a type annotation for a parameter, then ``typing.Any`` is assumed.

Here's a very basic example :

.. testcode::

    from event_processor import EventProcessor
    from event_processor.filters import Exists

    processor = EventProcessor()


    @processor(Exists("email"))
    def handle_user(email: str):
        print(email)


    processor.invoke({"email": "someone@example.com"})

.. testoutput::

    someone@example.com

Here's an example with a pydantic field type :

.. testcode::

    from event_processor import EventProcessor
    from event_processor.filters import Exists
    from pydantic import ValidationError
    from pydantic.color import Color

    processor = EventProcessor()


    @processor(Exists("my_color"))
    def handle_user(my_color: Color):
        print(my_color.as_hex())


    processor.invoke({"my_color": "white"})

    try:
        processor.invoke({"my_color": "not-a-color"})
    except ValidationError as e:
        print(e.errors()[0]["msg"])

.. testoutput::

    #fff
    value is not a valid color: string not recognised as a valid color
