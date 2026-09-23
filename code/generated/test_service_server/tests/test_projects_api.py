# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr, field_validator  # noqa: F401
from typing import Any, Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from test_service_server.models.create_project_request import CreateProjectRequest  # noqa: F401
from test_service_server.models.error_details import ErrorDetails  # noqa: F401
from test_service_server.models.project import Project  # noqa: F401
from test_service_server.models.project_list_response import ProjectListResponse  # noqa: F401
from test_service_server.models.sort_order import SortOrder  # noqa: F401


def test_list_projects(client: TestClient):
    """Test case for list_projects

    List projects
    """
    params = [("offset", 0),     ("limit", 20),     ("sort_by", 'version'),     ("order", 'ASC')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/projects",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_project(client: TestClient):
    """Test case for create_project

    Register a project
    """
    create_project_request = test_service_server.CreateProjectRequest()

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/projects",
    #    headers=headers,
    #    json=create_project_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_project(client: TestClient):
    """Test case for get_project

    Get a project
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/projects/{projectKey}".format(projectKey='project_key_example'),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_delete_project(client: TestClient):
    """Test case for delete_project

    Logically delete a project
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "DELETE",
    #    "/v1/projects/{projectKey}".format(projectKey='project_key_example'),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

