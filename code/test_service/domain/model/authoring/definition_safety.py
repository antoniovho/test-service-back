"""Runner-neutral safety rules for authored test definitions."""

import re
from collections.abc import Mapping
from string import Formatter

_EXECUTABLE_DIRECTIVE_KEYS = frozenset({"$ext"})
_DUNDER_SEGMENT = re.compile(r"(?:^|[.\[])__")


def find_unsafe_definition_construct(value: object) -> str | None:
    """Find a construct prohibited by the Test Service definition contract.

    These checks intentionally contain no knowledge of a particular runner.
    Runner adapters must enforce any additional rules imposed by their own
    template language or execution engine.
    """
    if isinstance(value, str):
        return _find_dunder_template_field(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _EXECUTABLE_DIRECTIVE_KEYS:
                return f"executable directive '{key}'"
            found = find_unsafe_definition_construct(key) or find_unsafe_definition_construct(item)
            if found:
                return found
        return None
    if isinstance(value, list | tuple):
        return next(
            (found for item in value if (found := find_unsafe_definition_construct(item))), None
        )
    return None


def _find_dunder_template_field(text: str) -> str | None:
    """Find a replacement field that traverses a dunder attribute or item."""
    try:
        fields = list(Formatter().parse(text))
    except ValueError:
        return None
    for _, name, format_spec, _ in fields:
        if name is not None and _DUNDER_SEGMENT.search(name) is not None:
            return f"template field '{name}'"
        if format_spec and (found := _find_dunder_template_field(format_spec)):
            return found
    return None
