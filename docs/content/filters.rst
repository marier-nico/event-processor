.. _filters-detail:

Filters
=======

There are a few available filters to help you make sure the correct processor is invoked for the correct event. To see
how to use filters in practice, see the :ref:`core concepts<core-concepts-example>`.

.. warning::
    It's possible to create different filters that will match the same event. For example, when using the :ref:`Exists`
    and :ref:`Eq` filters on the same key, if the :ref:`Eq` filter matches, then the :ref:`Exists` filter is guaranteed
    to match.

    Have a look at :ref:`Ranking Processors` to learn how to resolve these ambiguities. Also, note that these issues may
    not apply to your context. You only have to worry about this if you have ambiguous filters.

Accept
------

This filter will always match any event it is presented with. It will even match things that are not dictionaries. Use
this if you need to take a default action whenever no processor exists for an event, or if an unexpected event was sent
to your system.

.. testcode::

    from event_processor.filters import Accept

    accept = Accept()

    print(accept.matches({}))
    print(accept.matches(None))
    print(accept.matches({"Hello", "World"}))

.. testoutput::

    True
    True
    True

Exists
------

This filter matches events that contain a certain key (which can be nested), but the value can be anything.

.. testcode::

    from event_processor.filters import Exists

    a_exists = Exists("a")
    nested = Exists("a.b.c")

    print(a_exists.matches({"a": None}))
    print(a_exists.matches({"a": 2}))
    print(a_exists.matches({}))
    print(nested.matches({"a": {"b": {"c": None}}}))
    print(nested.matches({"a": {"b": {"c": 0}}}))

.. testoutput::

    True
    True
    False
    True
    True

Eq
--

This filter matches a subset of the events matched by :ref:`Exists`. It only matches the events where a specific value
is found at the specified key (as opposed to just existing).

.. testcode::

    from event_processor.filters import Eq

    a_is_b = Eq("a", "b")
    a_b_c_is_none = Eq("a.b.c", None)

    print(a_is_b.matches({"a": "b"}))
    print(a_is_b.matches({"a": 2}))
    print(a_b_c_is_none.matches({"a": {"b": {"c": None}}}))
    print(a_b_c_is_none.matches({"a": {"b": {"c": 0}}}))

.. testoutput::

    True
    False
    True
    False

And
---

This filter does exactly what you would expect, and matches when all the events supplied to it as arguments match. It
acts as a logical AND between all its sub-filters.

.. testcode::

    from event_processor.filters import And, Exists

    a_exists = Exists("a")
    b_exists = Exists("b")
    c_exists = Exists("c")

    a_and_b_exist = And(a_exists, b_exists)
    a_b_and_c_exist = And(a_exists, b_exists, c_exists)

    print(a_and_b_exist.matches({"a": 0, "b": 0}))
    print(a_and_b_exist.matches({"a": 0, "b": 0, "c": 0}))
    print(a_b_and_c_exist.matches({"a": 0, "b": 0}))
    print(a_b_and_c_exist.matches({"a": 0, "b": 0, "c": 0}))

.. testoutput::

    True
    True
    False
    True

You can also use ``&`` between processors instead of ``And`` explicitly to make your filters prettier.

.. testcode::

    from event_processor.filters import And, Exists

    a_exists = Exists("a")
    b_exists = Exists("b")
    c_exists = Exists("c")

    a_and_b_exist = a_exists & b_exists
    a_b_and_c_exist = a_exists & b_exists & c_exists

    print(a_and_b_exist.matches({"a": 0, "b": 0}))
    print(a_and_b_exist.matches({"a": 0, "b": 0, "c": 0}))
    print(a_b_and_c_exist.matches({"a": 0, "b": 0}))
    print(a_b_and_c_exist.matches({"a": 0, "b": 0, "c": 0}))

.. testoutput::

    True
    True
    False
    True

Or
--

This filter is similar to the :ref:`And` filter, except that it will match if any of its sub-filters match.

.. testcode::

    from event_processor.filters import Or, Exists

    a_exists = Exists("a")
    b_exists = Exists("b")
    c_exists = Exists("c")

    a_b_or_c_exist = Or(a_exists, b_exists, c_exists)

    print(a_b_or_c_exist.matches({"a": 0}))
    print(a_b_or_c_exist.matches({"b": 0}))
    print(a_b_or_c_exist.matches({"c": 0}))
    print(a_b_or_c_exist.matches({"d": 0}))

.. testoutput::

    True
    True
    True
    False

Again, to make things more ergonomic, you can use ``|`` instead of ``Or``.

.. testcode::

    from event_processor.filters import Or, Exists

    a_exists = Exists("a")
    b_exists = Exists("b")
    c_exists = Exists("c")

    a_b_or_c_exist = a_exists | b_exists | c_exists

    print(a_b_or_c_exist.matches({"a": 0}))
    print(a_b_or_c_exist.matches({"b": 0}))
    print(a_b_or_c_exist.matches({"c": 0}))
    print(a_b_or_c_exist.matches({"d": 0}))

.. testoutput::

    True
    True
    True
    False
