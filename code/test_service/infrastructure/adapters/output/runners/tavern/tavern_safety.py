"""Safety rules specific to Tavern's template language and execution engine."""

import re
from collections.abc import Mapping
from string import Formatter

from test_service.domain.model.authoring.definition_safety import (
    find_unsafe_definition_construct,
)

_TAVERN_TEMPLATE_ROOT = "tavern"


def find_unsafe_tavern_construct(value: object) -> str | None:
    """Find a construct unsafe for documents passed to Tavern.

    The shared definition policy runs first; this adapter then rejects Tavern's
    privileged ``tavern`` template namespace.
    """
    unsafe = find_unsafe_definition_construct(value)
    if unsafe is not None:
        return unsafe
    return _find_tavern_template_field(value)


def _find_tavern_template_field(value: object) -> str | None:
    """Find Tavern's privileged template root in nested values."""
    if isinstance(value, str):
        return _find_tavern_field_in_text(value)
    if isinstance(value, Mapping):
        return _find_tavern_field_in_mapping(value)
    if isinstance(value, list | tuple):
        return _find_tavern_field_in_sequence(value)
    return None


def _find_tavern_field_in_text(text: str) -> str | None:
    """Find Tavern's reserved root in a format string and its format specs."""
    try:
        fields = Formatter().parse(text)
        return next(
            (
                found
                for _, name, format_spec, _ in fields
                if (found := _find_tavern_field_in_format_parts(name, format_spec))
            ),
            None,
        )
    except ValueError:
        return None


def _find_tavern_field_in_format_parts(name: str | None, format_spec: str | None) -> str | None:
    """Inspect one parsed format field and its nested format specification."""
    if name is not None and _template_root(name) == _TAVERN_TEMPLATE_ROOT:
        return f"template field '{name}'"
    return _find_tavern_template_field(format_spec) if format_spec else None


def _find_tavern_field_in_mapping(value: Mapping[object, object]) -> str | None:
    """Inspect mapping keys and values in insertion order."""
    return next(
        (
            found
            for key, item in value.items()
            if (found := _find_tavern_template_field(key) or _find_tavern_template_field(item))
        ),
        None,
    )


def _find_tavern_field_in_sequence(value: list[object] | tuple[object, ...]) -> str | None:
    """Inspect sequence members in order."""
    return next((found for item in value if (found := _find_tavern_template_field(item))), None)


def _template_root(name: str) -> str:
    """Return the root name addressed by a Tavern format field."""
    return re.split(r"[.\[]", name, maxsplit=1)[0]
