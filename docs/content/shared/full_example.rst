.. code-block:: python
    :caption: pre-processor

    from dataclasses import dataclass

    import boto3


    @dataclass
    class User:
        email: str
        role: str


    # Uses the dynamodb client specified in the processor decorator
    def event_to_user(event: Dict, dynamodb_client: boto3.client):
        email = event["user"]["email"]
        response = dynamodb_client.get_item(
                        TableName="users",
                        Key={"Email": {"S": email}}
                   )
        role = response["Item"]["Role"]["S"]

        return Usesr(email=email, role=role)

.. code-block:: python
    :caption: processor

    from typing import Any

    from event_processor import processor


    # Does not use the dynamodb client, but needs it for pre-processing
    @processor(
        {"user.email": Any},
        pre_processor=event_to_user,
        boto_clients=("dynamodb",)
    )
    def my_processor(user: User):
        return user.role == "admin"

.. code-block:: python
    :caption: dependency-factory

    import boto3
    from event_processor import dependency_factory


    @dependency_factory
    def boto_clients(client_name: str) -> boto3.client:
        return boto3.client(client_name)
