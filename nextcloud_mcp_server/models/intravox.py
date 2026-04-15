"""Pydantic models for Nextcloud IntraVox app responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseResponse


class IntravoxPage(BaseModel):
    """Model for an IntraVox page."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    unique_id: str | None = Field(None, alias="uniqueId", description="Page UUID")
    title: str = Field(description="Page title")
    language: str | None = Field(None, description="Language code (e.g., 'en')")
    status: str | None = Field(None, description="Page status: 'draft' or 'published'")
    layout: dict[str, Any] | None = Field(
        None, description="Page layout structure (rows, columns, widgets)"
    )


class IntravoxPageSummary(BaseModel):
    """Lightweight page model for list responses."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    unique_id: str | None = Field(None, alias="uniqueId", description="Page UUID")
    title: str = Field(description="Page title")
    language: str | None = Field(None, description="Language code")
    status: str | None = Field(None, description="Page status")


class IntravoxMediaItem(BaseModel):
    """Model for a media file attached to a page."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    filename: str | None = Field(None, description="File name")
    size: int | None = Field(None, description="File size in bytes")
    mimetype: str | None = Field(None, description="MIME type")


class IntravoxComment(BaseModel):
    """Model for a comment on an IntraVox page."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int | None = Field(None, description="Comment ID")
    message: str = Field(description="Comment text")
    author: str | None = Field(None, description="Author user ID")
    timestamp: int | None = Field(None, description="Comment unix timestamp")


class IntravoxNavItem(BaseModel):
    """Model for a navigation item."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: str | None = Field(None, description="Navigation item title")
    page_id: str | None = Field(None, alias="pageId", description="Linked page ID")
    url: str | None = Field(None, description="External URL (if applicable)")
    children: list[dict[str, Any]] | None = Field(
        None, description="Child navigation items"
    )


class IntravoxBreadcrumb(BaseModel):
    """Model for a breadcrumb navigation item."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: str | None = Field(None, description="Page title")
    page_id: str | None = Field(None, alias="pageId", description="Page ID")


# --- Response Models ---


class ListPagesResponse(BaseResponse):
    """Response for listing pages."""

    results: list[IntravoxPageSummary] = Field(description="List of pages")
    total_count: int = Field(description="Total number of pages")


class GetPageResponse(BaseResponse):
    """Response for getting a single page."""

    results: list[IntravoxPage] = Field(description="Page content (single-item list)")


class CreatePageResponse(BaseResponse):
    """Response for creating a page."""

    results: list[IntravoxPage] = Field(description="Created page")


class UpdatePageResponse(BaseResponse):
    """Response for updating a page."""

    results: list[IntravoxPage] = Field(description="Updated page")


class DeletePageResponse(BaseResponse):
    """Response for deleting a page."""

    message: str = Field(description="Deletion status message")


class SearchPagesResponse(BaseResponse):
    """Response for searching pages."""

    results: list[IntravoxPageSummary] = Field(description="Matching pages")
    total_count: int = Field(description="Number of matches")


class GetPageTreeResponse(BaseResponse):
    """Response for getting the page tree."""

    results: list[dict[str, Any]] = Field(description="Hierarchical page tree")


class GetNavigationResponse(BaseResponse):
    """Response for getting navigation structure."""

    results: list[dict[str, Any]] = Field(description="Navigation items")


class GetBreadcrumbResponse(BaseResponse):
    """Response for getting a page's breadcrumb."""

    results: list[IntravoxBreadcrumb] = Field(
        description="Breadcrumb trail from root to page"
    )


class ListMediaResponse(BaseResponse):
    """Response for listing media files."""

    results: list[IntravoxMediaItem] = Field(description="Media files")
    total_count: int = Field(description="Number of media files")


class UploadMediaResponse(BaseResponse):
    """Response for uploading a media file."""

    message: str = Field(description="Upload status message")


class ListCommentsResponse(BaseResponse):
    """Response for listing comments on a page."""

    results: list[IntravoxComment] = Field(description="Comments")
    total_count: int = Field(description="Number of comments")


class CreateCommentResponse(BaseResponse):
    """Response for creating a comment."""

    results: list[IntravoxComment] = Field(description="Created comment")


class UpdateCommentResponse(BaseResponse):
    """Response for updating a comment."""

    results: list[IntravoxComment] = Field(description="Updated comment")


class DeleteCommentResponse(BaseResponse):
    """Response for deleting a comment."""

    message: str = Field(description="Deletion status message")
