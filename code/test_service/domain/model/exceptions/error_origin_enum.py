"""Origin classification for domain exceptions."""

from enum import StrEnum


class ErrorOrigin(StrEnum):
    """Classification of what triggered a domain exception.

    Attributes:
        USER: Caused by a caller's input or requested action.
        INTERNAL: Caused by an internal invariant or state inconsistency.
        PROVIDER: Caused by data reported by an external provider (e.g. the Runner).
    """

    USER = "USER"
    INTERNAL = "INTERNAL"
    PROVIDER = "PROVIDER"
