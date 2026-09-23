# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from uuid import UUID  # noqa: F401
from test_service_server.models.action_result_list_response import ActionResultListResponse  # noqa: F401
from test_service_server.models.create_environment_request import CreateEnvironmentRequest  # noqa: F401
from test_service_server.models.create_execution_request import CreateExecutionRequest  # noqa: F401
from test_service_server.models.environment import Environment  # noqa: F401
from test_service_server.models.environment_list_response import EnvironmentListResponse  # noqa: F401
from test_service_server.models.error_details import ErrorDetails  # noqa: F401
from test_service_server.models.execution import Execution  # noqa: F401
from test_service_server.models.execution_list_response import ExecutionListResponse  # noqa: F401
from test_service_server.models.test_result import TestResult  # noqa: F401
from test_service_server.models.test_result_artifact_list_response import TestResultArtifactListResponse  # noqa: F401
from test_service_server.models.test_result_list_response import TestResultListResponse  # noqa: F401


def test_list_environments(client: TestClient):
    """Test case for list_environments

    List execution environments
    """
    params = [("offset", 0),     ("limit", 20)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/environments",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_environment(client: TestClient):
    """Test case for create_environment

    Create an environment metadata resource
    """
    create_environment_request = test_service_server.CreateEnvironmentRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/environments",
    #    headers=headers,
    #    json=create_environment_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_environment(client: TestClient):
    """Test case for get_environment

    Get an environment
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/environments/{environmentId}".format(environmentId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_activate_environment(client: TestClient):
    """Test case for activate_environment

    Activate an environment
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/environments/{environmentId}/activations".format(environmentId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_deactivate_environment(client: TestClient):
    """Test case for deactivate_environment

    Deactivate an environment
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/environments/{environmentId}/deactivations".format(environmentId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_executions(client: TestClient):
    """Test case for list_executions

    List executions
    """
    params = [("project_key", 'project_key_example'),     ("offset", 0),     ("limit", 20)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/executions",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_execution(client: TestClient):
    """Test case for create_execution

    Create and schedule a plan execution
    """
    create_execution_request = test_service_server.CreateExecutionRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/executions",
    #    headers=headers,
    #    json=create_execution_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_execution(client: TestClient):
    """Test case for get_execution

    Get an execution
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/executions/{executionId}".format(executionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_cancel_execution(client: TestClient):
    """Test case for cancel_execution

    Cancel an execution
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/executions/{executionId}/cancellations".format(executionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_execution_results(client: TestClient):
    """Test case for list_execution_results

    List results for an execution
    """
    params = [("offset", 0),     ("limit", 20)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/executions/{executionId}/results".format(executionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_execution_result(client: TestClient):
    """Test case for get_execution_result

    Get an execution result
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/executions/{executionId}/results/{testResultId}".format(executionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d'), testResultId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_execution_result_actions(client: TestClient):
    """Test case for list_execution_result_actions

    List execution result actions
    """
    params = [("offset", 0),     ("limit", 20)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/executions/{executionId}/results/{testResultId}/actions".format(executionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d'), testResultId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_execution_result_artifacts(client: TestClient):
    """Test case for list_execution_result_artifacts

    List execution result artifacts
    """
    params = [("offset", 0),     ("limit", 20)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/executions/{executionId}/results/{testResultId}/artifacts".format(executionId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d'), testResultId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

