# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from test_service_server.models.drift_event import DriftEvent  # noqa: F401
from test_service_server.models.drift_event_list_response import DriftEventListResponse  # noqa: F401
from test_service_server.models.error_details import ErrorDetails  # noqa: F401
from test_service_server.models.viewer_sync_record import ViewerSyncRecord  # noqa: F401
from test_service_server.models.viewer_sync_record_list_response import ViewerSyncRecordListResponse  # noqa: F401


def test_publish_viewer_projection(client: TestClient):
    """Test case for publish_viewer_projection

    Publish canonical data to the external viewer
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/viewer/publications",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_check_viewer_drift(client: TestClient):
    """Test case for check_viewer_drift

    Detect changes made in the external viewer
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/viewer/drift-checks",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_viewer_sync_records(client: TestClient):
    """Test case for list_viewer_sync_records

    List outbound synchronization records
    """
    params = [("offset", 0),     ("limit", 20)]
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
    params = [("offset", 0),     ("limit", 20)]
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

