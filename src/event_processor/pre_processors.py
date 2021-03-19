"""Built-in event preprocessors."""


def passthrough(event):
    """Passthrough the event without touching it.

    :param event: The input event.
    :return: The input event.
    """
    return event
