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
            ResultStatus.BLOCKED: "BLOCKED",
            ResultStatus.SKIPPED: "TO DO",
        }[result_status]

    @staticmethod
    def to_test_run_step_status(result_status: ResultStatus) -> str:
        """Return the Xray status appropriate for one Test Run step."""
        return {
            ResultStatus.PASSED: "PASSED",
            ResultStatus.FAILED: "FAILED",
            ResultStatus.ERROR: "FAILED",
            ResultStatus.BLOCKED: "TODO",
            ResultStatus.SKIPPED: "TODO",
        }[result_status]
