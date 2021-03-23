Quick Start
===========

Here are some examples to illustrate common features of the library. These examples are not exhaustive, so you are
encouraged to still look through the rest of the docs to discover more powerful or less common use-cases.

Simple Filtering
----------------

This is as simple as it gets, just calling the right processor depending on the event.

.. testcode::

    from typing import Dict

    from event_processor import EventProcessor


    event_processor = EventProcessor()


    @event_processor.processor({"service.type": "service_a"})
    def process_service_a(event: Dict):
        return event["service"]["status"] == "up"

    @event_processor.processor({"service.type": "service_b"})
    def process_service_b(event: Dict):
        return event["service"]["authorized"]

    service_a_event = {
        "service": {
            "type": "service_a",
            "status": "down"
        }
    }
    service_b_event = {
        "service": {
            "type": "service_b",
            "authorized": False
        }
    }

    print(event_processor.invoke(service_a_event), event_processor.invoke(service_b_event))

.. testoutput::

    False False

Any Filter
----------

Sometimes you want to make sure there's a value at a given path in the event, but you don't care what it is, or you may
want to dynamically do things with it in the processor.

.. testcode::

    from typing import Any, Dict

    from event_processor import EventProcessor


    event_processor = EventProcessor()


    @event_processor.processor({"user.email": Any})
    def process_user(event: Dict):
        return event["user"]["email"] == "admin@example.com"

    print(
        event_processor.invoke({"user": {"email": "admin@example.com"}}),
        event_processor.invoke({"user": {"email": "not-admin@example.com"}})
    )

.. testoutput::

    True False

Pre-Processing
--------------

It can be convenient to to work with actual python objects rather than raw dictionaries, so you can use pre-processors
for processors.

.. testcode::

    from dataclasses import dataclass
    from typing import Any, Dict

    from event_processor import EventProcessor


    event_processor = EventProcessor()


    database = {
        "user@example.com": {"role": "user"},
        "admin@example.com": {"role": "admin"}
    }

    @dataclass
    class User:
        email: str
        role: str

    def event_to_user(event: Dict):
        email = event["user"]["email"]
        role = database.get(email, {}).get("role")
        return User(email=email, role=role)

    @event_processor.processor({"user.email": Any}, pre_processor=event_to_user)
    def process_user(user: User):
        return user.role == "admin"

    print(
        event_processor.invoke({"user": {"email": "user@example.com"}}),
        event_processor.invoke({"user": {"email": "admin@example.com"}})
    )

.. testoutput::

    False True


Dependency Injection
--------------------

Sometimes, you might want to call external services from a processor, so you can have your dependencies automatically
injected.

.. testcode::

    from typing import Any

    from event_processor import EventProcessor


    event_processor = EventProcessor()


    class FakeBotoClient:
        parameters = {"admin_email": "admin@example.com"}

        def get_parameter(self, Name=""):
            return {"Parameter": {"Value": self.parameters.get(Name)}}

    @event_processor.dependency_factory
    def boto3_clients(client_name: str):
        if client_name == "ssm":
            return FakeBotoClient()
        else:
            raise NotImplementedError()

    @event_processor.processor({"user.email": Any}, boto3_clients=("ssm",))
    def process_user(event: Dict, ssm_client: FakeBotoClient):
        ssm_response = ssm_client.get_parameter(Name="admin_email")
        admin_email = ssm_response["Parameter"]["Value"]
        return event["user"]["email"] == admin_email

    print(
        event_processor.invoke({"user": {"email": "admin@example.com"}}),
        event_processor.invoke({"user": {"email": "user@example.com"}})
    )

.. testoutput::

    True False
