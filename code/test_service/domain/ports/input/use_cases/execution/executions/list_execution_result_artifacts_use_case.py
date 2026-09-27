"""Input port: list artifacts for a test result."""

from typing import Protocol

from test_service.domain.application.queries.execution import (
    ListExecutionResultArtifactsQuery,
)
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import TestResultArtifact
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListExecutionResultArtifactsUseCase(
    AsyncUseCase[ListExecutionResultArtifactsQuery, Page[TestResultArtifact]], Protocol
):
    """Input port for listing technical evidence attached to one test result."""
