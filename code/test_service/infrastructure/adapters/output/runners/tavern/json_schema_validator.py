"""Tavern response assertion for corpus JSON Schema expectations."""

from collections.abc import Mapping, Sequence
from typing import Any

from jsonschema import Draft202012Validator, ValidationError


def validate_json_schema(response: Any, schema: Mapping[str, Any]) -> None:
    """Validate a Tavern HTTP response body without exposing its values on failure."""
    try:
        body = response.json()
    except ValueError:
        raise AssertionError("HTTP response body is not valid JSON") from None

    try:
        Draft202012Validator(schema).validate(body)
    except ValidationError as error:
        path = "$" + "".join(f"[{part!r}]" for part in error.absolute_path)
        raise AssertionError(
            f"HTTP response JSON schema mismatch at {path} ({error.validator})"
        ) from None


def validate_response_text(response: Any, expected_text: str) -> None:
    """Assert exact response text without exposing its value on failure."""
    if response.text != expected_text:
        raise AssertionError("HTTP response text did not match expected value")


def validate_response_contains_text(response: Any, expected_texts: str | Sequence[str]) -> None:
    """Assert response text contains every marker without exposing them on failure."""
    markers = [expected_texts] if isinstance(expected_texts, str) else expected_texts
    if not markers or any(not isinstance(value, str) or not value for value in markers):
        raise AssertionError("expected text assertion requires non-empty string values")
    if any(value not in response.text for value in markers):
        raise AssertionError("HTTP response text did not contain expected value")


def validate_response_excludes_text(response: Any, forbidden_texts: Sequence[str]) -> None:
    """Assert response text excludes sensitive values without echoing them on failure."""
    if not forbidden_texts or any(
        not isinstance(value, str) or not value for value in forbidden_texts
    ):
        raise AssertionError("forbidden text assertion requires non-empty string values")
    if any(value in response.text for value in forbidden_texts):
        raise AssertionError("HTTP response contains forbidden sensitive text")


def validate_response_header_names(response: Any, expected_header_names: Sequence[str]) -> None:
    """Assert expected HTTP headers have non-empty values, ignoring name casing."""
    actual_headers = {name.lower(): value for name, value in response.headers.items()}
    missing_names = [
        name
        for name in expected_header_names
        if not str(actual_headers.get(name.lower(), "")).strip()
    ]
    if missing_names:
        raise AssertionError(
            "HTTP response is missing expected header name(s): " + ", ".join(missing_names)
        )
