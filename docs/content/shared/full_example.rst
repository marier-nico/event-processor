.. testcode::

    from dataclasses import dataclass
    from typing import Any, Dict

    from event_processor import EventProcessor


    event_processor = EventProcessor()


    class FakeDynamoClient:
        database = {
            "users": [
                {"Email": {"S": "user@example.com"}, "Role": {"S": "user"}},
                {"Email": {"S": "admin@example.com"}, "Role": {"S": "admin"}}
            ]
        }

        def get_item(self, TableName="", Key={}):
            table = self.database.get(TableName, {})
            key_name = list(Key.keys())[0]
            record = [e for e in table if e[key_name]["S"] == Key[key_name]["S"]][0]
            return {"Item": record}


    @dataclass
    class User:
        email: str
        role: str


    @event_processor.dependency_factory
    def boto_clients(client_name: str) -> FakeDynamoClient:
        if client_name == "dynamodb":
            return FakeDynamoClient()
        else:
            raise NotImplementedError()


    # Uses the dynamodb client specified in the processor decorator
    def event_to_user(event: Dict, dynamodb_client: FakeDynamoClient):
        email = event["user"]["email"]
        response = dynamodb_client.get_item(
                        TableName="users",
                        Key={"Email": {"S": email}}
                   )
        role = response["Item"]["Role"]["S"]

        return User(email=email, role=role)


    # Does not use the dynamodb client, but needs it for pre-processing
    @event_processor.processor(
        {"user.email": Any},
        pre_processor=event_to_user,
        boto_clients=("dynamodb",)
    )
    def my_processor(user: User):
        return user.role == "admin"


    print(
        event_processor.invoke({"user": {"email": "user@example.com"}}),
        event_processor.invoke({"user": {"email": "admin@example.com"}})
    )

.. testoutput::

    False True
