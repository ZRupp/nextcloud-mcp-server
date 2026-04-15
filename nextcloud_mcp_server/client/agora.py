"""Client for Nextcloud Agora app operations."""

import logging
from typing import Any

from .base import BaseNextcloudClient

logger = logging.getLogger(__name__)


class AgoraClient(BaseNextcloudClient):
    """Client for Nextcloud Agora (participatory democracy) app operations.

    Agora manages inquiries (proposals, debates, petitions, projects, etc.)
    organized into families, with comments, suggestions, and supports.
    """

    app_name = "agora"
    API_BASE = "/apps/agora/api/v1.0"

    # --- Inquiries ---

    async def list_inquiries(self) -> list[dict[str, Any]]:
        """Get all inquiries.

        Returns:
            List of inquiry dicts
        """
        response = await self._make_request("GET", f"{self.API_BASE}/agora")
        return response.json()

    async def get_inquiry(self, inquiry_id: int) -> dict[str, Any]:
        """Get a single inquiry by ID.

        Args:
            inquiry_id: Inquiry ID

        Returns:
            Inquiry dict

        Raises:
            HTTPStatusError: 404 if not found, 403 if no access
        """
        response = await self._make_request(
            "GET", f"{self.API_BASE}/inquiry/{inquiry_id}"
        )
        return response.json()

    async def create_inquiry(
        self,
        inquiry_type: str,
        title: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new inquiry.

        Args:
            inquiry_type: Type of inquiry (proposal, debate, project, petition,
                          official_response, suggestion, grievance)
            title: Inquiry title
            description: Optional description

        Returns:
            Created inquiry dict

        Raises:
            HTTPStatusError: 403 if no permission
        """
        payload: dict[str, Any] = {"type": inquiry_type, "title": title}
        if description is not None:
            payload["description"] = description
        response = await self._make_request(
            "POST", f"{self.API_BASE}/inquiry", json=payload
        )
        return response.json()

    async def update_inquiry(self, inquiry_id: int, **fields: Any) -> dict[str, Any]:
        """Update an inquiry's configuration fields.

        Args:
            inquiry_id: Inquiry ID
            **fields: Fields to update (title, description, expire, access,
                      allowComment, allowSuggestions, showResults)

        Returns:
            Updated inquiry dict

        Raises:
            HTTPStatusError: 404 if not found, 409 on conflict
        """
        response = await self._make_request(
            "PUT",
            f"{self.API_BASE}/inquiry/{inquiry_id}",
            json={"inquiry": fields},
        )
        return response.json()

    async def delete_inquiry(self, inquiry_id: int) -> dict[str, Any]:
        """Delete an inquiry.

        Args:
            inquiry_id: Inquiry ID

        Returns:
            Deleted inquiry dict

        Raises:
            HTTPStatusError: 404 if not found, 403 if no permission
        """
        response = await self._make_request(
            "DELETE", f"{self.API_BASE}/inquiry/{inquiry_id}"
        )
        return response.json()

    # --- Inquiry Actions ---

    async def clone_inquiry(self, inquiry_id: int) -> dict[str, Any]:
        """Clone an inquiry.

        Args:
            inquiry_id: Inquiry ID to clone

        Returns:
            Cloned inquiry dict
        """
        response = await self._make_request(
            "POST", f"{self.API_BASE}/inquiry/{inquiry_id}/clone"
        )
        return response.json()

    async def trash_inquiry(self, inquiry_id: int) -> dict[str, Any]:
        """Move an inquiry to or remove from trash.

        Args:
            inquiry_id: Inquiry ID

        Returns:
            Updated inquiry dict
        """
        response = await self._make_request(
            "POST", f"{self.API_BASE}/inquiry/{inquiry_id}/trash"
        )
        return response.json()

    async def close_inquiry(self, inquiry_id: int) -> dict[str, Any]:
        """Close an inquiry (prevents further participation).

        Args:
            inquiry_id: Inquiry ID

        Returns:
            Closed inquiry dict
        """
        response = await self._make_request(
            "PUT", f"{self.API_BASE}/inquiry/{inquiry_id}/close"
        )
        return response.json()

    async def reopen_inquiry(self, inquiry_id: int) -> dict[str, Any]:
        """Reopen a closed inquiry.

        Args:
            inquiry_id: Inquiry ID

        Returns:
            Reopened inquiry dict
        """
        response = await self._make_request(
            "PUT", f"{self.API_BASE}/inquiry/{inquiry_id}/reopen"
        )
        return response.json()

    # --- Inquiry Types ---

    async def get_inquiry_types(self) -> list[dict[str, Any]]:
        """Get valid inquiry types.

        Returns:
            List of valid inquiry type definitions
        """
        response = await self._make_request("GET", f"{self.API_BASE}/enum/inquiry")
        return response.json()

    # --- Comments ---

    async def get_comments(self, inquiry_id: int) -> list[dict[str, Any]]:
        """Get all comments for an inquiry.

        Args:
            inquiry_id: Inquiry ID

        Returns:
            List of comment dicts
        """
        response = await self._make_request(
            "GET", f"{self.API_BASE}/inquiry/{inquiry_id}/comments"
        )
        return response.json()

    async def create_comment(self, inquiry_id: int, message: str) -> dict[str, Any]:
        """Add a comment to an inquiry.

        Args:
            inquiry_id: Inquiry ID
            message: Comment text

        Returns:
            Created comment dict
        """
        response = await self._make_request(
            "POST",
            f"{self.API_BASE}/comment",
            json={"inquiryId": inquiry_id, "message": message},
        )
        return response.json()

    async def delete_comment(self, comment_id: int) -> dict[str, Any]:
        """Delete a comment.

        Args:
            comment_id: Comment ID

        Returns:
            Deleted comment dict
        """
        response = await self._make_request(
            "DELETE", f"{self.API_BASE}/comment/{comment_id}"
        )
        return response.json()

    # --- Suggestions ---

    async def get_suggestions(self, inquiry_id: int) -> list[dict[str, Any]]:
        """Get all suggestions for an inquiry.

        Args:
            inquiry_id: Inquiry ID

        Returns:
            List of suggestion dicts
        """
        response = await self._make_request(
            "GET", f"{self.API_BASE}/inquiry/{inquiry_id}/suggestions"
        )
        return response.json()

    async def create_suggestion(self, inquiry_id: int, message: str) -> dict[str, Any]:
        """Add a suggestion to an inquiry.

        Args:
            inquiry_id: Inquiry ID
            message: Suggestion text

        Returns:
            Created suggestion dict
        """
        response = await self._make_request(
            "POST",
            f"{self.API_BASE}/suggestion",
            json={"inquiryId": inquiry_id, "message": message},
        )
        return response.json()

    # --- Supports ---

    async def get_supports(self, inquiry_id: int) -> list[dict[str, Any]]:
        """Get all supports (votes) for an inquiry.

        Args:
            inquiry_id: Inquiry ID

        Returns:
            List of support dicts
        """
        response = await self._make_request(
            "GET", f"{self.API_BASE}/inquiry/{inquiry_id}/supports"
        )
        return response.json()
