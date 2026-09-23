# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr, field_validator  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from uuid import UUID  # noqa: F401
from test_service_server.models.action_request import ActionRequest  # noqa: F401
from test_service_server.models.create_test_plan_request import CreateTestPlanRequest  # noqa: F401
from test_service_server.models.create_test_set_request import CreateTestSetRequest  # noqa: F401
from test_service_server.models.error_details import ErrorDetails  # noqa: F401
from test_service_server.models.sort_order import SortOrder  # noqa: F401
from test_service_server.models.test_plan import TestPlan  # noqa: F401
from test_service_server.models.test_plan_list_response import TestPlanListResponse  # noqa: F401
from test_service_server.models.test_set import TestSet  # noqa: F401
from test_service_server.models.test_set_list_response import TestSetListResponse  # noqa: F401


def test_list_test_sets(client: TestClient):
    """Test case for list_test_sets

    List test set snapshots
    """
    params = [("project_key", 'project_key_example'),     ("status", 'status_example'),     ("offset", 0),     ("limit", 20),     ("sort_by", 'version'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/test-sets",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_test_set(client: TestClient):
    """Test case for create_test_set

    Create a test set snapshot
    """
    create_test_set_request = test_service_server.CreateTestSetRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-sets",
    #    headers=headers,
    #    json=create_test_set_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_test_set(client: TestClient):
    """Test case for get_test_set

    Get a test set version
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/test-sets/{testSetId}".format(testSetId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_test_set_version(client: TestClient):
    """Test case for create_test_set_version

    Create a test set version
    """
    create_test_set_request = test_service_server.CreateTestSetRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-sets/{testSetId}/versions".format(testSetId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=create_test_set_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_activate_test_set(client: TestClient):
    """Test case for activate_test_set

    Activate a test set version
    """
    action_request = test_service_server.ActionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-sets/{testSetId}/activations".format(testSetId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=action_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_deprecate_test_set(client: TestClient):
    """Test case for deprecate_test_set

    Deprecate a test set version
    """
    action_request = test_service_server.ActionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-sets/{testSetId}/deprecations".format(testSetId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=action_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_test_plans(client: TestClient):
    """Test case for list_test_plans

    List test plan snapshots
    """
    params = [("project_key", 'project_key_example'),     ("status", 'status_example'),     ("offset", 0),     ("limit", 20),     ("sort_by", 'version'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/test-plans",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_test_plan(client: TestClient):
    """Test case for create_test_plan

    Create a test plan snapshot
    """
    create_test_plan_request = test_service_server.CreateTestPlanRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-plans",
    #    headers=headers,
    #    json=create_test_plan_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_test_plan(client: TestClient):
    """Test case for get_test_plan

    Get a test plan version
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/test-plans/{testPlanId}".format(testPlanId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_test_plan_version(client: TestClient):
    """Test case for create_test_plan_version

    Create a test plan version
    """
    create_test_plan_request = test_service_server.CreateTestPlanRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-plans/{testPlanId}/versions".format(testPlanId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=create_test_plan_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_activate_test_plan(client: TestClient):
    """Test case for activate_test_plan

    Activate a test plan version
    """
    action_request = test_service_server.ActionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-plans/{testPlanId}/activations".format(testPlanId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=action_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_deprecate_test_plan(client: TestClient):
    """Test case for deprecate_test_plan

    Deprecate a test plan version
    """
    action_request = test_service_server.ActionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-plans/{testPlanId}/deprecations".format(testPlanId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=action_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

