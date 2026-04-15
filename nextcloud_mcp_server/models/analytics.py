"""Pydantic models for Nextcloud Analytics app responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseResponse


class AnalyticsReport(BaseModel):
    """Model for an Analytics report."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int | None = Field(None, description="Report ID")
    name: str | None = Field(None, description="Report name")
    type: int | None = Field(None, description="Report type")
    parent: int | None = Field(None, description="Parent folder ID")
    dataset: int | None = Field(None, description="Linked dataset ID")


class AnalyticsDataset(BaseModel):
    """Model for an Analytics dataset."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int | None = Field(None, description="Dataset ID")
    name: str | None = Field(None, description="Dataset name")
    type: int | None = Field(None, description="Dataset type")
    parent: int | None = Field(None, description="Parent folder ID")


class AnalyticsPanorama(BaseModel):
    """Model for an Analytics panorama (dashboard)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int | None = Field(None, description="Panorama ID")
    name: str | None = Field(None, description="Panorama name")
    type: int | None = Field(None, description="Panorama type")
    parent: int | None = Field(None, description="Parent folder ID")


class AnalyticsDataRecord(BaseModel):
    """Model for a data record."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    dimension1: str | None = Field(None, description="First dimension value")
    dimension2: str | None = Field(None, description="Second dimension value")
    value: str | None = Field(None, description="Numeric value (as string)")


class AnalyticsDataload(BaseModel):
    """Model for a dataload configuration."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int | None = Field(None, description="Dataload ID")
    name: str | None = Field(None, description="Dataload name")
    datasource: int | None = Field(None, description="Datasource type")
    dataset: int | None = Field(None, description="Target dataset ID")
    schedule: str | None = Field(None, description="Cron schedule expression")


class AnalyticsDatasource(BaseModel):
    """Model for a datasource type."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int | None = Field(None, description="Datasource type ID")
    name: str | None = Field(None, description="Datasource name")


# --- Response Models ---


class ListReportsResponse(BaseResponse):
    """Response for listing reports."""

    results: list[AnalyticsReport] = Field(description="List of reports")
    total_count: int = Field(description="Total number of reports")


class GetReportResponse(BaseResponse):
    """Response for getting a single report."""

    results: list[AnalyticsReport] = Field(description="Report details")


class CreateReportResponse(BaseResponse):
    """Response for creating a report."""

    results: list[AnalyticsReport] = Field(description="Created report")


class UpdateReportResponse(BaseResponse):
    """Response for updating a report."""

    results: list[AnalyticsReport] = Field(description="Updated report")


class DeleteReportResponse(BaseResponse):
    """Response for deleting a report."""

    message: str = Field(description="Deletion status message")


class ListDatasetsResponse(BaseResponse):
    """Response for listing datasets."""

    results: list[AnalyticsDataset] = Field(description="List of datasets")
    total_count: int = Field(description="Total number of datasets")


class GetDatasetResponse(BaseResponse):
    """Response for getting a single dataset."""

    results: list[AnalyticsDataset] = Field(description="Dataset details")


class CreateDatasetResponse(BaseResponse):
    """Response for creating a dataset."""

    results: list[AnalyticsDataset] = Field(description="Created dataset")


class UpdateDatasetResponse(BaseResponse):
    """Response for updating a dataset."""

    results: list[AnalyticsDataset] = Field(description="Updated dataset")


class DeleteDatasetResponse(BaseResponse):
    """Response for deleting a dataset."""

    message: str = Field(description="Deletion status message")


class ListPanoramasResponse(BaseResponse):
    """Response for listing panoramas."""

    results: list[AnalyticsPanorama] = Field(description="List of panoramas")
    total_count: int = Field(description="Total number of panoramas")


class GetPanoramaResponse(BaseResponse):
    """Response for getting a single panorama."""

    results: list[AnalyticsPanorama] = Field(description="Panorama details")


class CreatePanoramaResponse(BaseResponse):
    """Response for creating a panorama."""

    results: list[AnalyticsPanorama] = Field(description="Created panorama")


class UpdatePanoramaResponse(BaseResponse):
    """Response for updating a panorama."""

    results: list[AnalyticsPanorama] = Field(description="Updated panorama")


class DeletePanoramaResponse(BaseResponse):
    """Response for deleting a panorama."""

    message: str = Field(description="Deletion status message")


class GetDataResponse(BaseResponse):
    """Response for getting data records."""

    results: list[dict[str, Any]] = Field(description="Data records")


class AddDataResponse(BaseResponse):
    """Response for adding data records."""

    message: str = Field(description="Operation status message")


class DeleteDataResponse(BaseResponse):
    """Response for deleting data records."""

    message: str = Field(description="Operation status message")


class ListDataloadsResponse(BaseResponse):
    """Response for listing dataloads."""

    results: list[AnalyticsDataload] = Field(description="List of dataloads")
    total_count: int = Field(description="Total number of dataloads")


class ExecuteDataloadResponse(BaseResponse):
    """Response for executing a dataload."""

    message: str = Field(description="Execution status message")


class ListDatasourcesResponse(BaseResponse):
    """Response for listing datasource types."""

    results: list[AnalyticsDatasource] = Field(description="Available datasource types")
    total_count: int = Field(description="Total number of datasource types")
