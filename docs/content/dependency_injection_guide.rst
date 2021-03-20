Dependency Injection Guide
==========================

Sometimes, you want processors to take actions on external resources or services. To do this, it's usually necessary to
use a client from a SDK, or a class you built yourself which encapsulates the state for your client.

These clients most often require authentication, API keys, or other such things. Dependency injection is a clean and
convenient solution to the problem of supplying clients to event processors.

Overview
--------

At its core, this library expects factory functions to exist for those clients (either made by you or not). These
factories are used to create client instances, which will be forwarded to processors or pre-processors. You should use
the :py:func:`processor_decorator.dependency_factory` decorator to register factory functions.

Registering Dependency Factories
--------------------------------

Only factories that have been previously registered can be used in the processor decorator. Those factories should be
registered with the :py:func:`processor_decorator.dependency_factory` decorator. Factories are just functions that take
a single string argument (the client or SDK name) and return an instance of the client or SDK.

Combining Dependencies and Pre-Processors
-----------------------------------------

This is a powerful use-case for both pre-processors and dependency injection. Since dependencies will be forwarded to
the pre-processor (optionally) as well as the processor (also optionally), it's possible to ues pre-processors to make
external API calls or to use a database. This keeps the processors very simple and it also allows the pre-processors to
fully benefit from dependency injection. You can find an example of this use-case in the :ref:`Pre-Processing Guide`.

When does Injection Occur?
---------------------------

Forwarding occurs when dependencies are specified in the processor decorator and either the processor itself or the
pre-processor require dependencies. They are determined to require dependencies whenever they take more than a single
parameter.

For processors and pre-processors, the first parameter will always be the event (or the output of pre-processing), so
other parameters will be dependencies. Do note that processors and pre-processors can either take no dependencies or all
depencies, they cannot only take a few dependencies.


Full Example
------------

An especially convenient use-case for dependency injection is the boto AWS client. You can use boto clients in your
processors like this:

.. include:: shared/full_example.rst
