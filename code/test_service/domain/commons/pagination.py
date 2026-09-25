"""Pagination primitives shared by domain queries."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar

DEFAULT_PAGE_LIMIT = 25
MAX_PAGE_LIMIT = 100


class SortOrder(StrEnum):
    """Direction used when ordering a paginated collection.

    Attributes:
        ASC: Orders values from the lowest to the highest.
        DESC: Orders values from the highest to the lowest.
    """

    ASC = "ASC"
    DESC = "DESC"


@dataclass(frozen=True, slots=True)
class PaginationParams:
    """Validated parameters for retrieving a page of a collection.

    Args:
        offset: Number of records to skip before the first returned record.
        limit: Maximum number of records to return.
        sort_by: Optional domain field used to order the collection.
        order: Direction used with ``sort_by``.

    Raises:
        ValueError: If the offset is negative or the limit is outside the supported range.
    """

    offset: int = 0
    limit: int = DEFAULT_PAGE_LIMIT
    sort_by: str | None = None
    order: SortOrder = SortOrder.ASC

    def __post_init__(self) -> None:
        """Validate pagination bounds.

        Raises:
            ValueError: If ``offset`` is negative or ``limit`` is not between one and 100.
        """
        if self.offset < 0:
            raise ValueError("offset must be greater than or equal to zero")
        if not 1 <= self.limit <= MAX_PAGE_LIMIT:
            raise ValueError(f"limit must be between 1 and {MAX_PAGE_LIMIT}")


Item = TypeVar("Item")


@dataclass(frozen=True, slots=True)
class Page[Item]:
    """An immutable page of domain records.

    Args:
        items: Records included in the current page.
        total: Total number of records matching the query.

    Raises:
        ValueError: If ``total`` is negative.
    """

    items: tuple[Item, ...]
    total: int

    def __post_init__(self) -> None:
        """Validate the total number of matching records.

        Raises:
            ValueError: If ``total`` is negative.
        """
        if self.total < 0:
            raise ValueError("total must be greater than or equal to zero")
