"""Strict Pydantic DTOs for the first-load corpus format."""

import re
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from test_service.domain.model.authoring.test_case import Priority, TestLevel, TestType

_SENSITIVE_HEADER_NAMES = frozenset({"authorization", "cookie", "proxy-authorization", "x-api-key"})
_IDENTIFIER_PATTERN = r"^[A-Za-z][A-Za-z0-9_-]{0,99}$"
_SECRET_REFERENCE_PATTERN = re.compile(
    r"^(?:[A-Za-z][A-Za-z0-9_-]*\s+)?(?:\{\{[A-Za-z_]\w*\}\}|\{[A-Za-z_]\w*\})$"
)


class _CorpusModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class HttpConfiguration(_CorpusModel):
    url: str = Field(min_length=1, max_length=4096)
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"] = "GET"
    headers: dict[str, str] | None = None
    params: dict[str, Any] | None = None
    query: dict[str, Any] | None = None
    json_body: Any = Field(default=None, alias="json")
    expected_status: int | None = Field(default=None, alias="expectedStatus", ge=100, le=599)
    expected_json: Any = Field(default=None, alias="expectedJson")
    expected_text: str | None = Field(default=None, alias="expectedText", max_length=16384)
    expected_text_contains: str | list[str] | None = Field(
        default=None, alias="expectedTextContains"
    )
    forbidden_text: list[str] | None = Field(
        default=None, alias="forbiddenText", min_length=1, max_length=50
    )
    expected_headers: dict[str, str] | None = Field(default=None, alias="expectedHeaders")
    expected_header_names: list[str] | None = Field(
        default=None, alias="expectedHeaderNames", max_length=50
    )
    expected_json_schema: dict[str, Any] | None = Field(default=None, alias="expectedJsonSchema")
    max_response_time_ms: int | None = Field(default=None, alias="maxResponseTimeMs", ge=1)
    capture: dict[str, str] | None = None


class SseConfiguration(_CorpusModel):
    url: str = Field(min_length=1, max_length=4096)
    method: Literal["GET", "POST"] = "GET"
    headers: dict[str, str] | None = None
    params: dict[str, Any] | None = None
    query: dict[str, Any] | None = None
    json_body: Any = Field(default=None, alias="json")
    expected_event: str | None = Field(default=None, alias="expectedEvent", min_length=1)
    expected_data: str | None = Field(default=None, alias="expectedData")
    expected_data_json_schema: dict[str, Any] | None = Field(
        default=None, alias="expectedDataJsonSchema"
    )
    expected_final_data_json_schema: dict[str, Any] | None = Field(
        default=None, alias="expectedFinalDataJsonSchema"
    )
    expected_concatenated_content: str | None = Field(
        default=None, alias="expectedConcatenatedContent", max_length=16384
    )
    expected_content_type: str | None = Field(
        default=None, alias="expectedContentType", min_length=1, max_length=200
    )
    validate_usage_totals: bool | None = Field(default=None, alias="validateUsageTotals")
    expected_done: bool | None = Field(default=None, alias="expectedDone")
    max_events: int | None = Field(default=None, alias="maxEvents", ge=1)
    receive_timeout_seconds: float | None = Field(default=None, alias="receiveTimeoutSeconds", gt=0)
    max_response_time_ms: int | None = Field(default=None, alias="maxResponseTimeMs", ge=1)


class CorpusAction(_CorpusModel):
    identifier: str = Field(alias="id", pattern=_IDENTIFIER_PATTERN)
    action_type: Literal["HTTP", "SSE"] = Field(alias="type")
    configuration: dict[str, Any]

    @model_validator(mode="after")
    def validate_configuration(self) -> "CorpusAction":
        model_type = HttpConfiguration if self.action_type == "HTTP" else SseConfiguration
        self.configuration = model_type.model_validate(self.configuration).model_dump(
            by_alias=True, exclude_none=True
        )
        _validate_sensitive_headers(self.configuration)
        return self


class CorpusDefinition(_CorpusModel):
    schema_version: Literal["1.1"] = Field(alias="schemaVersion")
    variables: dict[str, str] = Field(default_factory=dict)
    actions: list[CorpusAction] = Field(min_length=1)


class CorpusMetadata(_CorpusModel):
    objective: str | None = Field(default=None, max_length=4000)
    labels: list[str] = Field(default_factory=list)
    source: str | None = Field(default=None, max_length=200)


class TestCaseCorpusDocument(_CorpusModel):
    kind: Literal["test-case"]
    schema_version: Literal["1.1.0"] = Field(alias="schemaVersion")
    test_case_key: str = Field(alias="testCaseKey", pattern=_IDENTIFIER_PATTERN)
    summary: str = Field(min_length=1, max_length=500)
    precondition_keys: list[str] = Field(default_factory=list, alias="preconditionKeys")
    definition: CorpusDefinition
    metadata: CorpusMetadata = Field(default_factory=CorpusMetadata)
    test_type: TestType = Field(default=TestType.AUTOMATED, alias="testType")
    test_level: TestLevel = Field(default=TestLevel.INTEGRATION, alias="testLevel")
    priority: Priority = Priority.MEDIUM
    timeout_seconds: int = Field(default=60, alias="timeoutSeconds", ge=1, le=3600)


class PreconditionCorpusDocument(_CorpusModel):
    kind: Literal["precondition"]
    schema_version: Literal["1.1.0"] = Field(alias="schemaVersion")
    precondition_key: str = Field(alias="preconditionKey", pattern=_IDENTIFIER_PATTERN)
    summary: str = Field(min_length=1, max_length=500)
    validation_definition: CorpusDefinition = Field(alias="validationDefinition")
    metadata: CorpusMetadata = Field(default_factory=CorpusMetadata)


CorpusDocument = TestCaseCorpusDocument | PreconditionCorpusDocument


def _validate_sensitive_headers(configuration: Mapping[str, object]) -> None:
    headers = configuration.get("headers")
    if not isinstance(headers, Mapping):
        return
    for name, value in headers.items():
        if name.lower() in _SENSITIVE_HEADER_NAMES and (
            not isinstance(value, str) or _SECRET_REFERENCE_PATTERN.fullmatch(value) is None
        ):
            raise ValueError(
                f"sensitive header '{name}' must use a service or captured variable reference"
            )
