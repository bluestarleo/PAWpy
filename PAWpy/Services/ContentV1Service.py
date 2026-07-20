"""ContentV1Service — the OAuth-era PAW Content API (``/api/v1/content``).

The officially supported REST API introduced in PAW 2.1.21 / 3.1.8 (see the
``content-v1`` group in :mod:`PAWpy.version_requirements`). Successor surface
to ``/pacontent/v1`` (:class:`~PAWpy.Services.ContentService.ContentService`),
with capabilities the legacy API lacks: asset content retrieval, per-asset
permissions, bulk operations, and asset types.

Endpoints wrapped (per IBM's designated Postman collection):

    GET    /api/v1/content/assets('<id>')                      fetch by id
    GET    /api/v1/content/assets(path='<path>')/assets        list children
    GET    /api/v1/content/assets('<id>')/content              asset content
    POST   /api/v1/content/assets(path='<path>')/assets        create asset
    DELETE /api/v1/content/assets('<id>')                      delete
    GET    /api/v1/content/assets('<id>')/permissions          get permissions
    PUT    /api/v1/content/assets('<id>')/permissions          set permissions
    GET    /api/v1/content/assets('<id>')/effectivepermissions effective perms
    POST   /api/v1/content/bulkcopy | bulkmove | bulkdelete | bulkpermissions
    GET    /api/v1/content/assettypes

Known permission names (from IBM's set-permissions example): ``list``,
``open``, ``write``, ``manage``, ``secure``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from PAWpy.Objects.Asset import Asset
from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import odata_query, odata_value_list

# Default base path of the OAuth-era content API. Override via the constructor
# for deployments that expose it under a different prefix.
DEFAULT_CONTENT_V1_BASE = "/api/v1/content"


def _json_or_none(resp: requests.Response) -> Any:
    if resp.status_code == 204 or not resp.content:
        return None
    return resp.json()


class ContentV1Service(ObjectService):
    # PAW API group (see PAWpy.version_requirements / coverage matrix).
    API_GROUP = "content-v1"

    def __init__(self, rest: RestService, content_base: str = DEFAULT_CONTENT_V1_BASE):
        super().__init__(rest)
        self._base = "/" + content_base.strip("/")

    @staticmethod
    def _enc(path: str) -> str:
        # Root folders ('shared', 'personal', 'users') pass through unchanged;
        # anything else is URL-encoded once. (Unlike /pacontent/v1, IBM's
        # examples for this API show plain paths, not double-encoded ones.)
        return quote(path, safe="")

    # ------------------------------------------------------------------ #
    # Assets
    # ------------------------------------------------------------------ #
    def get(self, asset_id: str) -> Asset:
        """Fetch a single asset by id."""
        resp = self._rest.GET(f"{self._base}/assets('{asset_id}')")
        return Asset(resp.json())

    def list_children(
        self,
        path: str = "shared",
        *,
        filter: Optional[str] = None,
        select: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[Asset]:
        """List the assets inside the folder at *path*.

        *path* is a content-store folder path; the roots are ``shared``,
        ``personal`` and ``users``.
        """
        params = odata_query(filter=filter, select=select, orderby=orderby, top=top, skip=skip)
        resp = self._rest.GET(
            f"{self._base}/assets(path='{self._enc(path)}')/assets",
            params=params or None,
        )
        return [Asset(item) for item in odata_value_list(resp.json())]

    def get_content(self, asset_id: str) -> Any:
        """Fetch an asset's content (the book/view definition).

        Returns parsed JSON when the server responds with JSON, else the raw
        bytes.
        """
        resp = self._rest.GET(f"{self._base}/assets('{asset_id}')/content")
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "json" in ctype:
            return resp.json()
        return resp.content

    def create(
        self,
        path: str,
        name: str,
        type: str,
        content: Any = None,
        custom_properties: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ) -> Asset:
        """Create an asset (with optional ``content``) in the folder at *path*."""
        body: Dict[str, Any] = {"name": name, "type": type, "overwrite": overwrite}
        if content is not None:
            body["content"] = content
        if custom_properties is not None:
            body["custom_properties"] = custom_properties
        resp = self._rest.POST(
            f"{self._base}/assets(path='{self._enc(path)}')/assets",
            json=body,
        )
        return Asset(resp.json())

    def delete(self, asset_id: str) -> None:
        """Delete an asset by id (no ``type`` predicate needed on this API)."""
        self._rest.DELETE(f"{self._base}/assets('{asset_id}')")

    # ------------------------------------------------------------------ #
    # Permissions
    # ------------------------------------------------------------------ #
    def get_permissions(self, asset_id: str) -> Any:
        """Permissions explicitly set on the asset."""
        return self._rest.GET(f"{self._base}/assets('{asset_id}')/permissions").json()

    def get_effective_permissions(self, asset_id: str) -> Any:
        """Permissions in effect on the asset (including inherited ones)."""
        return self._rest.GET(f"{self._base}/assets('{asset_id}')/effectivepermissions").json()

    def set_permissions(
        self,
        asset_id: str,
        permissions: List[Dict[str, Any]],
        inherit: bool = False,
    ) -> Any:
        """Replace the asset's permissions.

        Each *permissions* entry names one principal and its rights, e.g.::

            {"permissions": ["list", "open", "write"], "user": "<user-id>"}
            {"permissions": ["list", "open"], "group": "<group-id>"}
        """
        resp = self._rest.PUT(
            f"{self._base}/assets('{asset_id}')/permissions",
            json={"inherit": inherit, "permissions": permissions},
        )
        return _json_or_none(resp)

    # ------------------------------------------------------------------ #
    # Bulk operations
    # ------------------------------------------------------------------ #
    def bulk_copy(
        self,
        source_ids: List[str],
        target: str,
        conflict_resolution: str = "OVERWRITE",
    ) -> Any:
        """Copy assets (by id) into the *target* folder asset (by id)."""
        resp = self._rest.POST(
            f"{self._base}/bulkcopy",
            json={"source": source_ids},
            params={"target": target, "conflictResolution": conflict_resolution},
        )
        return _json_or_none(resp)

    def bulk_move(
        self,
        source_ids: List[str],
        target: str,
        conflict_resolution: str = "OVERWRITE",
    ) -> Any:
        """Move assets (by id) into the *target* folder asset (by id)."""
        resp = self._rest.POST(
            f"{self._base}/bulkmove",
            json={"source": source_ids},
            params={"target": target, "conflictResolution": conflict_resolution},
        )
        return _json_or_none(resp)

    def bulk_delete(self, asset_ids: List[str]) -> Any:
        """Delete several assets by id in one call."""
        resp = self._rest.POST(f"{self._base}/bulkdelete", json={"assets": asset_ids})
        return _json_or_none(resp)

    def bulk_permissions(
        self,
        asset_ids: List[str],
        permissions: List[Dict[str, Any]],
        inherit: bool = True,
        recursive: bool = False,
    ) -> Any:
        """Apply one permission set to several assets.

        Each *permissions* entry may name several principals at once, e.g.::

            {"permissions": ["list", "open"], "users": ["<id>"], "groups": ["<id>"]}
        """
        resp = self._rest.POST(
            f"{self._base}/bulkpermissions",
            json={"assets": asset_ids, "inherit": inherit, "permissions": permissions},
            params={"recursive": str(recursive).lower()},
        )
        return _json_or_none(resp)

    # ------------------------------------------------------------------ #
    # Asset types
    # ------------------------------------------------------------------ #
    def get_asset_types(self) -> List[Dict[str, Any]]:
        """List the asset types this PAW deployment supports."""
        return odata_value_list(self._rest.GET(f"{self._base}/assettypes").json())
