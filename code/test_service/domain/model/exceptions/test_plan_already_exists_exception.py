"""Raised when creating an existing logical Test Plan key."""

from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin


class TestPlanAlreadyExistsException(DomainException):
    """Raised when a Test Plan key already has an immutable version."""

    def __init__(self, project_key: str, plan_key: str) -> None:
        super().__init__(
            error_description=(
                f"Test plan with key '{plan_key}' already exists in project '{project_key}'. "
                f"Use POST /v1/projects/{project_key}/test-plans/{{testPlanId}}/versions "
                "to create a new version."
            ),
            error=DomainError.TEST_PLAN_ALREADY_EXISTS,
            origin=ErrorOrigin.USER,
        )
