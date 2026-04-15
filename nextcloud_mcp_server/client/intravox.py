"""Client for Nextcloud IntraVox app operations."""

import logging
from typing import Any

from .base import BaseNextcloudClient

logger = logging.getLogger(__name__)


class IntravoxClient(BaseNextcloudClient):
    """Client for Nextcloud IntraVox (intranet pages) app operations.

    IntraVox uses OCS routes for core pages/media CRUD (Basic Auth compatible)
    and internal routes for search, comments, navigation, and page tree.
    """

    app_name = "intravox"
    OCS_API_BASE = "/ocs/v2.php/apps/intravox/api/v1"
    INTERNAL_API_BASE = "/apps/intravox/api"

    _OCS_HEADERS = {
        "OCS-APIRequest": "true",
        "Accept": "application/json",
    }

    async def _make_ocs_request(
        self, method: str, url: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Make an OCS API request with proper headers and response unwrapping.

        Args:
            method: HTTP method
            url: OCS endpoint URL (relative to OCS_API_BASE)
            **kwargs: Additional request params (json, data, params, etc.)

        Returns:
            The unwrapped OCS data payload

        Raises:
            RuntimeError: If OCS meta statuscode indicates an error
            HTTPStatusError: On HTTP-level errors
        """
        headers = dict(self._OCS_HEADERS)
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        response = await self._make_request(
            method, f"{self.OCS_API_BASE}{url}", headers=headers, **kwargs
        )
        data = response.json()

        ocs_status = data.get("ocs", {}).get("meta", {}).get("statuscode", 0)
        if ocs_status not in (100, 200):
            ocs_message = (
                data.get("ocs", {}).get("meta", {}).get("message", "Unknown error")
            )
            raise RuntimeError(f"OCS API error (code {ocs_status}): {ocs_message}")

        return data.get("ocs", {}).get("data", {})

    # --- Pages (OCS) ---

    async def list_pages(self) -> list[dict[str, Any]]:
        """List all accessible pages.

        Returns:
            List of page dicts
        """
        data = await self._make_ocs_request("GET", "/pages")
        if isinstance(data, list):
            return data
        return data.get("pages", [data]) if data else []

    async def get_page(self, page_id: str) -> dict[str, Any]:
        """Get a page's content by ID.

        Args:
            page_id: Page unique ID

        Returns:
            Page dict with content, layout, etc.
        """
        return await self._make_ocs_request("GET", f"/pages/{page_id}")

    async def create_page(
        self,
        title: str,
        language: str = "en",
        parent_id: str | None = None,
        layout: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new page.

        Args:
            title: Page title
            language: Language code (default: 'en')
            parent_id: Optional parent page ID for nesting
            layout: Optional layout structure

        Returns:
            Created page dict
        """
        payload: dict[str, Any] = {"title": title, "language": language}
        if parent_id is not None:
            payload["parentId"] = parent_id
        if layout is not None:
            payload["layout"] = layout
        return await self._make_ocs_request("POST", "/pages", json=payload)

    async def update_page(self, page_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a page's content.

        Args:
            page_id: Page unique ID
            data: Page data to update (title, layout, status, etc.)

        Returns:
            Updated page dict
        """
        return await self._make_ocs_request("PUT", f"/pages/{page_id}", json=data)

    async def delete_page(self, page_id: str) -> dict[str, Any]:
        """Delete a page.

        Args:
            page_id: Page unique ID

        Returns:
            Deletion confirmation
        """
        return await self._make_ocs_request("DELETE", f"/pages/{page_id}")

    # --- Media (OCS) ---

    async def list_media(self, page_id: str) -> list[dict[str, Any]]:
        """List media files for a page.

        Args:
            page_id: Page unique ID

        Returns:
            List of media file dicts
        """
        data = await self._make_ocs_request("GET", f"/pages/{page_id}/media")
        if isinstance(data, list):
            return data
        return data.get("files", []) if data else []

    async def upload_media(
        self, page_id: str, filename: str, content: bytes
    ) -> dict[str, Any]:
        """Upload a media file to a page.

        Args:
            page_id: Page unique ID
            filename: File name
            content: File content bytes

        Returns:
            Upload result dict
        """
        return await self._make_ocs_request(
            "POST",
            f"/pages/{page_id}/media",
            data=content,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    async def get_media(self, page_id: str, filename: str) -> bytes:
        """Get a media file's content.

        Args:
            page_id: Page unique ID
            filename: Media file name

        Returns:
            File content bytes
        """
        response = await self._make_request(
            "GET",
            f"{self.OCS_API_BASE}/pages/{page_id}/media/{filename}",
            headers=self._OCS_HEADERS,
        )
        return response.content

    # --- Search (Internal) ---

    async def search_pages(self, query: str) -> list[dict[str, Any]]:
        """Search pages by query.

        Args:
            query: Search query string

        Returns:
            List of matching page dicts
        """
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/search", params={"query": query}
        )
        data = response.json()
        return data if isinstance(data, list) else data.get("results", [])

    # --- Navigation (Internal) ---

    async def get_page_tree(self) -> list[dict[str, Any]]:
        """Get the hierarchical page tree structure.

        Returns:
            Tree structure as list of page nodes
        """
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/pages/tree"
        )
        data = response.json()
        return data if isinstance(data, list) else []

    async def get_navigation(self) -> dict[str, Any]:
        """Get the navigation structure.

        Returns:
            Navigation configuration dict
        """
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/navigation"
        )
        return response.json()

    async def get_breadcrumb(self, page_id: str) -> list[dict[str, Any]]:
        """Get breadcrumb navigation for a page.

        Args:
            page_id: Page unique ID

        Returns:
            List of breadcrumb items from root to page
        """
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/pages/{page_id}/breadcrumb"
        )
        data = response.json()
        return data if isinstance(data, list) else []

    # --- Comments (Internal) ---

    async def get_comments(self, page_id: str) -> list[dict[str, Any]]:
        """Get comments on a page.

        Args:
            page_id: Page unique ID

        Returns:
            List of comment dicts
        """
        response = await self._make_request(
            "GET", f"{self.INTERNAL_API_BASE}/pages/{page_id}/comments"
        )
        data = response.json()
        return data if isinstance(data, list) else data.get("comments", [])

    async def create_comment(self, page_id: str, message: str) -> dict[str, Any]:
        """Add a comment to a page.

        Args:
            page_id: Page unique ID
            message: Comment text

        Returns:
            Created comment dict
        """
        response = await self._make_request(
            "POST",
            f"{self.INTERNAL_API_BASE}/pages/{page_id}/comments",
            json={"message": message},
        )
        return response.json()

    async def update_comment(self, comment_id: int, message: str) -> dict[str, Any]:
        """Update a comment.

        Args:
            comment_id: Comment ID
            message: Updated comment text

        Returns:
            Updated comment dict
        """
        response = await self._make_request(
            "PUT",
            f"{self.INTERNAL_API_BASE}/comments/{comment_id}",
            json={"message": message},
        )
        return response.json()

    async def delete_comment(self, comment_id: int) -> dict[str, Any]:
        """Delete a comment.

        Args:
            comment_id: Comment ID

        Returns:
            Deletion confirmation
        """
        response = await self._make_request(
            "DELETE", f"{self.INTERNAL_API_BASE}/comments/{comment_id}"
        )
        return response.json()
