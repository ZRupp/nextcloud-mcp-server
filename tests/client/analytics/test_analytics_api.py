"""Unit tests for Analytics client API methods."""

import logging

import httpx
import pytest

from nextcloud_mcp_server.client.analytics import AnalyticsClient
from tests.client.conftest import create_mock_response

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.unit


# --- Reports ---


async def test_analytics_list_reports(mocker):
    """Test that list_reports calls correct endpoint."""
    mock_response = create_mock_response(
        json_data=[
            {"id": 1, "name": "Sales Report", "type": 2},
            {"id": 2, "name": "Traffic Report", "type": 2},
        ]
    )

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.list_reports()

    assert len(result) == 2
    assert result[0]["name"] == "Sales Report"

    mock_make_request.assert_called_once_with("GET", "/apps/analytics/report")


async def test_analytics_get_report(mocker):
    """Test that get_report calls correct endpoint."""
    mock_response = create_mock_response(
        json_data={"id": 1, "name": "Sales Report", "type": 2, "dataset": 5}
    )

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_report(1)

    assert result["id"] == 1
    assert result["name"] == "Sales Report"

    mock_make_request.assert_called_once_with("GET", "/apps/analytics/report/1")


async def test_analytics_create_report(mocker):
    """Test that create_report sends correct payload."""
    mock_response = create_mock_response(json_data={"id": 10, "name": "New Report"})

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.create_report(name="New Report", dataset=5)

    assert result["id"] == 10

    mock_make_request.assert_called_once_with(
        "POST", "/apps/analytics/report", json={"name": "New Report", "dataset": 5}
    )


async def test_analytics_delete_report(mocker):
    """Test that delete_report calls correct endpoint."""
    mock_response = create_mock_response(json_data={})

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.delete_report(1)

    mock_make_request.assert_called_once_with("DELETE", "/apps/analytics/report/1")


async def test_analytics_copy_report(mocker):
    """Test that copy_report sends correct payload."""
    mock_response = create_mock_response(
        json_data={"id": 11, "name": "Sales Report (Copy)"}
    )

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.copy_report(1)

    assert result["id"] == 11

    mock_make_request.assert_called_once_with(
        "POST", "/apps/analytics/report/copy", json={"reportId": 1}
    )


# --- Datasets ---


async def test_analytics_list_datasets(mocker):
    """Test that list_datasets calls correct endpoint."""
    mock_response = create_mock_response(
        json_data=[{"id": 1, "name": "Sales Data"}, {"id": 2, "name": "Web Traffic"}]
    )

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.list_datasets()

    assert len(result) == 2
    mock_make_request.assert_called_once_with("GET", "/apps/analytics/dataset")


async def test_analytics_create_dataset(mocker):
    """Test that create_dataset sends correct payload."""
    mock_response = create_mock_response(json_data={"id": 5, "name": "New Dataset"})

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.create_dataset(name="New Dataset")

    assert result["id"] == 5
    mock_make_request.assert_called_once_with(
        "POST", "/apps/analytics/dataset", json={"name": "New Dataset"}
    )


# --- Panoramas ---


async def test_analytics_list_panoramas(mocker):
    """Test that list_panoramas calls correct endpoint."""
    mock_response = create_mock_response(
        json_data=[{"id": 1, "name": "Main Dashboard"}]
    )

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.list_panoramas()

    assert len(result) == 1
    assert result[0]["name"] == "Main Dashboard"

    mock_make_request.assert_called_once_with("GET", "/apps/analytics/panorama")


async def test_analytics_create_panorama(mocker):
    """Test that create_panorama sends correct payload."""
    mock_response = create_mock_response(json_data={"id": 3, "name": "New Dashboard"})

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.create_panorama(name="New Dashboard")

    assert result["id"] == 3
    mock_make_request.assert_called_once_with(
        "POST", "/apps/analytics/panorama", json={"name": "New Dashboard"}
    )


# --- Data Operations (v3 API) ---


async def test_analytics_get_data(mocker):
    """Test that get_data calls v3 API endpoint."""
    mock_response = create_mock_response(
        json_data={
            "data": [{"dimension1": "Jan", "dimension2": "Sales", "value": "100"}]
        }
    )

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.get_data(1)

    assert "data" in result
    assert len(result["data"]) == 1

    mock_make_request.assert_called_once_with("GET", "/apps/analytics/api/3.0/data/1")


async def test_analytics_add_data(mocker):
    """Test that add_data sends correct v3 API payload."""
    mock_response = create_mock_response(json_data={"success": True})

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    records = [{"dimension1": "Jan", "dimension2": "Sales", "value": "100"}]

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.add_data(5, records)

    mock_make_request.assert_called_once_with(
        "POST",
        "/apps/analytics/api/3.0/data/5/add",
        json={"data": records},
    )


async def test_analytics_delete_data(mocker):
    """Test that delete_data sends correct v3 API payload."""
    mock_response = create_mock_response(json_data={"success": True})

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    records = [{"dimension1": "Jan", "dimension2": "Sales"}]

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.delete_data(5, records)

    mock_make_request.assert_called_once_with(
        "POST",
        "/apps/analytics/api/3.0/data/5/delete",
        json={"delete": records},
    )


# --- Dataloads ---


async def test_analytics_list_dataloads(mocker):
    """Test that list_dataloads calls correct endpoint."""
    mock_response = create_mock_response(
        json_data=[{"id": 1, "name": "Daily Import", "schedule": "0 0 * * *"}]
    )

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.list_dataloads()

    assert len(result) == 1
    mock_make_request.assert_called_once_with("GET", "/apps/analytics/dataload")


async def test_analytics_execute_dataload(mocker):
    """Test that execute_dataload sends correct payload."""
    mock_response = create_mock_response(json_data={"success": True})

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    await client.execute_dataload(1)

    mock_make_request.assert_called_once_with(
        "POST",
        "/apps/analytics/dataload/execute",
        json={"dataloadId": 1},
    )


# --- Datasources ---


async def test_analytics_list_datasources(mocker):
    """Test that list_datasources calls correct endpoint."""
    mock_response = create_mock_response(
        json_data=[
            {"id": 1, "name": "CSV"},
            {"id": 2, "name": "GitHub"},
        ]
    )

    mock_make_request = mocker.patch.object(
        AnalyticsClient, "_make_request", return_value=mock_response
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")
    result = await client.list_datasources()

    assert len(result) == 2
    assert result[0]["name"] == "CSV"

    mock_make_request.assert_called_once_with("GET", "/apps/analytics/datasource")


# --- Error Handling ---


async def test_analytics_get_report_404(mocker):
    """Test that get_report raises on 404."""
    error_response = httpx.Response(
        status_code=404,
        content=b"Not found",
        request=httpx.Request("GET", "http://test.local/api"),
    )

    mocker.patch.object(
        AnalyticsClient,
        "_make_request",
        side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=httpx.Request("GET", "http://test.local/api"),
            response=error_response,
        ),
    )

    client = AnalyticsClient(mocker.AsyncMock(spec=httpx.AsyncClient), "testuser")

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        await client.get_report(999)
    assert excinfo.value.response.status_code == 404
