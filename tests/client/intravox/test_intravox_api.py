"""Unit tests for IntraVox client API methods."""

import logging

import httpx
import pytest

from nextcloud_mcp_server.client.intravox import IntravoxClient
from tests.client.conftest import (
    create_mock_intravox_ocs_response,
    create_mock_intravox_page_response,
    create_mock_intravox_pages_list_response,
    create_mock_response,
)

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.unit


# --- Pages (OCS) ---


async def test_intravox_list_pages(mocker):
    """Test that list_pages calls OCS endpoint and unwraps response."""
    mock_response = create_mock_intravox_pages_list_response()

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.list_pages()

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["title"] == "Home"
    assert result[1]["status"] == "draft"

    mock_make_request.assert_called_once_with(
        "GET",
        "/ocs/v2.php/apps/intravox/api/v1/pages",
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
    )


async def test_intravox_get_page(mocker):
    """Test that get_page calls OCS endpoint with page ID."""
    mock_response = create_mock_intravox_page_response(
        unique_id="page-uuid-42", title="My Page"
    )

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_page("page-uuid-42")

    assert result["uniqueId"] == "page-uuid-42"
    assert result["title"] == "My Page"

    mock_make_request.assert_called_once_with(
        "GET",
        "/ocs/v2.php/apps/intravox/api/v1/pages/page-uuid-42",
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
    )


async def test_intravox_create_page(mocker):
    """Test that create_page sends correct OCS payload."""
    mock_response = create_mock_intravox_page_response(
        unique_id="new-page", title="New Page"
    )

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.create_page(title="New Page", language="en")

    assert result["title"] == "New Page"

    mock_make_request.assert_called_once_with(
        "POST",
        "/ocs/v2.php/apps/intravox/api/v1/pages",
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        json={"title": "New Page", "language": "en"},
    )


async def test_intravox_delete_page(mocker):
    """Test that delete_page calls correct OCS endpoint."""
    mock_response = create_mock_intravox_ocs_response(data={})

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.delete_page("page-uuid-1")

    mock_make_request.assert_called_once_with(
        "DELETE",
        "/ocs/v2.php/apps/intravox/api/v1/pages/page-uuid-1",
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
    )


# --- Search (Internal) ---


async def test_intravox_search_pages(mocker):
    """Test that search_pages calls internal search endpoint."""
    mock_response = create_mock_response(
        json_data=[
            {"uniqueId": "page-1", "title": "Result 1"},
            {"uniqueId": "page-2", "title": "Result 2"},
        ]
    )

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.search_pages("vacation policy")

    assert len(result) == 2
    assert result[0]["title"] == "Result 1"

    mock_make_request.assert_called_once_with(
        "GET",
        "/apps/intravox/api/search",
        params={"query": "vacation policy"},
    )


# --- Navigation (Internal) ---


async def test_intravox_get_page_tree(mocker):
    """Test that get_page_tree calls internal endpoint."""
    mock_response = create_mock_response(
        json_data=[
            {"uniqueId": "home", "title": "Home", "children": []},
        ]
    )

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_page_tree()

    assert len(result) == 1
    assert result[0]["title"] == "Home"

    mock_make_request.assert_called_once_with("GET", "/apps/intravox/api/pages/tree")


async def test_intravox_get_navigation(mocker):
    """Test that get_navigation calls internal endpoint."""
    mock_response = create_mock_response(
        json_data={"items": [{"title": "Home", "pageId": "home"}]}
    )

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_navigation()

    assert "items" in result

    mock_make_request.assert_called_once_with("GET", "/apps/intravox/api/navigation")


# --- Comments (Internal) ---


async def test_intravox_get_comments(mocker):
    """Test that get_comments calls internal comments endpoint."""
    mock_response = create_mock_response(
        json_data=[
            {"id": 1, "message": "Great page!", "author": "user1"},
            {"id": 2, "message": "Thanks!", "author": "user2"},
        ]
    )

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_comments("page-1")

    assert len(result) == 2
    assert result[0]["message"] == "Great page!"

    mock_make_request.assert_called_once_with(
        "GET", "/apps/intravox/api/pages/page-1/comments"
    )


async def test_intravox_create_comment(mocker):
    """Test that create_comment sends correct payload."""
    mock_response = create_mock_response(
        json_data={"id": 5, "message": "My comment", "author": "testuser"}
    )

    mock_make_request = mocker.patch.object(
        IntravoxClient, "_make_request", return_value=mock_response
    )

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.create_comment("page-1", "My comment")

    assert result["id"] == 5
    assert result["message"] == "My comment"

    mock_make_request.assert_called_once_with(
        "POST",
        "/apps/intravox/api/pages/page-1/comments",
        json={"message": "My comment"},
    )


# --- OCS Error Handling ---


async def test_intravox_ocs_error(mocker):
    """Test that OCS error statuscode raises RuntimeError."""
    mock_response = create_mock_intravox_ocs_response(data={}, ocs_statuscode=404)

    mocker.patch.object(IntravoxClient, "_make_request", return_value=mock_response)

    client = IntravoxClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")

    with pytest.raises(RuntimeError, match="OCS API error"):
        await client.get_page("nonexistent")
