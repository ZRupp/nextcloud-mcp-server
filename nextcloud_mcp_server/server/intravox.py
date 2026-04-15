"""MCP tools for Nextcloud IntraVox app."""

import logging

from httpx import HTTPStatusError, RequestError
from mcp.server.fastmcp import Context, FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, ToolAnnotations

from nextcloud_mcp_server.auth import require_scopes
from nextcloud_mcp_server.context import get_client
from nextcloud_mcp_server.models.intravox import (
    CreateCommentResponse,
    CreatePageResponse,
    DeleteCommentResponse,
    DeletePageResponse,
    GetBreadcrumbResponse,
    GetNavigationResponse,
    GetPageResponse,
    GetPageTreeResponse,
    IntravoxBreadcrumb,
    IntravoxComment,
    IntravoxMediaItem,
    IntravoxPage,
    IntravoxPageSummary,
    ListCommentsResponse,
    ListMediaResponse,
    ListPagesResponse,
    SearchPagesResponse,
    UpdateCommentResponse,
    UpdatePageResponse,
    UploadMediaResponse,
)
from nextcloud_mcp_server.observability.metrics import instrument_tool

logger = logging.getLogger(__name__)


def configure_intravox_tools(mcp: FastMCP):
    """Configure IntraVox app MCP tools."""

    # --- Pages (OCS) ---

    @mcp.tool(
        title="List IntraVox Pages",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("intravox.read")
    @instrument_tool
    async def nc_intravox_list_pages(ctx: Context) -> ListPagesResponse:
        """List all accessible IntraVox intranet pages."""
        client = await get_client(ctx)
        try:
            data = await client.intravox.list_pages()
            pages = [IntravoxPageSummary(**p) for p in data]
            return ListPagesResponse(results=pages, total_count=len(pages))
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error listing pages: {e!s}")
            )
        except (HTTPStatusError, RuntimeError) as e:
            raise McpError(ErrorData(code=-1, message=f"Failed to list pages: {e!s}"))

    @mcp.tool(
        title="Get IntraVox Page",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("intravox.read")
    @instrument_tool
    async def nc_intravox_get_page(page_id: str, ctx: Context) -> GetPageResponse:
        """Get an IntraVox page's full content including layout and widgets.

        Args:
            page_id: Page unique ID
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.get_page(page_id)
            page = IntravoxPage(**data)
            return GetPageResponse(results=[page])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error getting page: {e!s}")
            )
        except (HTTPStatusError, RuntimeError) as e:
            raise McpError(ErrorData(code=-1, message=f"Failed to get page: {e!s}"))

    @mcp.tool(
        title="Create IntraVox Page",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("intravox.write")
    @instrument_tool
    async def nc_intravox_create_page(
        title: str,
        ctx: Context,
        language: str = "en",
        parent_id: str | None = None,
    ) -> CreatePageResponse:
        """Create a new IntraVox intranet page.

        Args:
            title: Page title
            language: Language code (default: 'en')
            parent_id: Optional parent page ID for nesting
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.create_page(
                title=title, language=language, parent_id=parent_id
            )
            page = IntravoxPage(**data)
            return CreatePageResponse(results=[page])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error creating page: {e!s}")
            )
        except (HTTPStatusError, RuntimeError) as e:
            raise McpError(ErrorData(code=-1, message=f"Failed to create page: {e!s}"))

    @mcp.tool(
        title="Update IntraVox Page",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("intravox.write")
    @instrument_tool
    async def nc_intravox_update_page(
        page_id: str,
        page_data: dict,
        ctx: Context,
    ) -> UpdatePageResponse:
        """Update an IntraVox page's content, layout, or status.

        Args:
            page_id: Page unique ID
            page_data: Dict with fields to update (title, layout, status, etc.)
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.update_page(page_id, page_data)
            page = IntravoxPage(**data)
            return UpdatePageResponse(results=[page])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error updating page: {e!s}")
            )
        except (HTTPStatusError, RuntimeError) as e:
            raise McpError(ErrorData(code=-1, message=f"Failed to update page: {e!s}"))

    @mcp.tool(
        title="Delete IntraVox Page",
        annotations=ToolAnnotations(
            destructiveHint=True, idempotentHint=True, openWorldHint=True
        ),
    )
    @require_scopes("intravox.write")
    @instrument_tool
    async def nc_intravox_delete_page(page_id: str, ctx: Context) -> DeletePageResponse:
        """Delete an IntraVox page permanently.

        Args:
            page_id: Page unique ID
        """
        client = await get_client(ctx)
        try:
            await client.intravox.delete_page(page_id)
            return DeletePageResponse(message=f"Page '{page_id}' deleted")
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error deleting page: {e!s}")
            )
        except (HTTPStatusError, RuntimeError) as e:
            raise McpError(ErrorData(code=-1, message=f"Failed to delete page: {e!s}"))

    # --- Search (Internal) ---

    @mcp.tool(
        title="Search IntraVox Pages",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("intravox.read")
    @instrument_tool
    async def nc_intravox_search_pages(query: str, ctx: Context) -> SearchPagesResponse:
        """Search IntraVox pages by content or title.

        Args:
            query: Search query string
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.search_pages(query)
            pages = [IntravoxPageSummary(**p) for p in data]
            return SearchPagesResponse(results=pages, total_count=len(pages))
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error searching pages: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to search pages: {e.response.status_code}",
                )
            )

    # --- Navigation (Internal) ---

    @mcp.tool(
        title="Get IntraVox Page Tree",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("intravox.read")
    @instrument_tool
    async def nc_intravox_get_page_tree(ctx: Context) -> GetPageTreeResponse:
        """Get the hierarchical page tree structure."""
        client = await get_client(ctx)
        try:
            data = await client.intravox.get_page_tree()
            return GetPageTreeResponse(results=data)
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error getting page tree: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to get page tree: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Get IntraVox Navigation",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("intravox.read")
    @instrument_tool
    async def nc_intravox_get_navigation(ctx: Context) -> GetNavigationResponse:
        """Get the IntraVox navigation structure."""
        client = await get_client(ctx)
        try:
            data = await client.intravox.get_navigation()
            items = data if isinstance(data, list) else data.get("items", [data])
            return GetNavigationResponse(results=items)
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error getting navigation: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to get navigation: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Get IntraVox Breadcrumb",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("intravox.read")
    @instrument_tool
    async def nc_intravox_get_breadcrumb(
        page_id: str, ctx: Context
    ) -> GetBreadcrumbResponse:
        """Get breadcrumb navigation trail for a page.

        Args:
            page_id: Page unique ID
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.get_breadcrumb(page_id)
            crumbs = [IntravoxBreadcrumb(**c) for c in data]
            return GetBreadcrumbResponse(results=crumbs)
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error getting breadcrumb: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to get breadcrumb: {e.response.status_code}",
                )
            )

    # --- Media (OCS) ---

    @mcp.tool(
        title="List IntraVox Media",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("intravox.read")
    @instrument_tool
    async def nc_intravox_list_media(page_id: str, ctx: Context) -> ListMediaResponse:
        """List media files attached to an IntraVox page.

        Args:
            page_id: Page unique ID
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.list_media(page_id)
            media = [IntravoxMediaItem(**m) for m in data]
            return ListMediaResponse(results=media, total_count=len(media))
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error listing media: {e!s}")
            )
        except (HTTPStatusError, RuntimeError) as e:
            raise McpError(ErrorData(code=-1, message=f"Failed to list media: {e!s}"))

    @mcp.tool(
        title="Upload IntraVox Media",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("intravox.write")
    @instrument_tool
    async def nc_intravox_upload_media(
        page_id: str,
        filename: str,
        content_base64: str,
        ctx: Context,
    ) -> UploadMediaResponse:
        """Upload a media file to an IntraVox page.

        Args:
            page_id: Page unique ID
            filename: File name (e.g. 'logo.png')
            content_base64: Base64-encoded file content
        """
        import base64  # noqa: PLC0415

        client = await get_client(ctx)
        try:
            content = base64.b64decode(content_base64)
            await client.intravox.upload_media(page_id, filename, content)
            return UploadMediaResponse(
                message=f"Media '{filename}' uploaded to page '{page_id}'"
            )
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error uploading media: {e!s}")
            )
        except (HTTPStatusError, RuntimeError) as e:
            raise McpError(ErrorData(code=-1, message=f"Failed to upload media: {e!s}"))

    # --- Comments (Internal) ---

    @mcp.tool(
        title="List IntraVox Comments",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    @require_scopes("intravox.read")
    @instrument_tool
    async def nc_intravox_get_comments(
        page_id: str, ctx: Context
    ) -> ListCommentsResponse:
        """List comments on an IntraVox page.

        Args:
            page_id: Page unique ID
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.get_comments(page_id)
            comments = [IntravoxComment(**c) for c in data]
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
        title="Create IntraVox Comment",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("intravox.write")
    @instrument_tool
    async def nc_intravox_create_comment(
        page_id: str, message: str, ctx: Context
    ) -> CreateCommentResponse:
        """Add a comment to an IntraVox page.

        Args:
            page_id: Page unique ID
            message: Comment text
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.create_comment(page_id, message)
            comment = IntravoxComment(**data)
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
        title="Update IntraVox Comment",
        annotations=ToolAnnotations(idempotentHint=False, openWorldHint=True),
    )
    @require_scopes("intravox.write")
    @instrument_tool
    async def nc_intravox_update_comment(
        comment_id: int, message: str, ctx: Context
    ) -> UpdateCommentResponse:
        """Edit an existing comment on an IntraVox page.

        Args:
            comment_id: Comment ID
            message: Updated comment text
        """
        client = await get_client(ctx)
        try:
            data = await client.intravox.update_comment(comment_id, message)
            comment = IntravoxComment(**data)
            return UpdateCommentResponse(results=[comment])
        except RequestError as e:
            raise McpError(
                ErrorData(code=-1, message=f"Network error updating comment: {e!s}")
            )
        except HTTPStatusError as e:
            raise McpError(
                ErrorData(
                    code=-1,
                    message=f"Failed to update comment: {e.response.status_code}",
                )
            )

    @mcp.tool(
        title="Delete IntraVox Comment",
        annotations=ToolAnnotations(
            destructiveHint=True, idempotentHint=True, openWorldHint=True
        ),
    )
    @require_scopes("intravox.write")
    @instrument_tool
    async def nc_intravox_delete_comment(
        comment_id: int, ctx: Context
    ) -> DeleteCommentResponse:
        """Delete a comment from an IntraVox page.

        Args:
            comment_id: Comment ID
        """
        client = await get_client(ctx)
        try:
            await client.intravox.delete_comment(comment_id)
            return DeleteCommentResponse(message=f"Comment {comment_id} deleted")
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
