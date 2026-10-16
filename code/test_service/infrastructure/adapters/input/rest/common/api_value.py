"""Conversions from generated API transport values to primitives."""

from enum import Enum


def enum_value(value: str | Enum | None) -> str | None:
    """Return the primitive value carried by a generated string enum."""
    return value.value if isinstance(value, Enum) else value
