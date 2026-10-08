"""Service-variable rendering shared by Tavern HTTP and SSE execution."""

import re
from collections.abc import Mapping

_SERVICE_VARIABLE = re.compile(r"\{\{([A-Za-z_]\w*)\}\}")


def render_service_variables(
    value: object, variables: Mapping[str, str], escape_braces: bool = False
) -> object:
    """Resolve service-owned placeholders while preserving Tavern variables.

    Args:
        value: Scalar or nested action configuration to render.
        variables: Service-owned values addressed as ``{{variableName}}``.
        escape_braces: Double every brace in substituted values so Tavern's own
            formatter treats them as literal text. Required whenever the result
            is handed to Tavern, because variable values can come from earlier
            responses and must never be evaluated as Tavern placeholders.

    Returns:
        A recursively rendered value. Undefined service variables and Tavern
        placeholders written as ``{variableName}`` remain unchanged. Mappings
        become ``dict`` and sequences become ``list``.
    """
    if isinstance(value, str):
        return _SERVICE_VARIABLE.sub(
            lambda match: _substitution(match, variables, escape_braces), value
        )
    if isinstance(value, list | tuple):
        return [render_service_variables(item, variables, escape_braces) for item in value]
    if isinstance(value, Mapping):
        return {
            key: render_service_variables(item, variables, escape_braces)
            for key, item in value.items()
        }
    return value


def _substitution(match: re.Match[str], variables: Mapping[str, str], escape_braces: bool) -> str:
    """Return the replacement text for one service placeholder."""
    if match.group(1) not in variables:
        return match.group(0)
    replacement = variables[match.group(1)]
    if escape_braces:
        return replacement.replace("{", "{{").replace("}", "}}")
    return replacement
