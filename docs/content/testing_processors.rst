Testing Processors
==================

Thanks to the separation between registering and invoking processors, testing every component of the system is extremely
easy. Essentially, since the processor decorator does not modify the function it decorates, it's possible to test
processors the same way any other function would be tested.

Because of the dependency injection, it's also very easy to mock clients during testing.

Example
-------

Suppose that we have the following functions we want to test:

.. include:: shared/full_example.rst

We could write the following tests:

.. code-block:: python
    :caption: tests.py

    from unittest.mock import MagicMock, patch

    def test_my_processor_returns_true_for_admin_user():
        test_user = User(email="test@example.com", role="admin")

        result = my_processor(test_user)

        assert result is True

    def test_event_to_user_returns_user_data_from_dynamodb():
        dynamodb_client = MagicMock()
        dynamodb_client.get_item.return_value = {
            "Item": {
                "Role": {"S": "mock-value"}
            }
        }
        test_event = {"user": {"email": "test@example.com"}}

        result = event_to_user(test_event, dynamodb_client)

        assert result.role == "mock-value"
        dynamodb_client.get_item.assert_called_once()

    @patch("path.to.your.factory.boto3")
    def test_boto_clients_creates_boto_client(boto3_mock):
        test_client_name = "mock-value"

        result = boto_clients(test_client_name)

        assert result == boto3_mock.client.return_value
        boto3_mock.assert_called_once_with(test_client_name)

As you can see, the dependency injection makes the processor and pre-processor easy to test, and it makes those tests
clearer by avoiding excessive patching. Patching *is* needed to test the dependency factory, but since that's the only
thing to test, it doesn't make the test any less clear.
