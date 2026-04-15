"""MCP tools for Nextcloud Agora app."""

import logging

from httpx import HTTPStatusError, RequestError
from mcp.server.fastmcp import Context, FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, ToolAnnotations

from nextcloud_mcp_server.auth import require_scopes
from nextcloud_mcp_server.context import get_client
from nextcloud_mcp_server.models.agora import (
    AgoraComment,
    AgoraInquiry,
    AgoraSuggestion,
    AgoraSupport,
    CreateCommentResponse,
    CreateInquiryResponse,
    CreateSuggestionResponse,
    DeleteInquiryResponse,
    GetInquiryResponse,
    GetInquiryTypesResponse,
    ListCommentsResponse,
    ListInquiriesResponse,
    ListSuggestionsResponse,
    ListSupportsResponse,
    UpdateInquiryResponse,
)
from nextcloud_mcp_server.observability.metrics import instrument_tool

logger = logging.getLogger(__name__)

VALID_INQUIRY_TYPES = {
    "proposal",
    "debate",
    "project",
    "petition",
    "official_response",
    "suggestion",
    "grievance",
}


def configure_agora_tools(mcp: FastMCP):
    """Configure Agora app MCP tools."""

    # --- Inquiries ---

    @mcp.tool(
        title="List Agora Inquiries",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("agora.read")
    @instrument_tool
    async def nc_agora_list_inquiries(ctx: Context) -> ListInquiriesResponse:
        """List all Agora inquiries (proposals, debates, petitions, etc.)."""
        client = await get_client(ctx)
        try:
            data = await client.agora.list_inquiries()
            inquiries = [AgoraInquiry(**i) for i in data]
            return ListInquiriesResponse(results=inquiries, total_count=len(inquiries))
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error listing inquiries: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to list inquiries: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Get Agora Inquiry",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("agora.read")
    @instrument_tool
    async def nc_agora_get_inquiry(inquiry_id: int, ctx: Context) -> GetInquiryResponse:
        """Get a single Agora inquiry by ID.

        Args:
            inquiry_id: The inquiry ID to retrieve
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.get_inquiry(inquiry_id)
            inquiry = AgoraInquiry(**data)
            return GetInquiryResponse(results=[inquiry])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error getting inquiry: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to get inquiry: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Create Agora Inquiry",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_create_inquiry(
        inquiry_type: str,
        title: str,
        ctx: Context,
        description: str | None = None,
    ) -> CreateInquiryResponse:
        """Create a new Agora inquiry.

        Args:
            inquiry_type: Type of inquiry (proposal, debate, project, petition,
                          official_response, suggestion, grievance)
            title: Inquiry title
            description: Optional description text
        """
        if inquiry_type not in VALID_INQUIRY_TYPES:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Invalid inquiry type '{inquiry_type}'. Must be one of: "
                    f"{', '.join(sorted(VALID_INQUIRY_TYPES))}",
                )
            )
        client = await get_client(ctx)
        try:
            data = await client.agora.create_inquiry(
                inquiry_type=inquiry_type, title=title, description=description
            )
            inquiry = AgoraInquiry(**data)
            return CreateInquiryResponse(results=[inquiry])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error creating inquiry: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to create inquiry: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Update Agora Inquiry",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_update_inquiry(
        inquiry_id: int,
        ctx: Context,
        title: str | None = None,
        description: str | None = None,
        access: str | None = None,
        expire: int | None = None,
        allow_comment: bool | None = None,
        allow_suggestions: bool | None = None,
        show_results: str | None = None,
    ) -> UpdateInquiryResponse:
        """Update an Agora inquiry's configuration.

        Args:
            inquiry_id: Inquiry ID to update
            title: New title
            description: New description
            access: Access level ('open' or 'private')
            expire: Expiration unix timestamp (0 = no expiration)
            allow_comment: Enable/disable comments
            allow_suggestions: Enable/disable suggestions
            show_results: When to show results ('always', 'never', 'closed')
        """
        fields = {}
        if title is not None:
            fields["title"] = title
        if description is not None:
            fields["description"] = description
        if access is not None:
            fields["access"] = access
        if expire is not None:
            fields["expire"] = expire
        if allow_comment is not None:
            fields["allowComment"] = allow_comment
        if allow_suggestions is not None:
            fields["allowSuggestions"] = allow_suggestions
        if show_results is not None:
            fields["showResults"] = show_results

        if not fields:
            raise McpError(ErrorData(code=-1, message="No fields to update"))

        client = await get_client(ctx)
        try:
            data = await client.agora.update_inquiry(inquiry_id, **fields)
            inquiry = AgoraInquiry(**data)
            return UpdateInquiryResponse(results=[inquiry])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error updating inquiry: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to update inquiry: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Delete Agora Inquiry",
        annotations=ToolAnnotations(
            destructiveHint=True, idempotentHint=True, openWorldHint=True
        ),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_delete_inquiry(
        inquiry_id: int, ctx: Context
    ) -> DeleteInquiryResponse:
        """Delete an Agora inquiry permanently.

        Args:
            inquiry_id: Inquiry ID to delete
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.delete_inquiry(inquiry_id)
            inquiry = AgoraInquiry(**data)
            return DeleteInquiryResponse(results=[inquiry])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error deleting inquiry: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to delete inquiry: {e.response.status_code}",
                )
            )

    # --- Inquiry Actions ---

    @mcp.tool(
        title="Clone Agora Inquiry",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_clone_inquiry(
        inquiry_id: int, ctx: Context
    ) -> CreateInquiryResponse:
        """Clone an existing Agora inquiry.

        Args:
            inquiry_id: Inquiry ID to clone
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.clone_inquiry(inquiry_id)
            inquiry = AgoraInquiry(**data)
            return CreateInquiryResponse(results=[inquiry])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error cloning inquiry: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to clone inquiry: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Trash Agora Inquiry",
        annotations=ToolAnnotations(openWorldHint=True),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_trash_inquiry(
        inquiry_id: int, ctx: Context
    ) -> UpdateInquiryResponse:
        """Move an Agora inquiry to or remove from trash (toggles).

        Args:
            inquiry_id: Inquiry ID to trash/untrash
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.trash_inquiry(inquiry_id)
            inquiry = AgoraInquiry(**data)
            return UpdateInquiryResponse(results=[inquiry])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error trashing inquiry: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to trash inquiry: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Close Agora Inquiry",
        annotations=ToolAnnotations(openWorldHint=True),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_close_inquiry(
        inquiry_id: int, ctx: Context
    ) -> UpdateInquiryResponse:
        """Close an Agora inquiry (prevents further participation).

        Args:
            inquiry_id: Inquiry ID to close
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.close_inquiry(inquiry_id)
            inquiry = AgoraInquiry(**data)
            return UpdateInquiryResponse(results=[inquiry])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error closing inquiry: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to close inquiry: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Reopen Agora Inquiry",
        annotations=ToolAnnotations(openWorldHint=True),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_reopen_inquiry(
        inquiry_id: int, ctx: Context
    ) -> UpdateInquiryResponse:
        """Reopen a previously closed Agora inquiry.

        Args:
            inquiry_id: Inquiry ID to reopen
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.reopen_inquiry(inquiry_id)
            inquiry = AgoraInquiry(**data)
            return UpdateInquiryResponse(results=[inquiry])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error reopening inquiry: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to reopen inquiry: {e.response.status_code}",
                )
            )

    # --- Comments ---

    @mcp.tool(
        title="List Agora Comments",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("agora.read")
    @instrument_tool
    async def nc_agora_list_comments(
        inquiry_id: int, ctx: Context
    ) -> ListCommentsResponse:
        """List all comments on an Agora inquiry.

        Args:
            inquiry_id: Inquiry ID to get comments for
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.get_comments(inquiry_id)
            comments = [AgoraComment(**c) for c in data]
            return ListCommentsResponse(results=comments, total_count=len(comments))
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error listing comments: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to list comments: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Create Agora Comment",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_create_comment(
        inquiry_id: int, message: str, ctx: Context
    ) -> CreateCommentResponse:
        """Add a comment to an Agora inquiry.

        Args:
            inquiry_id: Inquiry ID to comment on
            message: Comment text
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.create_comment(inquiry_id, message)
            comment = AgoraComment(**data)
            return CreateCommentResponse(results=[comment])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error creating comment: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to create comment: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Delete Agora Comment",
        annotations=ToolAnnotations(
            destructiveHint=True, idempotentHint=True, openWorldHint=True
        ),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_delete_comment(
        comment_id: int, ctx: Context
    ) -> DeleteInquiryResponse:
        """Delete a comment from an Agora inquiry.

        Args:
            comment_id: Comment ID to delete
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.delete_comment(comment_id)
            return DeleteInquiryResponse(results=[AgoraInquiry(**data)])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error deleting comment: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to delete comment: {e.response.status_code}",
                )
            )

    # --- Suggestions ---

    @mcp.tool(
        title="List Agora Suggestions",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("agora.read")
    @instrument_tool
    async def nc_agora_list_suggestions(
        inquiry_id: int, ctx: Context
    ) -> ListSuggestionsResponse:
        """List all suggestions on an Agora inquiry.

        Args:
            inquiry_id: Inquiry ID to get suggestions for
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.get_suggestions(inquiry_id)
            suggestions = [AgoraSuggestion(**s) for s in data]
            return ListSuggestionsResponse(
                results=suggestions, total_count=len(suggestions)
            )
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error listing suggestions: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to list suggestions: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Create Agora Suggestion",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("agora.write")
    @instrument_tool
    async def nc_agora_create_suggestion(
        inquiry_id: int, message: str, ctx: Context
    ) -> CreateSuggestionResponse:
        """Add a suggestion to an Agora inquiry.

        Args:
            inquiry_id: Inquiry ID to add suggestion to
            message: Suggestion text
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.create_suggestion(inquiry_id, message)
            suggestion = AgoraSuggestion(**data)
            return CreateSuggestionResponse(results=[suggestion])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error creating suggestion: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to create suggestion: {e.response.status_code}",
                )
            )

    # --- Supports ---

    @mcp.tool(
        title="List Agora Supports",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("agora.read")
    @instrument_tool
    async def nc_agora_list_supports(
        inquiry_id: int, ctx: Context
    ) -> ListSupportsResponse:
        """List all supports (votes) on an Agora inquiry.

        Args:
            inquiry_id: Inquiry ID to get supports for
        """
        client = await get_client(ctx)
        try:
            data = await client.agora.get_supports(inquiry_id)
            supports = [AgoraSupport(**s) for s in data]
            return ListSupportsResponse(results=supports, total_count=len(supports))
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error listing supports: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to list supports: {e.response.status_code}",
                )
            )

    # --- Inquiry Types ---

    @mcp.tool(
        title="Get Agora Inquiry Types",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("agora.read")
    @instrument_tool
    async def nc_agora_get_inquiry_types(
        ctx: Context,
    ) -> GetInquiryTypesResponse:
        """Get the list of valid Agora inquiry types."""
        client = await get_client(ctx)
        try:
            data = await client.agora.get_inquiry_types()
            return GetInquiryTypesResponse(results=data)
        except RequestError as e:
            raise McpError(
                ErrorData(
                    code=-1, message=f"Network error getting inquiry types: {e!s}"
                )
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to get inquiry types: {e.response.status_code}",
                )
            )
