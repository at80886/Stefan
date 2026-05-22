"""Application-wide exception types."""

from __future__ import annotations


class StefanAppError(Exception):
    """Error type that can be logged, shown to the user, and recovered from."""

    def __init__(self, message: str, *, user_message: str | None = None, recoverable: bool = True) -> None:
        super().__init__(message)
        self.user_message = user_message or message
        self.recoverable = recoverable
