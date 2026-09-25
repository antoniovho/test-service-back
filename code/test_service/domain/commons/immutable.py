"""Helpers to defensively freeze mutable inputs held by frozen dataclasses."""

from collections.abc import Mapping
from types import MappingProxyType

Freezable = Mapping[str, object]


def freeze_mapping(value: Freezable | None) -> Freezable | None:
    """Return a read-only, defensively-copied view of a mapping.

    Args:
        value: Mapping supplied by a caller, possibly mutable and possibly ``None``.

    Returns:
        An immutable ``MappingProxyType`` copy of ``value``, or ``None`` when ``value`` is ``None``.
    """
    if value is None:
        return None
    return MappingProxyType(dict(value))
