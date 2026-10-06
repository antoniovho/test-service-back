"""Service-variable rendering shared by Tavern HTTP and SSE execution."""

import re
from collections.abc import Mapping

_SERVICE_VARIABLE = re.compile(r"\{\{([A-Za-z_]\w*)\}\}")


def render_service_variables(value: object, variables: Mapping[str, str]) -> object:
    """Resolve service-owned placeholders while preserving Tavern variables.

    Args:
        value: Scalar or nested action configuration to render.
        variables: Service-owned values addressed as ``{{variableName}}``.

    Returns:
        A recursively rendered value. Undefined service variables and Tavern
        placeholders written as ``{variableName}`` remain unchanged.
    """
    if isinstance(value, str):
        return _SERVICE_VARIABLE.sub(
            lambda match: variables.get(match.group(1), match.group(0)), value
        )
    if isinstance(value, list):
        return [render_service_variables(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: render_service_variables(item, variables) for key, item in value.items()}
    return value
