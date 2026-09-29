"""Request-scoped caller identity, populated by IdentityMiddleware."""

from contextvars import ContextVar

_ANONYMOUS = "anonymous"

_current_identity: ContextVar[str] = ContextVar("current_identity", default=_ANONYMOUS)


def get_current_identity() -> str:
    """Return the identity of the current request's caller."""
    return _current_identity.get()


def set_current_identity(identity: str | None) -> None:
    """Set the identity of the current request's caller."""
    _current_identity.set(identity or _ANONYMOUS)
