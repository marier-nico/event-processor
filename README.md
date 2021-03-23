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

from event_processor import EventProcessor


event_processor = EventProcessor()


@event_processor.processor({"service.type": "service_a"})
def process_service_a(event: Dict):
    return event["service"]["status"] == "up"

@event_processor.processor({"service.type": "service_b"})
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
event_processor.invoke(service_a_event)  # False
event_processor.invoke(service_b_event)  # False
```

# Documentation

Find the full documentation on [Read the Docs](https://event-processor.readthedocs.io/).

# Use-Cases

[//]: # (Keep this entire section up to date with index.rst)

This library is very generic and it applies to several different problems in several different domains, so here are some
use-cases for it. Hopefully this might give you an idea for how the library is applicable to your own use-cases.

## FaaS (AWS, GCP, Azure)

This library is very useful in cloud computing environments where functions as a service are used, such with AWS Lambda,
Google Cloud Functions or Azure Functions. These platforms are frequently used to manage the cloud account. For example,
by running functions when a resource is launched, or simply on a schedule. They're also used for monitoring. In most
cases, functions will take an event as input and should take different actions based on the value of that event.

event-processor is helpful with the architecture of such functions, because it allows easily forwarding events to the
right function for processing.

### AWS - CloudWatch Alarm -> SNS -> Lambda

```python
import json

from event_processor import EventProcessor


event_processor = EventProcessor()


# Truncated for readability
cloudwatch_event = {
    "id": "c4c1c1c9-6542-e61b-6ef0-8c4d36933a92",
    "detail-type": "CloudWatch Alarm State Change",
    "detail": {
        "alarmName": "ServerCpuTooHigh",
        "previousState": {
            "value": "OK"
        },
        "state": {
            "value": "ALARM"
        }
    }
}

lambda_event = {
  "Records": [
    {
      "Sns": {
        "Subject": "TestInvoke",
        "Message": json.dumps(cloudwatch_event)
      }
    }
  ]
}


class DummySlackClient:
    def send_message(self, message: str):
        print(f"Send in slack: {message}")


@event_processor.dependency_factory
def messaging_service(service: str):
    if service == "slack":
        return DummySlackClient()
    else:
        raise NotImplementedError()


@event_processor.processor(
    {"detail.previousState.value": "OK", "detail.state.value": "ALARM"},
    messaging_service=("slack",)
)
def process_started_alarming(event, slack_client: DummySlackClient):
    slack_client.send_message(f"Alarm {event['detail']['alarmName']} went from OK to ALARM")


@event_processor.processor({}, messaging_service=("slack",))  # Default processor
def default_processor(event, slack_client: DummySlackClient):
    slack_client.send_message(f"Unexpected event: {event}")


def demo_lambda_main(event, _context):
    # You can pre-process events as much as you like before calling invoke.
    # You could also just process the whole raw event, but then filters would
    # be less useful since they couldn't filter against the cloudwatch event.
    # It would also be possible to just update the raw event by parsing the
    # json contained within, so it would be possible to filter on anything.

    cloudwatch_event = json.loads(event["Records"][0]["Sns"]["Message"])
    event_processor.invoke(cloudwatch_event)


demo_lambda_main(lambda_event, {})
lambda_event["Records"][0]["Sns"]["Message"] = json.dumps({"Unexpected": "Oops!"})
demo_lambda_main(lambda_event, {})
```

```
Send in slack: Alarm ServerCpuTooHigh went from OK to ALARM
Send in slack: Unexpected event: {'Unexpected': 'Oops!'}
```
