# Database Usage Example

In this example, you can get a sense for :

- How to integrate event-processor with a database by using dependency injection.
- How to accept dict payloads (perhaps coming from JSON) with pydantic.
- How to return JSON payloads with pydantic.
- How to use pydantic validators.

The example is useful if you're building :

- A system to handle user requests which uses JSON.
- A system that needs to access a database.

## Highlighted Concepts

**`handle_event`**

This function is useful to catch exceptions returned by event-processor and pydantic and converting those responses
into JSON.

**Returning Pydantic models**

This is a good idea because it allows easily returning JSON responses with a standard format. It also allows you to
easily validate responses as well.

**Using Pydantic models in event processor parameters**

This allows you to offload data validation to pydantic. This means you also automatically get relevant and friendly
error messages to return.

**Default processor**

This is useful because it allows you to return useful messages when you receive data you weren't expecting. You could
improve on the example by logging errors here instead of just returning a message.

## Caveats

**Fake database**

In the real world, you would obviously use a real database where you will probably want to use sessions or connection
pools. To do this, you would have to adapt the example somewhat, but the core idea is the same : you want to have one
function to return a connection from a pool, or a new session. **Don't forget to disable caching on that dependency!**

**Password hashing**

The hash function used in the example is not secure for reasons that _should_ be obvious. If you need to hold onto
passwords in your database, use something like [passlib](https://passlib.readthedocs.io/en/stable/). Crypto is hard to
get right, and you _really_ don't want to mess this up.
