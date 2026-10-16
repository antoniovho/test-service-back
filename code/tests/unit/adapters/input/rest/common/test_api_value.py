"""Tests for REST transport value conversions."""

from enum import Enum

from test_service.infrastructure.adapters.input.rest.common.api_value import enum_value


class SortBy(Enum):
    """Representative generated API enum."""

    CREATED_AT = "createdAt"


class TestEnumValue:
    def test_when_given_an_enum_expect_its_primitive_value(self):
        assert enum_value(SortBy.CREATED_AT) == "createdAt"

    def test_when_given_a_string_expect_the_original_value(self):
        assert enum_value("createdAt") == "createdAt"

    def test_when_given_none_expect_none(self):
        assert enum_value(None) is None
