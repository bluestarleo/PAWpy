"""Asset — a node in the PAW content store (folder, book/dashboard, view…).

Maps the properties documented for the Content Services API
(``/pacontent/v1/Assets``): ``id``, ``type``, ``name``, ``path``,
``description``, ``content``, ``custom_properties`` plus the read-only system
timestamps.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PAWpy.Objects.TM1Object import PAWObject


class Asset(PAWObject):
    @property
    def id(self) -> Optional[str]:
        return self._body.get("id")

    @property
    def type(self) -> Optional[str]:
        return self._body.get("type")

    @property
    def name(self) -> Optional[str]:
        return self._body.get("name")

    @property
    def path(self) -> Optional[str]:
        return self._body.get("path")

    @property
    def description(self) -> Optional[str]:
        return self._body.get("description")

    @property
    def content(self) -> Any:
        return self._body.get("content")

    @property
    def custom_properties(self) -> Dict[str, Any]:
        return self._body.get("custom_properties") or {}

    @property
    def is_folder(self) -> bool:
        return (self._body.get("type") or "").lower() == "folder"

    @property
    def is_book(self) -> bool:
        return (self._body.get("type") or "").lower() in ("book", "dashboard")
