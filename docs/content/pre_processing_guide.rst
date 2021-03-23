Pre-Processing Guide
====================

Pre-processors are useful when you want to modify the input event before passing it on to your processor. It's mostly a
convenience feature, because processors can always just accept the event and use it directly. Though, because
pre-processors are any function, they can also fetch additional values not present in the event.

Structural Pre-Processing
-------------------------

One use of pre-processors is to change the structure of input events to make them more convenient to manipulate for
processors. For example, you could turn an input event into a dataclass:

.. testcode::

    from dataclasses import dataclass
    from typing import Any, Dict

    from event_processor import EventProcessor


    event_processor = EventProcessor()


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

    @event_processor.processor(
        {"user.name": Any, "user.email": Any, "user.role": Any},
        pre_processor=event_to_user
    )
    def my_processor(user: User):  # The processor takes a User
        return user.role == "admin"

    print(
        event_processor.invoke({"user": {"name": "John", "email": "john@example.com", "role": "admin"}}),
        event_processor.invoke({"user": {"name": "Bob", "email": "bob@example.com", "role": "user"}}),
    )

.. testoutput::

    True False

Data Pre-Processing
-------------------

Another use of pre-processors is to fetch additional external data from, realistically, any source you could imagine.
This can also be combined with dependencies to create dynamic pre-processors that can fetch data from external sources.
Here's an example:

.. testcode::

    from event_processor import EventProcessor


    event_processor = EventProcessor()


    @dataclass
    class User:
        name: str
        email: str
        role: str


    class FakeDbClient:
        database = {
            "admin@example.com": {"role": "admin", "name": "John"},
            "user@example.com": {"role": "user", "name": "Bob"}
        }

        def fetch_by_email(self, email: str) -> User:
            user = self.database.get(email, {})
            return User(
                name=user["name"],
                email=email,
                role=user["role"]
            )


    def event_to_user(event: Dict, db_client: FakeDbClient) -> User:
        email = event["user"]["email_3"]
        user = db_client.fetch_by_email(email=email)
        return user


    @event_processor.dependency_factory
    def db_client(_name: str) -> FakeDbClient:
        return FakeDbClient()


    @event_processor.processor(
        {"user.email_3": Any},
        pre_processor=event_to_user,
        db_client=("my_db",)
    )
    def my_processor(user: User):
        return user.role == "admin"


    print(
        event_processor.invoke({"user": {"email_3": "user@example.com"}}),
        event_processor.invoke({"user": {"email_3": "admin@example.com"}})
    )

.. testoutput::

    False True

For more details on dependency injection, see the :ref:`Dependency Injection Guide`. The gist is that you can specify
dependencies in the decorator, and they will automatically be injected into either the processor, pre-processor, or
both, depending on the parameters.

Bigger Data Pre-Processing Example
----------------------------------

.. include:: shared/full_example.rst
