from typing import Optional, Union

__all__ = [
    "AuthorizationError",
    "MalformedRequest",
    "ContentTooLarge",
    "MethodNotAllowed",
    "InternalError",
    "UnexpectedError",
]

class FactoryAppException(Exception):
    """Basic Factory App exception."""

class UnexpectedError(Exception):
    """Internal Server Error."""

    def __init__(self):
        super().__init__("Unexpected Error")


class RequestError(Exception):
    """Request Error - basic class."""


class AuthorizationError(RequestError):
    """Unauthorized requests."""

    def __init__(self, msg: Optional[str] = None):
        super().__init__(
            f"The provided api key is invalid : {msg}."
            if msg
            else "Api key is missing."
        )


class MalformedRequest(RequestError):
    """Malformed Request Error."""

    def __init__(self, msg):
        super().__init__(msg)


class ContentTooLarge(RequestError):
    """Content too large Error."""

    def __init__(self, content_length: Union[float, int], max_content_length: int):
        super().__init__(
            f"The request is larger than the server is willing or able to process."
            f" Request length: {content_length}, but allowed is: {max_content_length}."
        )

class MethodNotAllowed(RequestError):
    """Method not allowed."""

    def __init__(self, method: str):
        super().__init__(f"Method: {method} not allowed.")

class InternalError(RequestError):
    """Validation Error"""

    def __init__(self):
        super().__init__(
            "The request was well-formed but server could not properly understand request."
        )