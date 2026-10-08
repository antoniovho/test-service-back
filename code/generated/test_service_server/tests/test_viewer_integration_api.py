# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr, field_validator  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from uuid import UUID  # noqa: F401
from test_service_server.models.drift_event_list_response import DriftEventListResponse  # noqa: F401
from test_service_server.models.error_details import ErrorDetails  # noqa: F401
from test_service_server.models.sort_order import SortOrder  # noqa: F401
from test_service_server.models.viewer_operation import ViewerOperation  # noqa: F401
from test_service_server.models.viewer_operation_list_response import ViewerOperationListResponse  # noqa: F401
from test_service_server.models.viewer_operation_request import ViewerOperationRequest  # noqa: F401
from test_service_server.models.viewer_sync_record_list_response import ViewerSyncRecordListResponse  # noqa: F401
from test_service_server.models.viewer_type import ViewerType  # noqa: F401


def test_publish_viewer_projection(client: TestClient):
    """Test case for publish_viewer_projection

    Publish canonical data to the external viewer
    """
    viewer_operation_request = test_service_server.ViewerOperationRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/projects/{projectKey}/viewer/publications".format(projectKey='project_key_example'),
    #    headers=headers,
    #    json=viewer_operation_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_check_viewer_drift(client: TestClient):
    """Test case for check_viewer_drift

    Detect changes made in the external viewer
    """
    viewer_operation_request = test_service_server.ViewerOperationRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/projects/{projectKey}/viewer/drift-checks".format(projectKey='project_key_example'),
    #    headers=headers,
    #    json=viewer_operation_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_project_viewer_sync_records(client: TestClient):
    """Test case for list_project_viewer_sync_records

    List outbound synchronization records for a project
    """
    params = [("viewer_type", test_service_server.ViewerType()),     ("offset", 0),     ("limit", 20),     ("sort_by", 'createdAt'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/projects/{projectKey}/viewer/sync-records".format(projectKey='project_key_example'),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_project_viewer_drift_events(client: TestClient):
    """Test case for list_project_viewer_drift_events

    List detected viewer drift events for a project
    """
    params = [("viewer_type", test_service_server.ViewerType()),     ("offset", 0),     ("limit", 20),     ("sort_by", 'detectedAt'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/projects/{projectKey}/viewer/drift-events".format(projectKey='project_key_example'),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_project_viewer_operations(client: TestClient):
    """Test case for list_project_viewer_operations

    List asynchronous Viewer operations for a project
    """
    params = [("viewer_type", test_service_server.ViewerType()),     ("offset", 0),     ("limit", 20),     ("sort_by", 'createdAt'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/projects/{projectKey}/viewer/operations".format(projectKey='project_key_example'),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_project_viewer_operation(client: TestClient):
    """Test case for get_project_viewer_operation

    Get an asynchronous Viewer operation
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/projects/{projectKey}/viewer/operations/{viewerOperationId}".format(projectKey='project_key_example', viewerOperationId=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_viewer_sync_records(client: TestClient):
    """Test case for list_viewer_sync_records

    List outbound synchronization records
    """
    params = [("viewer_type", test_service_server.ViewerType()),     ("offset", 0),     ("limit", 20),     ("sort_by", 'createdAt'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/viewer/sync-records",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_viewer_drift_events(client: TestClient):
    """Test case for list_viewer_drift_events

    List detected viewer drift events
    """
    params = [("viewer_type", test_service_server.ViewerType()),     ("offset", 0),     ("limit", 20),     ("sort_by", 'detectedAt'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/viewer/drift-events",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_viewer_operations(client: TestClient):
    """Test case for list_viewer_operations

    List asynchronous Viewer operations
    """
    params = [("viewer_type", test_service_server.ViewerType()),     ("offset", 0),     ("limit", 20),     ("sort_by", 'createdAt'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/viewer/operations",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

