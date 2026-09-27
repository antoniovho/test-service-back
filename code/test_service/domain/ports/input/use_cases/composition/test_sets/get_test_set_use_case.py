"""Input port: get test set."""

from typing import Protocol

from test_service.domain.application.queries.composition import TestSetQuery
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_case import AsyncUseCase


class GetTestSetUseCase(AsyncUseCase[TestSetQuery, TestSet], Protocol):
    """Input port for retrieving one TestSet snapshot by UUID."""
