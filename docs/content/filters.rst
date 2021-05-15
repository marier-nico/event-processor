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

NumCmp
------

This filter matches numbers that satisfy a comparison function with a given target.

.. note::
    You should try to avoid using this filter directly and instead use :ref:`Lt, Leq, Gt, Geq` when possible.

    The reason for this advisory is that in python, callables with the same code will compare as not being equal, which
    means that if you start using lambdas as the comparator (and more critically, if you use different lambdas that have
    the same behavior as comparators), then the equality checks for this filter will be inaccurate. This leads to
    duplicate processors not raising exceptions at import time.

    The tl;dr: if you use this filter, don't use lambdas as comparators and don't use different functions that do the
    same thing either.

.. testcode::

    from event_processor.filters import NumCmp

    def y_greater_than_twice_x(x, y):
        return (2 * x) < y

    # Note that the comparator is the same here, this is important.
    # You can use different comparators, but only if they do different things.
    twice_a_less_than_four = NumCmp("a", y_greater_than_twice_x, 4)
    twice_a_less_than_eight = NumCmp("a", y_greater_than_twice_x, 8)

    print(twice_a_less_than_four.matches({"a": 1}))
    print(twice_a_less_than_four.matches({"a": 2}))
    print(twice_a_less_than_eight.matches({"a": 3}))
    print(twice_a_less_than_eight.matches({"a": 4}))
    print(twice_a_less_than_eight.matches({"not-a": 2}))

.. testoutput::

    True
    False
    True
    False
    False

Lt, Leq, Gt, Geq
----------------

These filters all work in the same way in that they match when a value is present at the given path and it satisfies a
comparison operation.

* ``Lt`` means ``<``
* ``Leq`` means ``<=``
* ``Gt`` means ``>``
* ``Geq`` means ``>=``

.. testcode::

    from event_processor.filters import Lt, Leq, Gt, Geq

    a_lt_0 = Lt("a", 0)
    a_leq_0 = Leq("a", 0)
    a_gt_0 = Gt("a", 0)
    a_geq_0 = Geq("a", 0)

    print(a_lt_0.matches({"a": 0}))
    print(a_leq_0.matches({"a": 0}))
    print(a_gt_0.matches({"a": 0}))
    print(a_geq_0.matches({"a": 0}))

.. testoutput::

    False
    True
    False
    True

Dyn
---

This filter accepts a resolver parameter, which is any callable. Whether or not it matches a given event depends on the
return value of the resolver. If the resolver returns a truthy value, then the filter matches. Otherwise, it doesn't.
This is useful when your events have a more complex structure that can't really be handled by other existing filters.

.. warning::
    When using a dynamic filter, it's your job to make sure the functions you supply won't match the same events (and
    if they do, to specify a :ref:`rank<Ranking Processors>` or an :ref:`invocation strategy<Invocation Strategy>`).

With the Dyn filter, it's useful to use lambda functions because they fit nicely in one line and won't clutter your
code. If you use lambda functions, the functions you create **must** accept a single argument (which will be the event).

.. testcode::

    from event_processor.filters import Dyn

    a_len_is_0 = Dyn(lambda e: len(e.get("a", [])) == 0)
    a_len_is_bigger = Dyn(lambda e: len(e.get("a", [])) >= 1)

    print(a_len_is_0.matches({"a": []}))
    print(a_len_is_0.matches({"a": [0]}))
    print(a_len_is_bigger.matches({"a": []}))
    print(a_len_is_bigger.matches({"a": [0, 1]}))

.. testoutput::

    True
    False
    False
    True

It's also possible to use standard functions with the Dyn filter, in which case you can specify any argument that would
be valid for a dependency (see :ref:`Dependencies` for details). For example :

.. testcode::

    from event_processor import Depends, Event
    from event_processor.filters import Dyn

    def my_dependency():
        return 0

    def my_filter_resolver(event: Event, dep_value: int = Depends(my_dependency)):
        return event["key"] == dep_value

    a_filter = Dyn(my_filter_resolver)

    print(a_filter.matches({"key": 0}))
    print(a_filter.matches({"key": 1}))

.. testoutput::

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
