"""Client for Nextcloud Analytics app operations."""

import logging
from typing import Any

from .base import BaseNextcloudClient

logger = logging.getLogger(__name__)


class AnalyticsClient(BaseNextcloudClient):
    """Client for Nextcloud Analytics app operations.

    Analytics uses internal REST routes for report/dataset/panorama management
    and the v3 external API for data operations.
    """

    app_name = "analytics"
    INTERNAL_API_BASE = "/apps/analytics"
    DATA_API_BASE = "/apps/analytics/api/3.0"

    # --- Reports ---

    async def list_reports(self) -> list[dict[str, Any]]:
        """List all reports."""
        response = await self._make_request("GET", f"{self.INTERNAL_API_BASE}/report")
        return response.json()

    async def get_report(self, report_id: int) -> dict[str, Any]:
        """Get report details.

        Args:
            report_id: Report ID
        """
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/report/{report_id}"
        )
        return response.json()

    async def create_report(self, **fields: Any) -> dict[str, Any]:
        """Create a new report.

        Args:
            **fields: Report configuration fields
        """
        response = await self._make_request(
            "POST", f"{self.INTERNAL_API_BASE}/report", json=fields
        )
        return response.json()

    async def update_report(self, report_id: int, **fields: Any) -> dict[str, Any]:
        """Update a report.

        Args:
            report_id: Report ID
            **fields: Fields to update
        """
        response = await self._make_request(
            "PUT", f"{self.INTERNAL_API_BASE}/report/{report_id}", json=fields
        )
        return response.json()

    async def delete_report(self, report_id: int) -> dict[str, Any]:
        """Delete a report.

        Args:
            report_id: Report ID
        """
        response = await self._make_request(
            "DELETE", f"{self.INTERNAL_API_BASE}/report/{report_id}"
        )
        return response.json()

    async def copy_report(self, report_id: int) -> dict[str, Any]:
        """Copy/duplicate a report.

        Args:
            report_id: Report ID to copy
        """
        response = await self._make_request(
            "POST",
            f"{self.INTERNAL_API_BASE}/report/copy",
            json={"reportId": report_id},
        )
        return response.json()

    # --- Datasets ---

    async def list_datasets(self) -> list[dict[str, Any]]:
        """List all datasets."""
        response = await self._make_request("GET", f"{self.INTERNAL_API_BASE}/dataset")
        return response.json()

    async def get_dataset(self, dataset_id: int) -> dict[str, Any]:
        """Get dataset details.

        Args:
            dataset_id: Dataset ID
        """
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/dataset/{dataset_id}"
        )
        return response.json()

    async def create_dataset(self, **fields: Any) -> dict[str, Any]:
        """Create a new dataset.

        Args:
            **fields: Dataset configuration fields
        """
        response = await self._make_request(
            "POST", f"{self.INTERNAL_API_BASE}/dataset", json=fields
        )
        return response.json()

    async def update_dataset(self, dataset_id: int, **fields: Any) -> dict[str, Any]:
        """Update a dataset.

        Args:
            dataset_id: Dataset ID
            **fields: Fields to update
        """
        response = await self._make_request(
            "PUT", f"{self.INTERNAL_API_BASE}/dataset/{dataset_id}", json=fields
        )
        return response.json()

    async def delete_dataset(self, dataset_id: int) -> dict[str, Any]:
        """Delete a dataset.

        Args:
            dataset_id: Dataset ID
        """
        response = await self._make_request(
            "DELETE", f"{self.INTERNAL_API_BASE}/dataset/{dataset_id}"
        )
        return response.json()

    # --- Panoramas ---

    async def list_panoramas(self) -> list[dict[str, Any]]:
        """List all panoramas (dashboards)."""
        response = await self._make_request("GET", f"{self.INTERNAL_API_BASE}/panorama")
        return response.json()

    async def get_panorama(self, panorama_id: int) -> dict[str, Any]:
        """Get panorama details.

        Args:
            panorama_id: Panorama ID
        """
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/panorama/{panorama_id}"
        )
        return response.json()

    async def create_panorama(self, **fields: Any) -> dict[str, Any]:
        """Create a new panorama (dashboard).

        Args:
            **fields: Panorama configuration fields
        """
        response = await self._make_request(
            "POST", f"{self.INTERNAL_API_BASE}/panorama", json=fields
        )
        return response.json()

    async def update_panorama(self, panorama_id: int, **fields: Any) -> dict[str, Any]:
        """Update a panorama.

        Args:
            panorama_id: Panorama ID
            **fields: Fields to update
        """
        response = await self._make_request(
            "PUT", f"{self.INTERNAL_API_BASE}/panorama/{panorama_id}", json=fields
        )
        return response.json()

    async def delete_panorama(self, panorama_id: int) -> dict[str, Any]:
        """Delete a panorama.

        Args:
            panorama_id: Panorama ID
        """
        response = await self._make_request(
            "DELETE", f"{self.INTERNAL_API_BASE}/panorama/{panorama_id}"
        )
        return response.json()

    # --- Data Operations (v3 API) ---

    async def get_data(self, report_id: int) -> dict[str, Any]:
        """Get data records for a report.

        Args:
            report_id: Report ID
        """
        response = await self._make_request(
            "GET", f"{self.DATA_API_BASE}/data/{report_id}"
        )
        return response.json()

    async def add_data(
        self, dataset_id: int, records: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Add data records to a dataset via v3 API.

        Args:
            dataset_id: Dataset ID
            records: List of data records (each with dimension1, dimension2, value)
        """
        response = await self._make_request(
            "POST",
            f"{self.DATA_API_BASE}/data/{dataset_id}/add",
            json={"data": records},
        )
        return response.json()

    async def delete_data(
        self, dataset_id: int, records: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Delete data records from a dataset via v3 API.

        Args:
            dataset_id: Dataset ID
            records: List of records to delete (each with dimension1, dimension2)
        """
        response = await self._make_request(
            "POST",
            f"{self.DATA_API_BASE}/data/{dataset_id}/delete",
            json={"delete": records},
        )
        return response.json()

    # --- Dataloads ---

    async def list_dataloads(self) -> list[dict[str, Any]]:
        """List all configured dataloads."""
        response = await self._make_request("GET", f"{self.INTERNAL_API_BASE}/dataload")
        return response.json()

    async def execute_dataload(self, dataload_id: int) -> dict[str, Any]:
        """Trigger execution of a dataload.

        Args:
            dataload_id: Dataload ID
        """
        response = await self._make_request(
            "POST",
            f"{self.INTERNAL_API_BASE}/dataload/execute",
            json={"dataloadId": dataload_id},
        )
        return response.json()

    # --- Datasources ---

    async def list_datasources(self) -> list[dict[str, Any]]:
        """List available datasource types."""
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/datasource"
        )
        return response.json()
