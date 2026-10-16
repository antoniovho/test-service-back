from uuid import uuid4

import pytest

from test_service.domain.model.exceptions.error_codes_enum import DomainError
from test_service.domain.model.exceptions.invalid_precondition_version_source_exception import (
    InvalidPreconditionVersionSourceException,
)
from test_service.domain.model.exceptions.invalid_test_case_version_source_exception import (
    InvalidTestCaseVersionSourceException,
)
from test_service.domain.model.exceptions.invalid_test_plan_version_source_exception import (
    InvalidTestPlanVersionSourceException,
)
from test_service.domain.model.exceptions.invalid_test_set_version_source_exception import (
    InvalidTestSetVersionSourceException,
)


@pytest.mark.parametrize(
    ("exception_type", "resource"),
    [
        (InvalidTestCaseVersionSourceException, "test case"),
        (InvalidPreconditionVersionSourceException, "precondition"),
        (InvalidTestSetVersionSourceException, "test set"),
        (InvalidTestPlanVersionSourceException, "test plan"),
    ],
)
def test_when_deprecated_source_is_used_to_create_a_version_expect_identified_error(
    exception_type, resource
):
    identifier = uuid4()

    error = exception_type(identifier)

    assert error.code == DomainError.INVALID_VERSION_SOURCE.code
    assert resource in error.error_description
    assert str(identifier) in error.error_description
