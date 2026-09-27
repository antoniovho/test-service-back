import pytest

from test_service.domain.commons.pagination import (
    MAX_PAGE_LIMIT,
    Page,
    PaginationParams,
    SortOrder,
)


class TestPaginationParams:
    def test_when_defaults_expect_valid_instance(self):
        params = PaginationParams()

        assert params.offset == 0
        assert params.limit == 20
        assert params.order is SortOrder.ASC

    def test_when_negative_offset_expect_exception(self):
        with pytest.raises(ValueError, match="offset"):
            PaginationParams(offset=-1)

    @pytest.mark.parametrize("limit", [0, MAX_PAGE_LIMIT + 1], ids=["too_low", "too_high"])
    def test_when_limit_out_of_range_expect_exception(self, limit):
        with pytest.raises(ValueError, match="limit"):
            PaginationParams(limit=limit)


class TestPage:
    def test_when_negative_total_expect_exception(self):
        with pytest.raises(ValueError, match="total"):
            Page(items=(), total=-1)

    def test_when_valid_total_expect_instance(self):
        page = Page(items=(1, 2), total=2)

        assert page.items == (1, 2)
        assert page.total == 2
