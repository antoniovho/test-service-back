from test_service.domain.model.exceptions.domain_exception import DomainException
from test_service.domain.model.exceptions.error_origin_enum import ErrorOrigin
from test_service.domain.model.exceptions.permanent_viewer_result_publication_exception import (
    PermanentViewerResultPublicationError,
)
from test_service.domain.model.exceptions.retryable_viewer_result_publication_exception import (
    RetryableViewerResultPublicationError,
)


class TestViewerResultPublicationExceptions:
    def test_when_retryable_publication_error_expect_internal_retryable_metadata(self) -> None:
        error = RetryableViewerResultPublicationError("The viewer is not ready.")

        assert error.code == "VIEWER_RESULT_PUBLICATION_RETRYABLE"
        assert error.origin is ErrorOrigin.INTERNAL
        assert str(error) == "The viewer is not ready."
        assert isinstance(error, DomainException)

    def test_when_permanent_publication_error_has_provider_expect_provider_metadata(self) -> None:
        error = PermanentViewerResultPublicationError(
            "The provider rejected the result.",
            origin=ErrorOrigin.PROVIDER,
            provider_name="Xray",
        )

        assert error.code == "VIEWER_RESULT_PUBLICATION_PERMANENT"
        assert error.origin is ErrorOrigin.PROVIDER
        assert error.provider_name == "Xray"
        assert isinstance(error, DomainException)
