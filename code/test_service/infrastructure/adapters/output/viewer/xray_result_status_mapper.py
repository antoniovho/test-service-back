"""Translation from domain execution results to Xray Test Run statuses."""

from test_service.domain.model.execution.execution import ExecutionStatus, ResultStatus


class XrayResultStatusMapper:
    """Map domain result states to the Xray Test Run status vocabulary."""

    @staticmethod
    def to_test_run_status(result_status: ResultStatus, execution_status: ExecutionStatus) -> str:
        """Return the Xray status appropriate for one Test Run result."""
        if execution_status is ExecutionStatus.CANCELLED and result_status is ResultStatus.SKIPPED:
            return "TO DO"
        return {
            ResultStatus.PASSED: "PASSED",
            ResultStatus.FAILED: "FAILED",
            ResultStatus.ERROR: "FAILED",
            ResultStatus.BLOCKED: "TO DO",
            ResultStatus.SKIPPED: "TO DO",
        }[result_status]
