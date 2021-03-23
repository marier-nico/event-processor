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

Bigger Apps & Modules
---------------------

All these examples have assumed everything happens in a single file, which is not the case for most application. So if
your application is a bit more substantial and you want to split it up into modules, this is how you do it.

.. note::

   This example does not feature dependency factories, but it works the same way. You can simply add factories to
   subprocessors and they will automatically get added to the main processor when you call ``add_subprocessor`` on it.
   Also, if a factory with a given name already exists in the main processor, it will not be added again, so if you have
   multiple factories with the same name, but different behavior, the one in the main processor will be used.

.. code-block:: python
   :caption: my_processor.py

   from event_processor import EventProcessor


   event_processor = EventProcessor()


   @event_processor.processor({"key": "value"})
   def my_processor(event):
      return event["key"]

.. code-block:: python
   :caption: main.py

   from event_processor import EventProcessor

   from src.my_processor import event_processor as my_processor


   main_processor = EventProcessor()
   main_processor.add_subprocessor(my_processor)


   def main(event):
      print(main_processor.invoke(event))

.. code-block::

   >>> main({"key": "value"})
   value


The idea here is to define isolated processors in python submodules (as seen in ``my_processor.py``) and to import those
processors back into the main module, to add them as subprocessors to the main processor. You can add as many
subprocessors as you want, but there can be no overlap in filter expressions, just like if you were always using the
same event processor.

This is unfortunately required because of the way Python imports work. It would not be possible to instead import the
main procesor from submodules, because then since nothing would import the submodules, the processors would never be
registered.
