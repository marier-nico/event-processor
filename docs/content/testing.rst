Testing Processors
------------------

Thanks to the separation between the definition and invocation of processors, it's really easy to test processors. Since
the processor decorator returns the function as-is (and does not modify it), it's possible to test your processor the
same way you would test any other function. Dependencies also make it easy to use mocks for your external service
dependencies.

Here's an example of how you might test a processor :

.. testcode::

    from event_processor import EventProcessor, Event, Depends
    from event_processor.filters import Exists

    processor = EventProcessor()


    class FakeDatabase:
        values = {
            "users": [
                {"email": "admin@example.com", "role": "admin"},
                {"email": "user@example.com", "role": "user"},
            ]
        }

        def get_role_by_email(self, email: str) -> str:
            user = [user for user in self.values["users"] if user["email"] == email][0]
            return user["role"]


    database_instance = None
    def get_database() -> FakeDatabase:
        global database_instance
        if database_instance is None:
            database_instance = FakeDatabase()
        return database_instance


    def extract_email(event: Event):
        return event["email"]


    @processor(Exists("email"))
    def user_is_admin(
        email: str = Depends(extract_email, cache=False),
        db_client: FakeDatabase = Depends(get_database),
    ):
        user_role = db_client.get_role_by_email(email)
        return user_role == "admin"


    print(processor.invoke({"email": "user@example.com"}).returned_value)
    print(processor.invoke({"email": "admin@example.com"}).returned_value)


    #################### Tests #####################
    from unittest.mock import Mock


    def test_user_is_admin_returns_true_for_admin_user():
        mock_db = Mock()
        mock_db.get_role_by_email.return_value = "admin"

        result = user_is_admin("someone@example.com", mock_db)

        assert result is True


    def test_user_is_admin_returns_false_for_non_admin_user():
        mock_db = Mock()
        mock_db.get_role_by_email.return_value = "user"

        result = user_is_admin("someone@example.com", mock_db)

        assert result is False


    test_user_is_admin_returns_true_for_admin_user()
    test_user_is_admin_returns_false_for_non_admin_user()


.. testoutput::

    False
    True
