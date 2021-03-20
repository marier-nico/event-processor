Process Events In Style
=======================

This library aims to simplif the common pattern of event processing. It simplifies the process of filtering,
dispatching and pre-processing events as well as injecting dependencies in event processors.

The only requirement is that your events are regular python dictionaries.

Take a look at the following examples to get an overview of the features available! Of course, you can mix and combine
them in any way you like to create more complex scenarios.

.. contents:: :local:

Simple Filtering
----------------

This is as simple as it gets, just calling the right processor depending on the event.

.. code-block:: python

    @processor({"service.type": "service_a"})
    def process_service_a(event: Dict):
        return event["service"]["status"] == "up"

    @processor({"service.type": "service_b"})
    def process_service_b(event: Dict):
        return event["authorized"]

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
    invoke(service_a_event)  # False
    invoke(service_b_event)  # False

Any Filter
----------

Sometimes you want to make sure there's a value at a given path in the event, but you don't care what it is, or you may
want to dynamically do things with it in the processor.

.. code-block:: python

    from typing import Any

    @processor({"user.email": Any})
    def process_user(event: Dict):
        return event["user"]["email"] == "admin@example.com"

    invoke({"user": {"email": "admin@example.com"}})  # True
    invoke({"user": {"email": "not-admin@example.com"}})  # False

Pre-Processing
--------------

It can be convenient to to work with actual python objects rather than raw dictionaries, so you can use pre-processors
for processors.

.. code-block:: python

    from dataclasses import dataclass
    from typing import Any

    database = {
        "user@example.com": {"role": "user"},
        "admin@example.com": {"role": "admin}
    }

    @dataclass
    class User:
        email: str
        role: str

    def event_to_user(event: Dict):
        email = event["user"]["email"]
        role = database.get(email, {}).get("role")
        return User(email=email, role=role)

    @processor({"user.email": Any}, pre_processor=event_to_user)
    def process_user(user: User):
        return user.role == "admin"

Dependency Injection
--------------------

Sometimes, you might want to call external services from a processor, so you can have your dependencies automatically
injected.

.. code-block:: python

    import boto3
    from typing import Any

    @dependency_factory
    def boto3_clients(client_name: str) -> boto3.client:
        boto3.client(client_name)

    @processor({"user.email": Any}, boto3_clients=("ssm",))
    def process_user(event: Dict, ssm_client: boto3.client):
        ssm_response = ssm_client.get_parameter(Name="admin_email")
        admin_email = ssm_response["Parameter"]["Value"]
        return event["user"]["email"] == admin_email

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   content/filtering_guide
   content/pre_processing_guide
   content/dependency_injection_guide
   content/testing_processors
   content/code

Changelog
---------

.. include:: content/changelog.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
