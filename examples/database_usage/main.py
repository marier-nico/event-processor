from typing import Union

from pydantic import BaseModel, ValidationError

from event_processor import EventProcessor, Depends
from event_processor.filters import Accept, Eq
from examples.database_usage.database import get_session, FakeDatabase
from examples.database_usage.models import (
    UserRegistrationRequest,
    UserRegistrationResponse,
    UserLoginRequest,
    UserLoginResponse,
    ErrorResponse,
)
from examples.database_usage.passwords import hash_password, verify_password

event_processor = EventProcessor()


@event_processor.processor(Accept(), rank=-1)
def default_processor() -> ErrorResponse:
    return ErrorResponse(message="Unknown action!")


@event_processor.processor(Eq("action", "register"))
def handle_registration(
    request: UserRegistrationRequest, db: FakeDatabase = Depends(get_session)
) -> UserRegistrationResponse:
    # The schema is : (email, role, password hash)
    db.insert("users", (request.email, "user", hash_password(request.password)))
    return UserRegistrationResponse(email=request.email, role="user")


@event_processor.processor(Eq("action", "login"))
def handle_login(
    request: UserLoginRequest, db: FakeDatabase = Depends(get_session)
) -> Union[UserLoginResponse, ErrorResponse]:
    result = db.query("users", request.email)
    if result is None:
        return ErrorResponse(message="Invalid username or password")

    email, role, password_hash = result
    if verify_password(password=request.password, hashed_password=password_hash):
        return UserLoginResponse(token="authenticated", role=role)
    else:
        return ErrorResponse(message="Invalid username or password")


def handle_event(event: dict) -> str:
    try:
        result = event_processor.invoke(event)
    except ValidationError as err:
        result = err.json()

    if hasattr(result, "__class__") and issubclass(result.__class__, BaseModel):
        return result.json()
    return str(result)


def main():
    unknown_result = handle_event({"action": "unhandled"})
    register_result = handle_event({"action": "register", "email": "test@example.com", "password": "Abcdefgh12345"})
    register_failed = handle_event({"action": "register", "email": "test@example.com", "password": "asdf"})
    login_result = handle_event({"action": "login", "email": "test@example.com", "password": "Abcdefgh12345"})
    login_failed_1 = handle_event({"action": "login", "email": "unknown@example.com", "password": "Abcdefgh12345"})
    login_failed_2 = handle_event({"action": "login", "email": "test@example.com", "password": "bad-password"})

    assert "Unknown action!" in unknown_result
    assert "test@example.com" in register_result
    assert "user" in register_result
    assert "password should be at least 8 characters" in register_failed
    assert "authenticated" in login_result
    assert "user" in login_result
    assert "Invalid username or password" in login_failed_1
    assert "Invalid username or password" in login_failed_2

    print("database_usage PASSED")
