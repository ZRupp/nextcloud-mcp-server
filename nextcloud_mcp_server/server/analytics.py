"""MCP tools for Nextcloud Analytics app."""

import logging
from typing import Any

from httpx import HTTPStatusError, RequestError
from mcp.server.fastmcp import Context, FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, ToolAnnotations

from nextcloud_mcp_server.auth import require_scopes
from nextcloud_mcp_server.context import get_client
from nextcloud_mcp_server.models.analytics import (
    AddDataResponse,
    AnalyticsDataload,
    AnalyticsDataset,
    AnalyticsDatasource,
    AnalyticsPanorama,
    AnalyticsReport,
    CreateDatasetResponse,
    CreatePanoramaResponse,
    CreateReportResponse,
    DeleteDataResponse,
    DeleteDatasetResponse,
    DeletePanoramaResponse,
    DeleteReportResponse,
    ExecuteDataloadResponse,
    GetDataResponse,
    GetDatasetResponse,
    GetPanoramaResponse,
    GetReportResponse,
    ListDataloadsResponse,
    ListDatasetsResponse,
    ListDatasourcesResponse,
    ListPanoramasResponse,
    ListReportsResponse,
    UpdateDatasetResponse,
    UpdatePanoramaResponse,
    UpdateReportResponse,
)
from nextcloud_mcp_server.observability.metrics import instrument_tool

logger = logging.getLogger(__name__)


def _handle_error(action: str, e: Exception) -> McpError:
    """Build a standard McpError from an exception."""
    if isinstance(e, RequestError):
        return McpError(ErrorData(code=-1, message=f"Network error {action}: {e!s}"))
    if isinstance(e, HTTPStatusError):
        return McpError(
            ErrorData(code=-1, message=f"Failed to {action}: {e.response.status_code}")
        )
    return McpError(ErrorData(code=-1, message=f"Failed to {action}: {e!s}"))


