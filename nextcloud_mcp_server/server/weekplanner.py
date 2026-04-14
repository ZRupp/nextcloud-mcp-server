"""MCP tools for Nextcloud WeekPlanner app."""

import logging
import uuid

from httpx import HTTPStatusError, RequestError
from mcp.server.fastmcp import Context, FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, ToolAnnotations

from nextcloud_mcp_server.auth import require_scopes
from nextcloud_mcp_server.context import get_client
from nextcloud_mcp_server.models.weekplanner import (
    CustomColumn,
    GetCustomColumnsResponse,
    GetWeekResponse,
    RecurringTaskDefinition,
    UpdateCustomColumnsResponse,
    UpdateWeekResponse,
    WeekPlannerTask,
)
from nextcloud_mcp_server.observability.metrics import instrument_tool

logger = logging.getLogger(__name__)

VALID_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}

VALID_COLORS = {"", "red", "orange", "yellow", "green", "blue", "purple"}


def configure_weekplanner_tools(mcp: FastMCP):
    """Configure WeekPlanner app MCP tools."""

    @mcp.tool(
        title="Get Week Tasks",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("weekplanner.read")
    @instrument_tool
    async def nc_weekplanner_get_week(
        year: int, week: int, ctx: Context
    ) -> GetWeekResponse:
        """Get all tasks for a specific week, organized by day.

        Args:
            year: ISO year number (e.g. 2026)
            week: ISO week number (1-53)
        """
        client = await get_client(ctx)
        try:
            data = await client.weekplanner.get_week(year, week)
            days_raw = data.get("days", {})
            days = {
                day: [WeekPlannerTask(**t) for t in tasks]
                for day, tasks in days_raw.items()
            }
            return GetWeekResponse(
                results=days,
                updated_at=data.get("updatedAt", 0),
            )
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error getting week: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to get week: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Add Task to Week",
        annotations=ToolAnnotations(
            idempotentHint=False,
            openWorldHint=True,
        ),
    )
    @require_scopes("weekplanner.write")
    @instrument_tool
    async def nc_weekplanner_add_task(
        year: int,
        week: int,
        day: str,
        title: str,
        ctx: Context,
        notes: str = "",
        color: str = "",
    ) -> UpdateWeekResponse:
        """Add a new task to a specific day of the week.

        Args:
            year: ISO year number (e.g. 2026)
            week: ISO week number (1-53)
            day: Day of the week (monday, tuesday, ..., sunday)
            title: Task title
            notes: Optional task notes/details
            color: Optional color (red, orange, yellow, green, blue, purple)
        """
        day = day.lower()
        if day not in VALID_DAYS:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Invalid day '{day}'. Must be one of: {', '.join(sorted(VALID_DAYS))}",
                )
            )
        if color and color not in VALID_COLORS:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Invalid color '{color}'. Must be one of: {', '.join(sorted(VALID_COLORS - {''}))}",
                )
            )

        client = await get_client(ctx)
        try:
            data = await client.weekplanner.get_week(year, week)
            days = data.get("days", {})

            new_task = {
                "id": str(uuid.uuid4()),
                "title": title,
                "done": False,
                "notes": notes,
                "recurrence": "",
                "color": color,
            }

            if day not in days:
                days[day] = []
            days[day].append(new_task)

            result = await client.weekplanner.put_week(year, week, days)
            return UpdateWeekResponse(
                message=f"Task '{title}' added to {day}",
                updated_at=result.get("updatedAt", 0),
            )
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error adding task: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to add task: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Update Task in Week",
        annotations=ToolAnnotations(
            idempotentHint=False,
            openWorldHint=True,
        ),
    )
    @require_scopes("weekplanner.write")
    @instrument_tool
    async def nc_weekplanner_update_task(
        year: int,
        week: int,
        task_id: str,
        ctx: Context,
        title: str | None = None,
        notes: str | None = None,
        color: str | None = None,
        recurrence: str | None = None,
    ) -> UpdateWeekResponse:
        """Update an existing task's properties.

        Args:
            year: ISO year number (e.g. 2026)
            week: ISO week number (1-53)
            task_id: UUID of the task to update
            title: New title (omit to keep current)
            notes: New notes (omit to keep current)
            color: New color (omit to keep current)
            recurrence: New recurrence ('', 'daily', 'weekly', 'monthly'; omit to keep current)
        """
        if color is not None and color not in VALID_COLORS:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Invalid color '{color}'. Must be one of: {', '.join(sorted(VALID_COLORS - {''}))}",
                )
            )

        client = await get_client(ctx)
        try:
            data = await client.weekplanner.get_week(year, week)
            days = data.get("days", {})

            found = False
            for day_tasks in days.values():
                for task in day_tasks:
                    if task.get("id") == task_id:
                        if title is not None:
                            task["title"] = title
                        if notes is not None:
                            task["notes"] = notes
                        if color is not None:
                            task["color"] = color
                        if recurrence is not None:
                            task["recurrence"] = recurrence
                        found = True
                        break
                if found:
                    break

            if not found:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Task '{task_id}' not found in week {year}-W{week}",
                    )
                )

            result = await client.weekplanner.put_week(year, week, days)
            return UpdateWeekResponse(
                message=f"Task '{task_id}' updated",
                updated_at=result.get("updatedAt", 0),
            )
        except McpError:
            raise
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error updating task: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to update task: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Complete Task in Week",
        annotations=ToolAnnotations(
            idempotentHint=False,
            openWorldHint=True,
        ),
    )
    @require_scopes("weekplanner.write")
    @instrument_tool
    async def nc_weekplanner_complete_task(
        year: int,
        week: int,
        task_id: str,
        ctx: Context,
        done: bool = True,
    ) -> UpdateWeekResponse:
        """Mark a task as completed or uncompleted.

        Args:
            year: ISO year number (e.g. 2026)
            week: ISO week number (1-53)
            task_id: UUID of the task
            done: True to mark complete, False to uncheck (default True)
        """
        client = await get_client(ctx)
        try:
            data = await client.weekplanner.get_week(year, week)
            days = data.get("days", {})

            found = False
            for day_tasks in days.values():
                for task in day_tasks:
                    if task.get("id") == task_id:
                        task["done"] = done
                        found = True
                        break
                if found:
                    break

            if not found:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Task '{task_id}' not found in week {year}-W{week}",
                    )
                )

            result = await client.weekplanner.put_week(year, week, days)
            status = "completed" if done else "uncompleted"
            return UpdateWeekResponse(
                message=f"Task '{task_id}' marked as {status}",
                updated_at=result.get("updatedAt", 0),
            )
        except McpError:
            raise
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error completing task: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to complete task: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Move Task Between Days",
        annotations=ToolAnnotations(
            idempotentHint=False,
            openWorldHint=True,
        ),
    )
    @require_scopes("weekplanner.write")
    @instrument_tool
    async def nc_weekplanner_move_task(
        year: int,
        week: int,
        task_id: str,
        target_day: str,
        ctx: Context,
    ) -> UpdateWeekResponse:
        """Move a task from one day to another within the same week.

        Args:
            year: ISO year number (e.g. 2026)
            week: ISO week number (1-53)
            task_id: UUID of the task to move
            target_day: Destination day (monday, tuesday, ..., sunday)
        """
        target_day = target_day.lower()
        if target_day not in VALID_DAYS:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Invalid day '{target_day}'. Must be one of: {', '.join(sorted(VALID_DAYS))}",
                )
            )

        client = await get_client(ctx)
        try:
            data = await client.weekplanner.get_week(year, week)
            days = data.get("days", {})

            # Find and remove the task from its current day
            moved_task = None
            source_day = None
            for day_name, day_tasks in days.items():
                for i, task in enumerate(day_tasks):
                    if task.get("id") == task_id:
                        moved_task = day_tasks.pop(i)
                        source_day = day_name
                        break
                if moved_task:
                    break

            if not moved_task:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Task '{task_id}' not found in week {year}-W{week}",
                    )
                )

            # Add to target day
            if target_day not in days:
                days[target_day] = []
            days[target_day].append(moved_task)

            result = await client.weekplanner.put_week(year, week, days)
            return UpdateWeekResponse(
                message=f"Task moved from {source_day} to {target_day}",
                updated_at=result.get("updatedAt", 0),
            )
        except McpError:
            raise
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error moving task: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to move task: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Delete Task from Week",
        annotations=ToolAnnotations(
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    @require_scopes("weekplanner.write")
    @instrument_tool
    async def nc_weekplanner_delete_task(
        year: int,
        week: int,
        task_id: str,
        ctx: Context,
    ) -> UpdateWeekResponse:
        """Delete a task from the week.

        Args:
            year: ISO year number (e.g. 2026)
            week: ISO week number (1-53)
            task_id: UUID of the task to delete
        """
        client = await get_client(ctx)
        try:
            data = await client.weekplanner.get_week(year, week)
            days = data.get("days", {})

            found = False
            for day_tasks in days.values():
                for i, task in enumerate(day_tasks):
                    if task.get("id") == task_id:
                        day_tasks.pop(i)
                        found = True
                        break
                if found:
                    break

            if not found:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Task '{task_id}' not found in week {year}-W{week}",
                    )
                )

            result = await client.weekplanner.put_week(year, week, days)
            return UpdateWeekResponse(
                message=f"Task '{task_id}' deleted",
                updated_at=result.get("updatedAt", 0),
            )
        except McpError:
            raise
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error deleting task: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to delete task: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Get Custom Columns",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("weekplanner.read")
    @instrument_tool
    async def nc_weekplanner_get_custom_columns(
        ctx: Context,
    ) -> GetCustomColumnsResponse:
        """Get custom columns (e.g., 'Someday') and recurring task definitions."""
        client = await get_client(ctx)
        try:
            data = await client.weekplanner.get_custom_columns()
            columns = [CustomColumn(**c) for c in data.get("columns", [])]
            recurring = [
                RecurringTaskDefinition(**r) for r in data.get("recurringTasks", [])
            ]
            return GetCustomColumnsResponse(
                columns=columns,
                recurring_tasks=recurring,
                updated_at=data.get("updatedAt", 0),
            )
        except RequestError as e:
            raise McpError(
                ErrorData(
                    code=-1, message=f"Network error getting custom columns: {e!s}"
                )
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to get custom columns: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Update Custom Columns",
        annotations=ToolAnnotations(
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    @require_scopes("weekplanner.write")
    @instrument_tool
    async def nc_weekplanner_update_custom_columns(
        columns: list[dict],
        ctx: Context,
        recurring_tasks: list[dict] | None = None,
    ) -> UpdateCustomColumnsResponse:
        """Update custom columns and recurring task definitions.

        Args:
            columns: List of column objects with 'id', 'title', and 'tasks' fields
            recurring_tasks: Optional list of recurring task definitions
        """
        client = await get_client(ctx)
        try:
            result = await client.weekplanner.put_custom_columns(
                columns=columns,
                recurring_tasks=recurring_tasks or [],
            )
            return UpdateCustomColumnsResponse(
                message="Custom columns updated",
                updated_at=result.get("updatedAt", 0),
            )
        except RequestError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Network error updating custom columns: {e!s}",
                )
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to update custom columns: {e.response.status_code}",
                )
            )
