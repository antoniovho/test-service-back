from unittest.mock import Mock

import pytest
from tavern._core.extfunctions import get_wrapped_response_function

from test_service.infrastructure.adapters.output.runners.tavern.json_schema_validator import (
    validate_json_schema,
    validate_response_contains_text,
    validate_response_excludes_text,
    validate_response_header_names,
    validate_response_text,
)


class TestValidateJsonSchema:
    def test_when_loaded_by_tavern_expect_schema_validator_is_resolvable(self) -> None:
        response = Mock()
        response.json.return_value = {"id": "order-123"}
        validator = get_wrapped_response_function(
            {
                "function": (
                    "test_service.infrastructure.adapters.output.runners.tavern."
                    "json_schema_validator:validate_json_schema"
                ),
                "extra_kwargs": {"schema": {"type": "object", "required": ["id"]}},
            }
        )

        result = validator(response)

        assert result is None

    def test_when_response_matches_schema_expect_validation_succeeds(self) -> None:
        response = Mock()
        response.json.return_value = {"id": "order-123"}
        schema = {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}

        result = validate_json_schema(response, schema)

        assert result is None

    def test_when_response_does_not_match_schema_expect_safe_assertion(self) -> None:
        response = Mock()
        response.json.return_value = {"id": "sensitive-value"}
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}

        with pytest.raises(AssertionError, match=r"schema mismatch at \$\['id'\]") as error:
            validate_json_schema(response, schema)

        assert "sensitive-value" not in str(error.value)

    def test_when_nested_response_does_not_match_schema_expect_full_path(self) -> None:
        response = Mock()
        response.json.return_value = {"orders": [{"id": "sensitive-value"}]}
        schema = {
            "type": "object",
            "properties": {
                "orders": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}},
                    },
                }
            },
        }

        with pytest.raises(
            AssertionError, match=r"schema mismatch at \$\['orders'\]\[0\]\['id'\]"
        ) as error:
            validate_json_schema(response, schema)

        assert "sensitive-value" not in str(error.value)

    def test_when_response_body_is_not_json_expect_safe_assertion(self) -> None:
        response = Mock()
        response.json.side_effect = ValueError("sensitive response body")

        with pytest.raises(AssertionError, match="response body is not valid JSON") as error:
            validate_json_schema(response, {"type": "object"})

        assert "sensitive response body" not in str(error.value)

    def test_when_response_text_matches_expect_validation_succeeds(self) -> None:
        response = Mock(text="I'm alive!")

        result = validate_response_text(response, "I'm alive!")

        assert result is None

    def test_when_response_text_differs_expect_safe_assertion(self) -> None:
        response = Mock(text="sensitive response value")

        with pytest.raises(AssertionError, match="text did not match") as error:
            validate_response_text(response, "I'm alive!")

        assert "sensitive response value" not in str(error.value)

    def test_when_expected_response_header_is_present_expect_validation_succeeds(self) -> None:
        response = Mock(headers={"X-LiteLLM-Call-ID": "call-123"})

        result = validate_response_header_names(response, ["x-litellm-call-id"])

        assert result is None

    def test_when_expected_response_header_is_missing_expect_assertion(self) -> None:
        response = Mock(headers={"Content-Type": "application/json"})

        with pytest.raises(AssertionError, match="x-litellm-call-id"):
            validate_response_header_names(response, ["x-litellm-call-id"])

    def test_when_expected_response_header_is_empty_expect_assertion(self) -> None:
        response = Mock(headers={"X-LiteLLM-Call-ID": "  "})

        with pytest.raises(AssertionError, match="x-litellm-call-id"):
            validate_response_header_names(response, ["x-litellm-call-id"])


class TestValidateResponseExcludesText:
    def test_when_response_excludes_forbidden_values_expect_validation_succeeds(self) -> None:
        response = Mock(text='{"error":"invalid credential"}')

        result = validate_response_excludes_text(response, ["secret-key", "Traceback"])

        assert result is None

    def test_when_response_contains_forbidden_value_expect_safe_assertion(self) -> None:
        response = Mock(text='{"error":"credential secret-key rejected"}')

        with pytest.raises(AssertionError, match="contains forbidden sensitive text") as error:
            validate_response_excludes_text(response, ["secret-key"])

        assert "secret-key" not in str(error.value)

    def test_when_forbidden_values_are_empty_expect_assertion(self) -> None:
        response = Mock(text="safe response")

        with pytest.raises(AssertionError, match="requires non-empty string values"):
            validate_response_excludes_text(response, [])

    @pytest.mark.parametrize(
        "forbidden_values",
        [[""], ["secret-key", 7]],
        ids=["empty-value", "non-string-value"],
    )
    def test_when_forbidden_values_are_invalid_expect_assertion(self, forbidden_values) -> None:
        response = Mock(text="safe response")

        with pytest.raises(AssertionError, match="requires non-empty string values"):
            validate_response_excludes_text(response, forbidden_values)


class TestValidateResponseContainsText:
    def test_when_response_contains_single_expected_marker_expect_validation_succeeds(self) -> None:
        response = Mock(text="request accepted")

        result = validate_response_contains_text(response, "accepted")

        assert result is None

    def test_when_response_contains_expected_marker_expect_validation_succeeds(self) -> None:
        response = Mock(
            text='{"correlation_id":"security-test-42","label":"requested_model="gpt-test""}'
        )

        result = validate_response_contains_text(
            response, ["security-test-42", 'requested_model="gpt-test"']
        )

        assert result is None

    def test_when_response_omits_expected_marker_expect_safe_assertion(self) -> None:
        response = Mock(text="sensitive sink response")

        with pytest.raises(AssertionError, match="did not contain expected value") as error:
            validate_response_contains_text(response, ["security-test-42", "missing-label"])

        assert "sensitive sink response" not in str(error.value)
        assert "security-test-42" not in str(error.value)

    @pytest.mark.parametrize(
        "expected_values",
        [[], [""], ["expected-marker", 7]],
        ids=["empty-list", "empty-value", "non-string-value"],
    )
    def test_when_expected_values_are_invalid_expect_assertion(self, expected_values) -> None:
        response = Mock(text="safe response")

        with pytest.raises(AssertionError, match="requires non-empty string values"):
            validate_response_contains_text(response, expected_values)
