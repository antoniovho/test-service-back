from test_service.infrastructure.adapters.output.runners.tavern.executors.tavern_executor import (
    _reporter_source,
)


class _Response:
    def __init__(self) -> None:
        self.status_code = 200
        self.headers = {
            "Authorization": "Bearer response-secret",
            "Set-Cookie": "session=response-secret",
            "X-Trace": "trace-value",
        }
        self.text = "response-body"

    def json(self) -> dict[str, str]:
        return {"token": "response-secret"}


class TestTavernExecutor:
    def test_when_request_fails_before_response_expect_credentials_redacted(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        namespace["pytest_tavern_beta_before_every_request"](
            {
                "method": "POST",
                "url": "https://api.example.test/accounts",
                "headers": {
                    "Authorization": "Bearer request-secret",
                    "X-Api-Key": "request-secret",
                    "X-Trace": "trace-value",
                },
                "json": {"password": "request-secret"},
            }
        )
        namespace["complete"]("FAILED")

        stage = namespace["result"]["stages"][0]
        request = stage["actual"]["request"]
        serialized = str(stage)

        assert request == {
            "method": "POST",
            "url": "https://api.example.test/accounts",
            "headers": {
                "Authorization": "[REDACTED]",
                "X-Api-Key": "[REDACTED]",
                "X-Trace": "trace-value",
            },
        }
        assert "request-secret" not in serialized

    def test_when_reporter_records_response_expect_sensitive_evidence_redacted(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        namespace["pytest_tavern_beta_before_every_request"]({})
        namespace["pytest_tavern_beta_after_every_response"]({}, _Response())
        namespace["complete"]("PASSED")

        stage = namespace["result"]["stages"][0]
        response = stage["actual"]
        serialized = str(stage)

        assert response["headers"]["Authorization"] == "[REDACTED]"
        assert response["headers"]["Set-Cookie"] == "[REDACTED]"
        assert response["body"] == {"token": "[REDACTED]"}
        assert "response-secret" not in serialized

    def test_when_response_body_exceeds_limit_expect_truncated_evidence(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        evidence = namespace["response_body_evidence"]("x" * 4097)

        assert evidence == {"truncated": True, "content": '"' + "x" * 4095}
