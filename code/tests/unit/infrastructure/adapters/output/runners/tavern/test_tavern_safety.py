import pytest

from test_service.infrastructure.adapters.output.runners.tavern.tavern_safety import (
    find_unsafe_tavern_construct,
)


class TestFindUnsafeTavernConstruct:
    @pytest.mark.parametrize(
        ("value", "construct"),
        [
            ("{tavern.env_vars.SECRET}", "tavern.env_vars.SECRET"),
            ({"url": "https://api.example.test/?key={tavern.env_vars.API_KEY}"}, "tavern"),
            ({"headers": {"{tavern.env_vars.HEADER}": "value"}}, "tavern"),
            ({"headers": {"X-Leak": "{tavern[env_vars][SECRET]}"}}, "tavern"),
            ({"headers": {"X-Leak": "{tavern.env_vars.SECRET!s}"}}, "tavern"),
            ({"headers": {"X-Leak": "{orderId:{tavern.env_vars.SECRET}}"}}, "tavern"),
            ({"json": [{"token": "{tavern.env_vars.SECRET}"}]}, "tavern"),
            ({"json": ({"token": "{tavern.env_vars.SECRET}"},)}, "tavern"),
        ],
        ids=[
            "string",
            "mapping-value",
            "mapping-key",
            "indexed-root",
            "conversion",
            "nested-format-spec",
            "list-item",
            "tuple-item",
        ],
    )
    def test_when_value_uses_tavern_namespace_expect_description(self, value, construct):
        found = find_unsafe_tavern_construct(value)

        assert found is not None
        assert construct in found

    @pytest.mark.parametrize(
        "value",
        [
            "{orderId}",
            {"url": "{{baseUrl}}/orders/{orderId}"},
            {"headers": {"X-Literal": "{{tavern.env_vars.SECRET}}"}},
            {"json": {"$ref": "#/definitions/order", "$schema": "draft-07"}},
            {"json": [1, True, None, 2.5]},
            {"json": ({"token": "{orderId}"},)},
            "unmatched { brace",
        ],
        ids=[
            "ordinary-field",
            "service-template-and-ordinary-field",
            "escaped-tavern-field",
            "other-dollar-keys",
            "scalar-list",
            "ordinary-tuple-item",
            "invalid-format-string",
        ],
    )
    def test_when_value_has_no_unsafe_tavern_construct_expect_none(self, value):
        assert find_unsafe_tavern_construct(value) is None

    @pytest.mark.parametrize(
        ("value", "construct"),
        [
            ({"json": {"$ext": {"function": "os:system"}}}, "$ext"),
            ({"headers": {"X-Leak": "{orderId.__class__}"}}, "__class__"),
        ],
        ids=["executable-directive", "dunder-traversal"],
    )
    def test_when_value_violates_shared_definition_policy_expect_description(
        self, value, construct
    ):
        found = find_unsafe_tavern_construct(value)

        assert found is not None
        assert construct in found