def configure_analytics_tools(mcp: FastMCP):
    """Configure Analytics app MCP tools."""

    # --- Reports ---

    @mcp.tool(
        title="List Analytics Reports",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_list_reports(ctx: Context) -> ListReportsResponse:
        """List all Analytics reports."""
        client = await get_client(ctx)
        try:
            data = await client.analytics.list_reports()
            reports = [AnalyticsReport(**r) for r in data]
            return ListReportsResponse(results=reports, total_count=len(reports))
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("list reports", e)

    @mcp.tool(
        title="Get Analytics Report",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_get_report(
        report_id: int, ctx: Context
    ) -> GetReportResponse:
        """Get details of a specific Analytics report.

        Args:
            report_id: Report ID
        """
        client = await get_client(ctx)
        try:
            data = await client.analytics.get_report(report_id)
            report = AnalyticsReport(**data)
            return GetReportResponse(results=[report])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("get report", e)

    @mcp.tool(
        title="Create Analytics Report",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_create_report(
        name: str,
        ctx: Context,
        dataset_id: int | None = None,
        parent: int | None = None,
    ) -> CreateReportResponse:
        """Create a new Analytics report.

        Args:
            name: Report name
            dataset_id: Optional dataset to link to
            parent: Optional parent folder ID
        """
        client = await get_client(ctx)
        try:
            fields: dict[str, Any] = {"name": name}
            if dataset_id is not None:
                fields["dataset"] = dataset_id
            if parent is not None:
                fields["parent"] = parent
            data = await client.analytics.create_report(**fields)
            report = AnalyticsReport(**data)
            return CreateReportResponse(results=[report])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("create report", e)

    @mcp.tool(
        title="Update Analytics Report",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_update_report(
        report_id: int,
        report_data: dict,
        ctx: Context,
    ) -> UpdateReportResponse:
        """Update an Analytics report's configuration.

        Args:
            report_id: Report ID
            report_data: Dict of fields to update (name, type, parent, etc.)
        """
        client = await get_client(ctx)
        try:
            data = await client.analytics.update_report(report_id, **report_data)
            report = AnalyticsReport(**data)
            return UpdateReportResponse(results=[report])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("update report", e)

    @mcp.tool(
        title="Delete Analytics Report",
        annotations=ToolAnnotations(
            destructiveHint=True, idempotentHint=True, openWorldHint=True
        ),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_delete_report(
        report_id: int, ctx: Context
    ) -> DeleteReportResponse:
        """Delete an Analytics report permanently.

        Args:
            report_id: Report ID
        """
        client = await get_client(ctx)
        try:
            await client.analytics.delete_report(report_id)
            return DeleteReportResponse(message=f"Report {report_id} deleted")
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("delete report", e)

    @mcp.tool(
        title="Copy Analytics Report",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_copy_report(
        report_id: int, ctx: Context
    ) -> CreateReportResponse:
        """Duplicate an existing Analytics report.

        Args:
            report_id: Report ID to copy
        """
        client = await get_client(ctx)
        try:
            data = await client.analytics.copy_report(report_id)
            report = AnalyticsReport(**data)
            return CreateReportResponse(results=[report])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("copy report", e)

    # --- Datasets ---

    @mcp.tool(
        title="List Analytics Datasets",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_list_datasets(ctx: Context) -> ListDatasetsResponse:
        """List all Analytics datasets."""
        client = await get_client(ctx)
        try:
            data = await client.analytics.list_datasets()
            datasets = [AnalyticsDataset(**d) for d in data]
            return ListDatasetsResponse(results=datasets, total_count=len(datasets))
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("list datasets", e)

    @mcp.tool(
        title="Get Analytics Dataset",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_get_dataset(
        dataset_id: int, ctx: Context
    ) -> GetDatasetResponse:
        """Get details of a specific Analytics dataset.

        Args:
            dataset_id: Dataset ID
        """
        client = await get_client(ctx)
        try:
            data = await client.analytics.get_dataset(dataset_id)
            dataset = AnalyticsDataset(**data)
            return GetDatasetResponse(results=[dataset])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("get dataset", e)

    @mcp.tool(
        title="Create Analytics Dataset",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_create_dataset(
        name: str,
        ctx: Context,
        parent: int | None = None,
    ) -> CreateDatasetResponse:
        """Create a new Analytics dataset (data storage).

        Args:
            name: Dataset name
            parent: Optional parent folder ID
        """
        client = await get_client(ctx)
        try:
            fields: dict[str, Any] = {"name": name}
            if parent is not None:
                fields["parent"] = parent
            data = await client.analytics.create_dataset(**fields)
            dataset = AnalyticsDataset(**data)
            return CreateDatasetResponse(results=[dataset])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("create dataset", e)

    @mcp.tool(
        title="Update Analytics Dataset",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_update_dataset(
        dataset_id: int,
        dataset_data: dict,
        ctx: Context,
    ) -> UpdateDatasetResponse:
        """Update an Analytics dataset's configuration.

        Args:
            dataset_id: Dataset ID
            dataset_data: Dict of fields to update
        """
        client = await get_client(ctx)
        try:
            data = await client.analytics.update_dataset(dataset_id, **dataset_data)
            dataset = AnalyticsDataset(**data)
            return UpdateDatasetResponse(results=[dataset])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("update dataset", e)

    @mcp.tool(
        title="Delete Analytics Dataset",
        annotations=ToolAnnotations(
            destructiveHint=True, idempotentHint=True, openWorldHint=True
        ),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_delete_dataset(
        dataset_id: int, ctx: Context
    ) -> DeleteDatasetResponse:
        """Delete an Analytics dataset permanently.

        Args:
            dataset_id: Dataset ID
        """
        client = await get_client(ctx)
        try:
            await client.analytics.delete_dataset(dataset_id)
            return DeleteDatasetResponse(message=f"Dataset {dataset_id} deleted")
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("delete dataset", e)

    # --- Panoramas ---

    @mcp.tool(
        title="List Analytics Panoramas",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_list_panoramas(ctx: Context) -> ListPanoramasResponse:
        """List all Analytics panoramas (dashboards)."""
        client = await get_client(ctx)
        try:
            data = await client.analytics.list_panoramas()
            panoramas = [AnalyticsPanorama(**p) for p in data]
            return ListPanoramasResponse(results=panoramas, total_count=len(panoramas))
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("list panoramas", e)

    @mcp.tool(
        title="Get Analytics Panorama",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_get_panorama(
        panorama_id: int, ctx: Context
    ) -> GetPanoramaResponse:
        """Get details of a specific Analytics panorama (dashboard).

        Args:
            panorama_id: Panorama ID
        """
        client = await get_client(ctx)
        try:
            data = await client.analytics.get_panorama(panorama_id)
            panorama = AnalyticsPanorama(**data)
            return GetPanoramaResponse(results=[panorama])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("get panorama", e)

    @mcp.tool(
        title="Create Analytics Panorama",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_create_panorama(
        name: str,
        ctx: Context,
        parent: int | None = None,
    ) -> CreatePanoramaResponse:
        """Create a new Analytics panorama (dashboard).

        Args:
            name: Panorama name
            parent: Optional parent folder ID
        """
        client = await get_client(ctx)
        try:
            fields: dict[str, Any] = {"name": name}
            if parent is not None:
                fields["parent"] = parent
            data = await client.analytics.create_panorama(**fields)
            panorama = AnalyticsPanorama(**data)
            return CreatePanoramaResponse(results=[panorama])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("create panorama", e)

    @mcp.tool(
        title="Update Analytics Panorama",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_update_panorama(
        panorama_id: int,
        panorama_data: dict,
        ctx: Context,
    ) -> UpdatePanoramaResponse:
        """Update an Analytics panorama's configuration.

        Args:
            panorama_id: Panorama ID
            panorama_data: Dict of fields to update
        """
        client = await get_client(ctx)
        try:
            data = await client.analytics.update_panorama(panorama_id, **panorama_data)
            panorama = AnalyticsPanorama(**data)
            return UpdatePanoramaResponse(results=[panorama])
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("update panorama", e)

    @mcp.tool(
        title="Delete Analytics Panorama",
        annotations=ToolAnnotations(
            destructiveHint=True, idempotentHint=True, openWorldHint=True
        ),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_delete_panorama(
        panorama_id: int, ctx: Context
    ) -> DeletePanoramaResponse:
        """Delete an Analytics panorama permanently.

        Args:
            panorama_id: Panorama ID
        """
        client = await get_client(ctx)
        try:
            await client.analytics.delete_panorama(panorama_id)
            return DeletePanoramaResponse(message=f"Panorama {panorama_id} deleted")
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("delete panorama", e)

    # --- Data Operations (v3 API) ---

    @mcp.tool(
        title="Get Analytics Data",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_get_data(report_id: int, ctx: Context) -> GetDataResponse:
        """Get data records for an Analytics report.

        Args:
            report_id: Report ID
        """
        client = await get_client(ctx)
        try:
            data = await client.analytics.get_data(report_id)
            records = data.get("data", []) if isinstance(data, dict) else []
            return GetDataResponse(results=records)
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("get data", e)

    @mcp.tool(
        title="Add Analytics Data",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_add_data(
        dataset_id: int,
        records: list[dict],
        ctx: Context,
    ) -> AddDataResponse:
        """Add data records to an Analytics dataset (v3 API).

        Args:
            dataset_id: Dataset ID
            records: List of data records, each with dimension1, dimension2, and value
        """
        client = await get_client(ctx)
        try:
            await client.analytics.add_data(dataset_id, records)
            return AddDataResponse(
                message=f"{len(records)} record(s) added to dataset {dataset_id}"
            )
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("add data", e)

    @mcp.tool(
        title="Delete Analytics Data",
        annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_delete_data(
        dataset_id: int,
        records: list[dict],
        ctx: Context,
    ) -> DeleteDataResponse:
        """Delete data records from an Analytics dataset (v3 API).

        Args:
            dataset_id: Dataset ID
            records: List of records to delete, each with dimension1 and dimension2
        """
        client = await get_client(ctx)
        try:
            await client.analytics.delete_data(dataset_id, records)
            return DeleteDataResponse(
                message=f"{len(records)} record(s) deleted from dataset {dataset_id}"
            )
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("delete data", e)

    # --- Dataloads ---

    @mcp.tool(
        title="List Analytics Dataloads",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_list_dataloads(ctx: Context) -> ListDataloadsResponse:
        """List all configured Analytics dataloads (scheduled data imports)."""
        client = await get_client(ctx)
        try:
            data = await client.analytics.list_dataloads()
            dataloads = [AnalyticsDataload(**d) for d in data]
            return ListDataloadsResponse(results=dataloads, total_count=len(dataloads))
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("list dataloads", e)

    @mcp.tool(
        title="Execute Analytics Dataload",
        annotations=ToolAnnotations(openWorldHint=True),
    )
    @require_scopes("analytics.write")
    @instrument_tool
    async def nc_analytics_execute_dataload(
        dataload_id: int, ctx: Context
    ) -> ExecuteDataloadResponse:
        """Trigger execution of an Analytics dataload.

        Args:
            dataload_id: Dataload ID to execute
        """
        client = await get_client(ctx)
        try:
            await client.analytics.execute_dataload(dataload_id)
            return ExecuteDataloadResponse(
                message=f"Dataload {dataload_id} execution triggered"
            )
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("execute dataload", e)

    # --- Datasources ---

    @mcp.tool(
        title="List Analytics Datasources",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("analytics.read")
    @instrument_tool
    async def nc_analytics_list_datasources(ctx: Context) -> ListDatasourcesResponse:
        """List available Analytics datasource types."""
        client = await get_client(ctx)
        try:
            data = await client.analytics.list_datasources()
            sources = [AnalyticsDatasource(**s) for s in data]
            return ListDatasourcesResponse(results=sources, total_count=len(sources))
        except (RequestError, HTTPStatusError) as e:
            raise _handle_error("list datasources", e)
