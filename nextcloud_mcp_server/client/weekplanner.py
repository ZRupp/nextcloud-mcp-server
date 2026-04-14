"""Client for Nextcloud WeekPlanner app operations."""

import logging
from typing import Any

from .base import BaseNextcloudClient

logger = logging.getLogger(__name__)


class WeekPlannerClient(BaseNextcloudClient):
    """Client for Nextcloud WeekPlanner app operations.

    WeekPlanner stores entire weeks as JSON blobs keyed by (user, year, week).
    There are no per-task endpoints — the whole week is fetched and saved atomically.
    """

    app_name = "weekplanner"
    API_BASE = "/apps/weekplanner"

    async def get_week(self, year: int, week: int) -> dict[str, Any]:
        """Get week data containing tasks organized by day.

        Args:
            year: ISO year number
            week: ISO week number (1-53)

        Returns:
            Dict with 'days' mapping day names to task lists, plus 'updatedAt' timestamp.
            Example: {"days": {"monday": [...], "tuesday": [...]}, "updatedAt": 1234567890}
        """
        response = await self._make_request(
            "GET", f"{self.API_BASE}/week/{year}/{week}"
        )
        return response.json()

    async def put_week(
        self, year: int, week: int, days: dict[str, list[dict[str, Any]]]
    ) -> dict[str, Any]:
        """Save week data (replaces entire week atomically).

        Args:
            year: ISO year number
            week: ISO week number (1-53)
            days: Mapping of day names to task lists

        Returns:
            Dict with 'status' and 'updatedAt' timestamp
        """
        response = await self._make_request(
            "PUT", f"{self.API_BASE}/week/{year}/{week}", json={"days": days}
        )
        return response.json()

    async def get_custom_columns(self) -> dict[str, Any]:
        """Get custom columns and recurring task definitions.

        Returns:
            Dict with 'columns' list and 'recurringTasks' list, plus 'updatedAt'.
        """
        response = await self._make_request("GET", f"{self.API_BASE}/custom-columns")
        return response.json()

    async def put_custom_columns(
        self,
        columns: list[dict[str, Any]],
        recurring_tasks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Save custom columns and recurring task definitions.

        Args:
            columns: List of custom column configs
            recurring_tasks: List of recurring task definitions

        Returns:
            Dict with 'status' and 'updatedAt' timestamp
        """
        response = await self._make_request(
            "PUT",
            f"{self.API_BASE}/custom-columns",
            json={"columns": columns, "recurringTasks": recurring_tasks},
        )
        return response.json()
