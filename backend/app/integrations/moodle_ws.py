"""Moodle Web Services client (C-09).

HTTP client for Moodle WS API with retry, timeout, and error mapping.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class MoodleWSError(Exception):
    """Raised when Moodle WS is unreachable or returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class MoodleWSClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout))

    def _ws_url(self, func: str, **kwargs: Any) -> str:
        params = [("wstoken", self._token), ("moodlewsrestformat", "json")]
        for k, v in kwargs.items():
            params.append((k, str(v)))
        query = "&".join(f"{k}={v}" for k, v in params)
        return f"{self._base_url}/webservice/rest/server.php?{query}&wsfunction={func}"

    @retry(
        retry=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _get(self, url: str) -> dict[str, Any]:
        logger.debug("Moodle WS GET: %s", url)
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("exception"):
                raise MoodleWSError(
                    data.get("message", "Moodle WS error"),
                    status_code=response.status_code,
                )
            return data
        except httpx.TimeoutException as e:
            logger.warning("Moodle WS timeout: %s", e)
            raise MoodleWSError(f"Moodle no respondió en {self._timeout}s") from e
        except httpx.HTTPStatusError as e:
            logger.warning("Moodle WS HTTP error: %s", e)
            raise MoodleWSError(
                f"Moodle WS error {e.response.status_code}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            logger.warning("Moodle WS connection error: %s", e)
            raise MoodleWSError(f"No se pudo conectar a Moodle: {e}") from e

    async def get_users(self, course_id: int) -> list[dict[str, Any]]:
        """Get enrolled users for a course."""
        url = self._ws_url("core_enrol_get_enrolled_users", courseid=course_id)
        result = await self._get(url)
        users: list[dict[str, Any]] = []
        for u in result if isinstance(result, list) else []:
            users.append({
                "id": u.get("id"),
                "firstname": u.get("firstname"),
                "lastname": u.get("lastname"),
                "email": u.get("email"),
            })
        return users

    async def get_activities(self, course_id: int) -> list[dict[str, Any]]:
        """Get activities/modules for a course."""
        url = self._ws_url("local_ws_get_activities", courseid=course_id)
        try:
            result = await self._get(url)
        except MoodleWSError:
            # Fallback: try core_course_get_contents
            url = self._ws_url("core_course_get_contents", courseid=course_id)
            result = await self._get(url)
        activities: list[dict[str, Any]] = []
        if isinstance(result, list):
            for module in result:
                for mod in module.get("modules", []):
                    activities.append({
                        "id": mod.get("id"),
                        "name": mod.get("name"),
                        "type": mod.get("modname"),
                        "duedate": mod.get("due"),
                    })
        return activities

    async def sync_enrollments(
        self, course_id: int, user_ids: list[int],
    ) -> bool:
        """Sync user enrollments to Moodle (enrol users)."""
        for uid in user_ids:
            url = self._ws_url(
                "enrol_manual_enrol_users",
                enrolments=[{"roleid": 5, "userid": uid, "courseid": course_id}],
            )
            await self._get(url)
        return True

    async def close(self) -> None:
        await self._client.aclose()