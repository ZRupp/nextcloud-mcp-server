"""Unit tests for Agora client API methods."""

import logging

import httpx
import pytest

from nextcloud_mcp_server.client.agora import AgoraClient
from tests.client.conftest import (
    create_mock_agora_comment_response,
    create_mock_agora_comments_list_response,
    create_mock_agora_inquiries_list_response,
    create_mock_agora_inquiry_response,
    create_mock_response,
)

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.unit


# --- Inquiry Tests ---


async def test_agora_list_inquiries(mocker):
    """Test that list_inquiries returns a list of inquiry dicts."""
    mock_response = create_mock_agora_inquiries_list_response()

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.list_inquiries()

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["title"] == "Proposal A"
    assert result[1]["type"] == "debate"

    mock_make_request.assert_called_once_with("GET", "/apps/agora/api/v1.0/inquiries")


async def test_agora_get_inquiry(mocker):
    """Test that get_inquiry returns a single inquiry dict."""
    mock_response = create_mock_agora_inquiry_response(
        inquiry_id=42, title="My Proposal", inquiry_type="proposal"
    )

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_inquiry(42)

    assert result["id"] == 42
    assert result["title"] == "My Proposal"
    assert result["type"] == "proposal"

    mock_make_request.assert_called_once_with("GET", "/apps/agora/api/v1.0/inquiry/42")


async def test_agora_create_inquiry(mocker):
    """Test that create_inquiry sends correct payload."""
    mock_response = create_mock_agora_inquiry_response(
        inquiry_id=99, title="New Debate", inquiry_type="debate"
    )

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.create_inquiry(
        inquiry_type="debate", title="New Debate", description="About things"
    )

    assert result["id"] == 99
    assert result["title"] == "New Debate"

    mock_make_request.assert_called_once_with(
        "POST",
        "/apps/agora/api/v1.0/inquiry",
        json={"type": "debate", "title": "New Debate", "description": "About things"},
    )


async def test_agora_update_inquiry(mocker):
    """Test that update_inquiry sends correct payload structure."""
    mock_response = create_mock_agora_inquiry_response(
        inquiry_id=1, title="Updated Title"
    )

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.update_inquiry(1, title="Updated Title", access="private")

    assert result["title"] == "Updated Title"

    mock_make_request.assert_called_once_with(
        "PUT",
        "/apps/agora/api/v1.0/inquiry/1",
        json={"inquiry": {"title": "Updated Title", "access": "private"}},
    )


async def test_agora_delete_inquiry(mocker):
    """Test that delete_inquiry calls the correct endpoint."""
    mock_response = create_mock_agora_inquiry_response(inquiry_id=5)

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.delete_inquiry(5)

    mock_make_request.assert_called_once_with(
        "DELETE", "/apps/agora/api/v1.0/inquiry/5"
    )


# --- Inquiry Actions ---


async def test_agora_clone_inquiry(mocker):
    """Test that clone_inquiry calls the correct endpoint."""
    mock_response = create_mock_agora_inquiry_response(inquiry_id=100)

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.clone_inquiry(10)

    assert result["id"] == 100
    mock_make_request.assert_called_once_with(
        "POST", "/apps/agora/api/v1.0/inquiry/10/clone"
    )


async def test_agora_trash_inquiry(mocker):
    """Test that trash_inquiry uses PUT to toggle archive state."""
    mock_response = create_mock_agora_inquiry_response(inquiry_id=10)

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.trash_inquiry(10)

    mock_make_request.assert_called_once_with(
        "PUT", "/apps/agora/api/v1.0/inquiry/10/archive/toggle"
    )


async def test_agora_close_inquiry(mocker):
    """Test that close_inquiry uses PUT."""
    mock_response = create_mock_agora_inquiry_response(inquiry_id=10)

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.close_inquiry(10)

    mock_make_request.assert_called_once_with(
        "PUT", "/apps/agora/api/v1.0/inquiry/10/close"
    )


async def test_agora_reopen_inquiry(mocker):
    """Test that reopen_inquiry uses PUT."""
    mock_response = create_mock_agora_inquiry_response(inquiry_id=10)

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.reopen_inquiry(10)

    mock_make_request.assert_called_once_with(
        "PUT", "/apps/agora/api/v1.0/inquiry/10/reopen"
    )


# --- Comments ---


async def test_agora_get_comments(mocker):
    """Test that get_comments returns comment list."""
    mock_response = create_mock_agora_comments_list_response()

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_comments(1)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["message"] == "Comment 1"

    mock_make_request.assert_called_once_with(
        "GET", "/apps/agora/api/v1.0/inquiry/1/comments"
    )


async def test_agora_create_comment(mocker):
    """Test that create_comment sends correct payload."""
    mock_response = create_mock_agora_comment_response(
        comment_id=5, inquiry_id=1, message="My comment"
    )

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.create_comment(1, "My comment")

    assert result["id"] == 5
    assert result["message"] == "My comment"

    mock_make_request.assert_called_once_with(
        "POST",
        "/apps/agora/api/v1.0/inquiry/1/comment",
        json={"message": "My comment"},
    )


# --- Suggestions ---


async def test_agora_get_suggestions(mocker):
    """Test that get_suggestions calls correct endpoint."""
    mock_response = create_mock_response(
        json_data=[
            {"id": 1, "inquiryId": 1, "message": "Suggestion 1"},
        ]
    )

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_suggestions(1)

    assert len(result) == 1
    assert result[0]["message"] == "Suggestion 1"

    mock_make_request.assert_called_once_with(
        "GET", "/apps/agora/api/v1.0/inquiry/1/suggestions"
    )


# --- Supports ---


async def test_agora_get_supports(mocker):
    """Test that get_supports calls correct endpoint."""
    mock_response = create_mock_response(
        json_data=[
            {"id": 1, "inquiryId": 1, "userId": "user1", "status": "supported"},
        ]
    )

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_supports(1)

    assert len(result) == 1
    assert result[0]["status"] == "supported"

    mock_make_request.assert_called_once_with(
        "GET", "/apps/agora/api/v1.0/inquiry/1/supports"
    )


# --- Inquiry Types ---


async def test_agora_get_inquiry_types(mocker):
    """Test that get_inquiry_types calls correct endpoint."""
    mock_response = create_mock_response(
        json_data=[
            {"name": "Proposal", "value": "proposal"},
            {"name": "Debate", "value": "debate"},
        ]
    )

    mock_make_request = mocker.patch.object(
        AgoraClient, "_make_request", return_value=mock_response
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_inquiry_types()

    assert len(result) == 2
    assert result[0]["value"] == "proposal"

    mock_make_request.assert_called_once_with("GET", "/apps/agora/api/v1.0/enum")


# --- Error Handling ---


async def test_agora_get_inquiry_404(mocker):
    """Test that get_inquiry raises on 404."""
    error_response = httpx.Response(
        status_code=404,
        content=b"Not found",
        request=httpx.Request("GET", "http://test.local/api"),
    )

    mocker.patch.object(
        AgoraClient,
        "_make_request",
        side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=httpx.Request("GET", "http://test.local/api"),
            response=error_response,
        ),
    )

    client = AgoraClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        await client.get_inquiry(999)
    assert excinfo.value.response.status_code == 404
