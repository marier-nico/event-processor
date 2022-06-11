import json

from pydantic import ValidationError

from event_processor import EventProcessor, ErrorHandlingStrategies, InvocationStrategies
from examples.lambda_api.api_response import ApiResponse

processor = EventProcessor(
    invocation_strategy=InvocationStrategies.FIRST_MATCH,
    error_handling_strategy=ErrorHandlingStrategies.CAPTURE,
)


def lambda_handler(event, _context):
    request_context = event["requestContext"]

    method = request_context["http"]["method"]
    route = request_context["http"]["path"][len(f"/{request_context['stage']}"):]  # ignore the stage from the path

    query_string = event.get("queryStringParameters", {})
    body_parameters = json.loads(event.get("body", json.dumps({})))

    full_event = {
        "method": method,
        "route": route,
        **query_string,
        **body_parameters,
    }

    try:
        result = processor.invoke(full_event)
    except ValidationError as validation_error:
        return ApiResponse.bad_request({"errors": validation_error.errors()}).dict(by_alias=True)

    if result.has_exception():
        return ApiResponse.server_error({"error": str(result.raised_exception)}).dict(by_alias=True)

    return result.returned_value.dict(by_alias=True)  # This requires that all processors return an `ApiResponse`
