import string

from pydantic import BaseModel, validator


class UserRegistrationRequest(BaseModel):
    email: str
    password: str

    @validator("password")
    def check_password(cls, password: str):
        if len(password) < 8:
            raise ValueError("password should be at least 8 characters")
        if not any(c in string.ascii_lowercase for c in password):
            raise ValueError("password should contain at least one lowercase letter")
        if not any(c in string.ascii_uppercase for c in password):
            raise ValueError("password should contain at least one uppercase letter")
        if not any(c in string.digits for c in password):
            raise ValueError("password should contain at least one digit")

        return password


class UserRegistrationResponse(BaseModel):
    email: str
    role: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserLoginResponse(BaseModel):
    token: str
    role: str


class ErrorResponse(BaseModel):
    message: str
