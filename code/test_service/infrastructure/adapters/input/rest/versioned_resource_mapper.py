"""Shared REST mappings for versioned resources."""

from collections.abc import Callable
from typing import Any

from test_service_server.models.pagination import Pagination as ApiPagination

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.lifecycle import VersionStatus


class VersionedResourceMapper:
    """Convert pagination, status, and page responses for versioned resources."""

    @staticmethod
    def to_pagination(
        offset: int | None, limit: int | None, sort_by: str | None, order: Any
    ) -> PaginationParams:
        return PaginationParams(
            offset=offset or 0,
            limit=limit or 20,
            sort_by={"version": "version", "createdAt": "created_at"}.get(
                sort_by or "version", "version"
            ),
            order=SortOrder(order.value) if order is not None else SortOrder.ASC,
        )

    @staticmethod
    def to_status(value: str | None) -> VersionStatus | None:
        return VersionStatus(value) if value is not None else None

    @staticmethod
    def to_response(
        response_type: type,
        page: Page,
        project_name: str,
        pagination: PaginationParams,
        to_api: Callable[[Any, str], Any],
    ) -> Any:
        return response_type(
            data=[to_api(snapshot, project_name) for snapshot in page.items],
            pagination=ApiPagination(
                offset=pagination.offset, limit=pagination.limit, total=page.total
            ),
        )
