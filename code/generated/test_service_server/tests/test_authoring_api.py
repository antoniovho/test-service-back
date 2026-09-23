# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr, field_validator  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from uuid import UUID  # noqa: F401
from test_service_server.models.action_request import ActionRequest  # noqa: F401
from test_service_server.models.create_precondition_request import CreatePreconditionRequest  # noqa: F401
from test_service_server.models.create_test_case_request import CreateTestCaseRequest  # noqa: F401
from test_service_server.models.error_details import ErrorDetails  # noqa: F401
from test_service_server.models.precondition import Precondition  # noqa: F401
from test_service_server.models.precondition_list_response import PreconditionListResponse  # noqa: F401
from test_service_server.models.sort_order import SortOrder  # noqa: F401
from test_service_server.models.test_case import TestCase  # noqa: F401
from test_service_server.models.test_case_list_response import TestCaseListResponse  # noqa: F401
from test_service_server.models.test_case_version_list_response import TestCaseVersionListResponse  # noqa: F401


def test_list_test_cases(client: TestClient):
    """Test case for list_test_cases

    List test case versions
    """
    params = [("project_key", 'project_key_example'),     ("status", 'status_example'),     ("offset", 0),     ("limit", 20),     ("sort_by", 'version'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/test-cases",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_test_case(client: TestClient):
    """Test case for create_test_case

    Create a test case version
    """
    create_test_case_request = test_service_server.CreateTestCaseRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-cases",
    #    headers=headers,
    #    json=create_test_case_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_test_case(client: TestClient):
    """Test case for get_test_case

    Get a test case version
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/test-cases/{testCaseId}".format(testCaseId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_test_case_versions(client: TestClient):
    """Test case for list_test_case_versions

    List versions of a test case key
    """
    params = [("offset", 0),     ("limit", 20)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/test-cases/{testCaseId}/versions".format(testCaseId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_test_case_version(client: TestClient):
    """Test case for create_test_case_version

    Create a new immutable test case version
    """
    create_test_case_request = test_service_server.CreateTestCaseRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-cases/{testCaseId}/versions".format(testCaseId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=create_test_case_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_activate_test_case(client: TestClient):
    """Test case for activate_test_case

    Activate a test case version
    """
    action_request = test_service_server.ActionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-cases/{testCaseId}/activations".format(testCaseId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=action_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_deprecate_test_case(client: TestClient):
    """Test case for deprecate_test_case

    Deprecate a test case version
    """
    action_request = test_service_server.ActionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/test-cases/{testCaseId}/deprecations".format(testCaseId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=action_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_preconditions(client: TestClient):
    """Test case for list_preconditions

    List preconditions
    """
    params = [("status", 'status_example'),     ("offset", 0),     ("limit", 20),     ("sort_by", 'version'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/preconditions",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_precondition(client: TestClient):
    """Test case for create_precondition

    Create a precondition version
    """
    create_precondition_request = test_service_server.CreatePreconditionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/preconditions",
    #    headers=headers,
    #    json=create_precondition_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_precondition(client: TestClient):
    """Test case for get_precondition

    Get a precondition version
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/preconditions/{preconditionId}".format(preconditionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_precondition_versions(client: TestClient):
    """Test case for list_precondition_versions

    List versions of a precondition
    """
    params = [("offset", 0),     ("limit", 20)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/preconditions/{preconditionId}/versions".format(preconditionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_precondition_version(client: TestClient):
    """Test case for create_precondition_version

    Create a precondition version
    """
    create_precondition_request = test_service_server.CreatePreconditionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/preconditions/{preconditionId}/versions".format(preconditionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=create_precondition_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_activate_precondition(client: TestClient):
    """Test case for activate_precondition

    Activate a precondition version
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/preconditions/{preconditionId}/activations".format(preconditionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_deprecate_precondition(client: TestClient):
    """Test case for deprecate_precondition

    Deprecate a precondition version
    """
    action_request = test_service_server.ActionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/preconditions/{preconditionId}/deprecations".format(preconditionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=action_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

