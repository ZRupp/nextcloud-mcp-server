"""Pydantic models for Nextcloud Agora app responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseResponse


class AgoraInquiry(BaseModel):
    """Model for an Agora inquiry (proposal, debate, petition, etc.)."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(description="Inquiry ID")
    title: str = Field(description="Inquiry title")
    description: str | None = Field(None, description="Inquiry description")
    type: str = Field(
        description="Inquiry type (proposal, debate, project, petition, "
        "official_response, suggestion, grievance)"
    )
    access: str | None = Field(None, description="Access level: 'open' or 'private'")
    owner: str | None = Field(None, description="Owner user ID")
    created: int | None = Field(None, description="Creation unix timestamp")
    expire: int | None = Field(
        None, description="Expiration unix timestamp (0 = no expiration)"
    )
    allow_comment: bool | None = Field(
        None, alias="allowComment", description="Whether comments are enabled"
    )
    allow_suggestions: bool | None = Field(
        None, alias="allowSuggestions", description="Whether suggestions are enabled"
    )
    show_results: str | None = Field(
        None,
        alias="showResults",
        description="When to show results: 'always', 'never', 'closed'",
    )


class AgoraComment(BaseModel):
    """Model for a comment on an inquiry."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(description="Comment ID")
    inquiry_id: int | None = Field(
        None, alias="inquiryId", description="Parent inquiry ID"
    )
    user_id: str | None = Field(None, alias="userId", description="Commenter user ID")
    message: str = Field(description="Comment text")
    timestamp: int | None = Field(None, description="Comment unix timestamp")


class AgoraSuggestion(BaseModel):
    """Model for a suggestion on an inquiry."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(description="Suggestion ID")
    inquiry_id: int | None = Field(
        None, alias="inquiryId", description="Parent inquiry ID"
    )
    message: str = Field(description="Suggestion text")


class AgoraSupport(BaseModel):
    """Model for a support vote on an inquiry."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(description="Support ID")
    inquiry_id: int | None = Field(
        None, alias="inquiryId", description="Parent inquiry ID"
    )
    user_id: str | None = Field(None, alias="userId", description="Supporter user ID")
    status: str | None = Field(None, description="Support status (e.g. 'supported')")


class AgoraInquiryType(BaseModel):
    """Model for a valid inquiry type definition."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Agora may return different fields depending on version;
    # use extra="allow" to capture them all
    name: str | None = Field(None, description="Type name")
    value: str | None = Field(None, description="Type value")


# --- Response Models ---


class ListInquiriesResponse(BaseResponse):
    """Response for listing inquiries."""

    results: list[AgoraInquiry] = Field(description="List of inquiries")
    total_count: int = Field(description="Total number of inquiries")


class GetInquiryResponse(BaseResponse):
    """Response for getting a single inquiry."""

    results: list[AgoraInquiry] = Field(description="Inquiry (single-item list)")


class CreateInquiryResponse(BaseResponse):
    """Response for creating an inquiry."""

    results: list[AgoraInquiry] = Field(description="Created inquiry")


class UpdateInquiryResponse(BaseResponse):
    """Response for updating an inquiry."""

    results: list[AgoraInquiry] = Field(description="Updated inquiry")


class DeleteInquiryResponse(BaseResponse):
    """Response for deleting an inquiry."""

    results: list[AgoraInquiry] = Field(description="Deleted inquiry")


class ListCommentsResponse(BaseResponse):
    """Response for listing comments on an inquiry."""

    results: list[AgoraComment] = Field(description="List of comments")
    total_count: int = Field(description="Total number of comments")


class CreateCommentResponse(BaseResponse):
    """Response for creating a comment."""

    results: list[AgoraComment] = Field(description="Created comment")


class ListSuggestionsResponse(BaseResponse):
    """Response for listing suggestions on an inquiry."""

    results: list[AgoraSuggestion] = Field(description="List of suggestions")
    total_count: int = Field(description="Total number of suggestions")


class CreateSuggestionResponse(BaseResponse):
    """Response for creating a suggestion."""

    results: list[AgoraSuggestion] = Field(description="Created suggestion")


class ListSupportsResponse(BaseResponse):
    """Response for listing supports on an inquiry."""

    results: list[AgoraSupport] = Field(description="List of supports")
    total_count: int = Field(description="Total number of supports")


class GetInquiryTypesResponse(BaseResponse):
    """Response for listing valid inquiry types."""

    results: list[dict[str, Any]] = Field(
        description="List of valid inquiry type definitions"
    )
