import pytest

from test_service.domain.model.authoring.definition_safety import (
    find_unsafe_definition_construct,
)


class TestFindUnsafeDefinitionConstruct:
    @pytest.mark.parametrize(
        ("value", "construct"),
        [
            ({"json": {"$ext": {"function": "os:system", "extra_args": ["id"]}}}, "$ext"),
            ({"headers": {"$ext": {"function": "os:getenv"}}}, "$ext"),
            ({"params": {"$ext": {"function": "os:getenv"}}}, "$ext"),
            ({"save": {"$ext": {"function": "os:system"}}}, "$ext"),
            ({"expectedJson": {"data": {"$ext": {"function": "os:system"}}}}, "$ext"),
            ({"json": [{"item": {"$ext": {"function": "os:system"}}}]}, "$ext"),
            ({"json": ({"$ext": {"function": "os:system"}},)}, "$ext"),
            ({"headers": {"X-Leak": "{orderId.__class__}"}}, "__class__"),
            ({"headers": {"X-Leak": "{orderId[__class__]}"}}, "__class__"),
        ],
    )
    def test_when_value_uses_unsafe_construct_expect_description(self, value, construct):
        found = find_unsafe_definition_construct(value)

        assert found is not None
        assert construct in found

    @pytest.mark.parametrize(
        "value",
        [
            {"headers": {"X-Order": "{orderId}"}},
            {"url": "{{baseUrl}}/orders/{orderId}"},
            {"headers": {"X-Literal": "{tavern.env_vars.SECRET}"}},
            {"json": {"_id": "{_id}", "name": "{items[0].name}"}},
            {"json": {"$ref": "#/definitions/order", "$schema": "draft-07"}},
            {"json": {"text": "unmatched { brace"}},
            {"json": [1, True, None, 2.5]},
            {},
            None,
            42,
        ],
    )
    def test_when_value_has_no_unsafe_construct_expect_none(self, value):
        assert find_unsafe_definition_construct(value) is None

    def test_when_several_constructs_present_expect_first_one_reported(self):
        value = {"json": {"$ext": {"function": "os:system"}}, "headers": {"X": "{value.__class__}"}}

        assert find_unsafe_definition_construct(value) == "executable directive '$ext'"
