"""Pydantic models for Nextcloud WeekPlanner app responses."""

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseResponse


class WeekPlannerTask(BaseModel):
    """Model for a single task in the week planner."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="Task UUID")
    title: str = Field(description="Task title")
    done: bool = Field(False, description="Whether the task is completed")
    notes: str = Field("", description="Task notes/details")
    recurrence: str = Field(
        "", description="Recurrence pattern: '', 'daily', 'weekly', or 'monthly'"
    )
    color: str = Field(
        "",
        description="Task color: '', 'red', 'orange', 'yellow', 'green', 'blue', or 'purple'",
    )
    recurring_source_id: str | None = Field(
        None,
        alias="recurringSourceId",
        description="ID of the recurring task definition that generated this task",
    )
    recurring_original_date: str | None = Field(
        None,
        alias="recurringOriginalDate",
        description="Original date for this recurring task instance",
    )


class CustomColumn(BaseModel):
    """Model for a custom column (e.g., 'Someday' sidebar column)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="Column ID (e.g., 'custom_1')")
    title: str = Field("", description="Column title")
    tasks: list[WeekPlannerTask] = Field(
        default_factory=list, description="Tasks in this column"
    )


class RecurringTaskDefinition(BaseModel):
    """Model for a recurring task definition."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="Definition ID")
    title: str = Field(description="Task title")
    notes: str = Field("", description="Task notes")
    recurrence: str = Field(
        description="Recurrence type: 'daily', 'weekly', or 'monthly'"
    )
    start_date: str = Field(alias="startDate", description="Start date (ISO format)")
    end_date: str = Field(alias="endDate", description="End date (ISO format)")
    day_of_week: int = Field(
        alias="dayOfWeek", description="Day of week (0=Monday, 6=Sunday)"
    )
    day_of_month: int = Field(alias="dayOfMonth", description="Day of month (1-31)")
    exception_dates: list[str] = Field(
        default_factory=list,
        alias="exceptionDates",
        description="Dates to skip this recurring task",
    )


class GetWeekResponse(BaseResponse):
    """Response for getting a week's tasks."""

    results: dict[str, list[WeekPlannerTask]] = Field(
        description="Mapping of day names to task lists"
    )
    updated_at: int = Field(description="Last update timestamp (unix)")


class UpdateWeekResponse(BaseResponse):
    """Response for updating a week's tasks."""

    message: str = Field(description="Status message")
    updated_at: int = Field(description="New update timestamp (unix)")


class GetCustomColumnsResponse(BaseResponse):
    """Response for getting custom columns."""

    columns: list[CustomColumn] = Field(description="Custom columns")
    recurring_tasks: list[RecurringTaskDefinition] = Field(
        default_factory=list, description="Recurring task definitions"
    )
    updated_at: int = Field(description="Last update timestamp (unix)")


class UpdateCustomColumnsResponse(BaseResponse):
    """Response for updating custom columns."""

    message: str = Field(description="Status message")
    updated_at: int = Field(description="New update timestamp (unix)")
