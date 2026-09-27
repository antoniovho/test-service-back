"""Generic inbound use-case contract."""

from typing import Protocol


class AsyncUseCase[Request, Response](Protocol):
    """One application operation exposed to an inbound adapter.

    Type parameters:
        Request: Command or query accepted by the use case.
        Response: Domain model or page returned by the use case.
    """

    async def execute(self, request: Request) -> Response:
        """Execute one application command or query.

        Args:
            request: Typed application command or query.

        Returns:
            The domain response associated with the operation.

        Raises:
            DomainException: If the request violates a domain rule or targets a missing entity.
        """
        ...
