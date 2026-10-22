import pytest

from test_service.domain.model.execution.execution import ExecutionStatus, ResultStatus
from test_service.infrastructure.adapters.output.viewer.xray_result_status_mapper import (
    XrayResultStatusMapper,
)


class TestXrayResultStatusMapper:
    @pytest.mark.parametrize(
        ("execution_status", "result_status", "expected_xray_status"),
        [
            (ExecutionStatus.PASSED, ResultStatus.PASSED, "PASS"),
            (ExecutionStatus.FAILED, ResultStatus.FAILED, "FAIL"),
            (ExecutionStatus.ERROR, ResultStatus.ERROR, "FAIL"),
            (ExecutionStatus.PARTIALLY_FAILED, ResultStatus.BLOCKED, "ABORTED"),
            (ExecutionStatus.FAILED, ResultStatus.SKIPPED, "TODO"),
            (ExecutionStatus.CANCELLED, ResultStatus.SKIPPED, "ABORTED"),
        ],
        ids=["passed", "failed", "error", "blocked", "skipped", "cancelled_skipped"],
    )
    def test_when_mapping_result_status_expect_xray_test_run_status(
        self,
        execution_status: ExecutionStatus,
        result_status: ResultStatus,
        expected_xray_status: str,
    ) -> None:
        result = XrayResultStatusMapper.to_test_run_status(result_status, execution_status)

        assert result == expected_xray_status
