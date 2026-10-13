"""Platform policy for constructs a runner would evaluate as code or privileged data.

Definitions are authored before any runner is chosen, so the domain rejects these
constructs up front. Runner adapters reuse the same policy at their boundary.
"""

import re
from collections.abc import Mapping
from string import Formatter

_EXECUTABLE_DIRECTIVE_KEYS = frozenset({"$ext"})
_RESERVED_TEMPLATE_ROOTS = frozenset({"tavern"})
_DUNDER_SEGMENT = re.compile(r"(?:^|[.\[])__")


def find_reserved_construct(value: object) -> str | None:
    """Find a construct a runner would evaluate as code or as privileged data.

    Args:
        value: Action configuration, or any value nested inside it.

    Returns:
        A short description of the first reserved construct found, or ``None``.
    """
    if isinstance(value, str):
        return _find_reserved_template_field(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _EXECUTABLE_DIRECTIVE_KEYS:
                return f"executable directive '{key}'"
            found = find_reserved_construct(key) or find_reserved_construct(item)
            if found:
                return found
        return None
    if isinstance(value, list | tuple):
        return next((found for item in value if (found := find_reserved_construct(item))), None)
    return None


def _find_reserved_template_field(text: str) -> str | None:
    """Find a replacement field that reaches the runner's reserved namespace."""
    try:
        fields = list(Formatter().parse(text))
    except ValueError:
        return None
    for _, name, format_spec, _ in fields:
        if name is not None and _is_reserved_field(name):
            return f"template field '{name}'"
        if format_spec:
            found = _find_reserved_template_field(format_spec)
            if found:
                return found
    return None


def _is_reserved_field(name: str) -> bool:
    """Report whether a replacement field names a reserved root or traverses a dunder."""
    root = re.split(r"[.\[]", name, maxsplit=1)[0]
    return root in _RESERVED_TEMPLATE_ROOTS or _DUNDER_SEGMENT.search(name) is not None
