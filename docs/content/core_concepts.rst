Core Concepts
=============

The core idea of this library is really simple. All you have are processors, filters and dependencies. Read on to learn
more about each concept.

.. _processors-concept:

Processors
----------

Processors are simply functions that you create to process a certain event. Which processor gets called for which event
depends on the filters you use for that processor. More info on the :ref:`processors<processors-detail>` page.

.. _filters-concept:

Filters
-------

Filters are how you tell the library which processor to invoke for each event you want to process. There's a few
different kinds of filters, the most common being the ``Exists`` filter and the ``Eq`` filter. More info on the
:ref:`filters<filters-detail>` page.

.. note::
    It's possible to have ambiguous filters (see :ref:`Filters<filters-detail>` for details). To resolve them, take a
    look at :ref:`Ranking Processors` and :ref:`Invocation Strategies<Invocation Strategy>`.

.. _dependencies-concept:

Dependencies
------------

Dependencies are a pretty key concept, because they allow your processors to depend on values obtained dynamically
(which is super important if you want to use external APIs in your processors). It's also possible to depend on the
event (so you can have it injected into your processor). More info on the :ref:`dependencies<dependencies-detail>` page.

.. _core-concepts-example:

Example
-------

This example shows how these three concepts click together to make event processing easy. For the example, we just use
a stub for the SSM client and assume that the ``admin_email`` parameter has a value of ``admin@example.com``.

.. testsetup:: core_concepts

    class FakeSSMClient:
        parameters = {"admin_email": "admin@example.com"}

        def get_parameter(self, Name=""):
            return {"Parameter": {"Value": self.parameters.get(Name)}}

.. testcode:: core_concepts

    from event_processor import EventProcessor, Event, Depends
    from event_processor.filters import Exists

    event_processor = EventProcessor()


    def get_ssm():
        return FakeSSMClient()


    @event_processor.processor(Exists("user.email"))
    def user_is_admin(raw_event: Event, ssm_client: FakeSSMClient = Depends(get_ssm)) -> bool:
        ssm_response = ssm_client.get_parameter(Name="admin_email")
        admin_email = ssm_response["Parameter"]["Value"]
        return raw_event["user"]["email"] == admin_email

    print("admin@example.com is admin:", event_processor.invoke({"user": {"email": "admin@example.com"}}))
    print("user@example.com is admin:", event_processor.invoke({"user": {"email": "user@example.com"}}))

.. testoutput:: core_concepts

    admin@example.com is admin: True
    user@example.com is admin: False


You can see that because the event contains a value at ``user.email`` (i.e. this path ``Exists`` in the event), the
processor was invoked. It also received the event by specifying a parameter with the ``Event`` type and received an SSM
client by depending on the value returned by ``get_ssm``.
