# Process Events In Style

![build](https://img.shields.io/github/checks-status/marier-nico/event-processor/main)
![coverage](https://img.shields.io/codecov/c/github/marier-nico/event-processor?token=RELUVFBJHX)
![code-size](https://img.shields.io/github/languages/code-size/marier-nico/event-processor)
![docs](https://readthedocs.org/projects/event-processor/badge/?version=latest)

event-processor is a library that aims to simplify the common pattern of event processing. It simplifies the process of
filtering, dispatching and pre-processing events as well as injecting dependencies in event processors.

The only requirement is that your events are regular python dictionaries. Python 3.7+ is supported.

Here's a very basic example of simple event filtering and dispatching. This is as simple as it gets, just calling the
right processor depending on the event:

```python
from typing import Dict

from event_processor import processor, invoke


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
```

# Documentation

Find the full documentation on [Read the Docs](https://event-processor.readthedocs.io/).
