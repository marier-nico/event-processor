# Process Events In Style

![build](https://img.shields.io/github/checks-status/marier-nico/event-processor/main)
![coverage](https://img.shields.io/codecov/c/github/marier-nico/event-processor?token=RELUVFBJHX)
![code-size](https://img.shields.io/github/languages/code-size/marier-nico/event-processor)
![docs](https://readthedocs.org/projects/event-processor/badge/?version=latest)

This library aims to simplify the common pattern of event processing. It simplifies the process of filtering,
dispatching and pre-processing events as well as injecting dependencies in event processors.

The only requirement is that your events are regular python dictionaries.

Take a look at the following examples to get an overview of the features available! Of course, you can mix and combine
them in any way you like to create more complex scenarios.

```python
from event_processor import EventProcessor, Event
from event_processor.filters import Eq


event_processor = EventProcessor()


@event_processor.processor(Eq("service.type", "service_a"))
def process_service_a(event: Event):
    return event["service"]["status"] == "up"

@event_processor.processor(Eq("service.type", "service_b"))
def process_service_b(event: Event):
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
event_processor.invoke(service_a_event)  # False
event_processor.invoke(service_b_event)  # False
```

# Documentation

Find the full documentation on [Read the Docs](https://event-processor.readthedocs.io/).
