Pre-Processing Guide
====================

Pre-processors are useful when you want to modify the input event before passing it on to your processor. It's mostly a
convenience feature, because processors can always just accept the event and use it directly. Though, because
pre-processors are any function, they can also fetch additional values not present in the event.

Structural Pre-Processing
-------------------------

One use of pre-processors is to change the structure of input events to make them more convenient to manipulate for
processors. For example, you could turn an input event into a dataclass:

.. code-block:: python

    from dataclasses import dataclass
    from typing import Any

    from event_processor import processor


    @dataclass
    class User:
        name: str
        email: str
        role: str

    def event_to_user(event: Dict) -> User:  # This is a pre-processor
        user = event["user"]
        return User(
            name=user["name"],
            email=user["email"],
            role=user["role"]
        )

    @processor(
        {"user.name": Any, "user.email": Any, "user.role": Any},
        pre_processor=event_to_user
    )
    def my_processor(user: User):  # The processor takes a User
        return user.role == "admin"

Data Pre-Processing
-------------------

Another use of pre-processors is to fetch additional external data from, realistically, any source you could imagine.
This can also be combined with dependencies to create dynamic pre-processors that can fetch data from external sources.
Here's an example:

.. code-block:: python

    # Assuming the same User class as the previous example
    from event_processor import processor

    def event_to_user(event: Dict, db_client) -> User:
        email = event["user"]["email"]
        user = db_client.fetch_user_by_email(email=email)
        return user

    @processor(
        {"user.email": Any},
        pre_processor=event_to_user,
        db_client=("my_db",)
    )
    def my_processor(user: User):
        return user.role == "admin"

For more details on dependency injection, see the :ref:`Dependency Injection Guide`. The gist is that you can specify
dependencies in the decorator, and they will automatically be injected into either the processor, pre-processor, or
both, depending on the parameters.

Bigger Data Pre-Processing Example
----------------------------------

.. include:: shared/full_example.rst
