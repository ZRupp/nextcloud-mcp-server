"""Unit tests for WeekPlanner client API methods."""

import logging

import httpx
import pytest

from nextcloud_mcp_server.client.weekplanner import WeekPlannerClient
from tests.client.conftest import (
    create_mock_weekplanner_custom_columns_response,
    create_mock_weekplanner_put_response,
    create_mock_weekplanner_week_response,
)

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.unit


async def test_weekplanner_get_week(mocker):
    """Test that get_week correctly calls the API and returns week data."""
    mock_response = create_mock_weekplanner_week_response(
        days={
            "monday": [
                {
                    "id": "task-1",
                    "title": "Standup",
                    "done": False,
                    "notes": "",
                    "recurrence": "",
                    "color": "",
                }
            ],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": [],
        },
        updated_at=1713100000,
    )

    mock_make_request = mocker.patch.object(
        WeekPlannerClient, "_make_request", return_value=mock_response
    )

    client = WeekPlannerClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_week(2026, 16)

    assert result["updatedAt"] == 1713100000
    assert len(result["days"]["monday"]) == 1
    assert result["days"]["monday"][0]["title"] == "Standup"
    assert result["days"]["tuesday"] == []

    mock_make_request.assert_called_once_with("GET", "/apps/weekplanner/week/2026/16")


async def test_weekplanner_get_week_empty(mocker):
    """Test get_week with an empty week returns default structure."""
    mock_response = create_mock_weekplanner_week_response()

    mocker.patch.object(WeekPlannerClient, "_make_request", return_value=mock_response)

    client = WeekPlannerClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_week(2026, 16)

    assert result["updatedAt"] == 1713100000
    for day in [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]:
        assert result["days"][day] == []


async def test_weekplanner_put_week(mocker):
    """Test that put_week sends the correct body and returns status."""
    mock_response = create_mock_weekplanner_put_response(updated_at=1713100001)

    mock_make_request = mocker.patch.object(
        WeekPlannerClient, "_make_request", return_value=mock_response
    )

    client = WeekPlannerClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    days = {
        "monday": [
            {
                "id": "task-1",
                "title": "Test",
                "done": True,
                "notes": "",
                "recurrence": "",
                "color": "",
            }
        ],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": [],
    }

    result = await client.put_week(2026, 16, days)

    assert result["status"] == "ok"
    assert result["updatedAt"] == 1713100001

    mock_make_request.assert_called_once_with(
        "PUT", "/apps/weekplanner/week/2026/16", json={"days": days}
    )


async def test_weekplanner_get_custom_columns(mocker):
    """Test that get_custom_columns returns columns and recurring tasks."""
    mock_response = create_mock_weekplanner_custom_columns_response(
        columns=[
            {"id": "custom_1", "title": "Someday", "tasks": []},
            {"id": "custom_2", "title": "Goals", "tasks": []},
        ],
        recurring_tasks=[
            {
                "id": "recurring-1",
                "title": "Daily standup",
                "notes": "",
                "recurrence": "daily",
                "startDate": "2026-01-01",
                "endDate": "2026-12-31",
                "dayOfWeek": 0,
                "dayOfMonth": 0,
                "exceptionDates": [],
            }
        ],
    )

    mock_make_request = mocker.patch.object(
        WeekPlannerClient, "_make_request", return_value=mock_response
    )

    client = WeekPlannerClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_custom_columns()

    assert len(result["columns"]) == 2
    assert result["columns"][0]["title"] == "Someday"
    assert len(result["recurringTasks"]) == 1
    assert result["recurringTasks"][0]["recurrence"] == "daily"

    mock_make_request.assert_called_once_with("GET", "/apps/weekplanner/custom-columns")


async def test_weekplanner_put_custom_columns(mocker):
    """Test that put_custom_columns sends correct body."""
    mock_response = create_mock_weekplanner_put_response(updated_at=1713100002)

    mock_make_request = mocker.patch.object(
        WeekPlannerClient, "_make_request", return_value=mock_response
    )

    client = WeekPlannerClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    columns = [{"id": "custom_1", "title": "Someday", "tasks": []}]
    recurring = [{"id": "r1", "title": "Standup", "recurrence": "daily"}]

    result = await client.put_custom_columns(columns, recurring)

    assert result["status"] == "ok"
    assert result["updatedAt"] == 1713100002

    mock_make_request.assert_called_once_with(
        "PUT",
        "/apps/weekplanner/custom-columns",
        json={"columns": columns, "recurringTasks": recurring},
    )


async def test_weekplanner_get_week_error_404(mocker):
    """Test that get_week raises on 404."""
    error_response = httpx.Response(
        status_code=404,
        content=b"Not found",
        request=httpx.Request("GET", "http://test.local/api"),
    )

    mocker.patch.object(
        WeekPlannerClient,
        "_make_request",
        side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=httpx.Request("GET", "http://test.local/api"),
            response=error_response,
        ),
    )

    client = WeekPlannerClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        await client.get_week(2026, 16)
    assert excinfo.value.response.status_code == 404
