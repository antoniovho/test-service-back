"""Service-variable rendering shared by Tavern HTTP and SSE execution."""

import re
from collections.abc import Mapping

_SERVICE_VARIABLE = re.compile(r"\{\{([A-Za-z_]\w*)\}\}")
_TAVERN_VARIABLE = re.compile(r"\{[A-Za-z_]\w*\}")


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


def escape_tavern_literal_braces(value: object) -> object:
    """Escape literal braces for Tavern while retaining its simple saved-variable syntax.

    Tavern applies Python ``str.format`` recursively to each string in its test
    document. JSON examples and regular-expression quantifiers therefore need
    escaping, whereas a saved-variable reference such as ``{response_id}``
    must remain format-able by Tavern in a later stage.
    """
    if isinstance(value, str):
        return _escape_tavern_literal_braces(value)
    if isinstance(value, list | tuple):
        return [escape_tavern_literal_braces(item) for item in value]
    if isinstance(value, Mapping):
        return {key: escape_tavern_literal_braces(item) for key, item in value.items()}
    return value


def _escape_tavern_literal_braces(value: str) -> str:
    """Double braces except recognised ``{saved_variable}`` expressions."""
    escaped: list[str] = []
    index = 0
    while index < len(value):
        character = value[index]
        if character == "{" and index + 1 < len(value) and value[index + 1] == "{":
            escaped.append("{{")
            index += 2
            continue
        if character == "}" and index + 1 < len(value) and value[index + 1] == "}":
            escaped.append("}}")
            index += 2
            continue
        if character == "{":
            variable = _TAVERN_VARIABLE.match(value, index)
            if variable is not None:
                escaped.append(variable.group(0))
                index = variable.end()
                continue
            escaped.append("{{")
        elif character == "}":
            escaped.append("}}")
        else:
            escaped.append(character)
        index += 1
    return "".join(escaped)
