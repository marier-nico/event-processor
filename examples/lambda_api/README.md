# Lambda API Example

This example shows how you might use the library to create an API on AWS Lambda.

The key is to inject some request information from the Lambda event into your event-processor invocation so that you can
do schema validation on the entire payload and access anything in the request context.
