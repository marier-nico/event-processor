import json
from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    status_code: int = Field(..., alias="statusCode")
    body: Any = ""
    headers: dict = {"content-type": "application/json"}

    @classmethod
    def bad_request(cls, error_info: dict) -> "ApiResponse":
        return cls(status_code=400, body=json.dumps(error_info))

    @classmethod
    def ok_text_response(cls, response: dict) -> "ApiResponse":
        return cls(status_code=200, body=json.dumps(response))

    @classmethod
    def server_error(cls, error_info: dict) -> "ApiResponse":
        return cls(status_code=500, body=json.dumps(error_info))
