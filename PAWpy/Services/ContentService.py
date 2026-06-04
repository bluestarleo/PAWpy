"""ContentService — CRUD over the PAW Content Services API.

Wraps the OData-style ``/pacontent/v1/Assets`` surface documented by IBM:

    GET    /pacontent/v1/Assets('<id>')                  fetch by id
    GET    /pacontent/v1/Assets(path='<path>')           fetch by path (encoded x2)
    GET    /pacontent/v1/Assets(path='<folder>')/Assets  list children
    POST   /pacontent/v1/Assets                          create folder / dashboard
    PUT    /pacontent/v1/Assets(id='<id>', type='<t>')   update content / props
    DELETE /pacontent/v1/Assets(id='<id>', type='<t>')   delete by id+type
    DELETE /pacontent/v1/Assets(path='<path>')           delete by path

Supports the OData query options ``$filter / $select / $expand / $orderby /
$top / $skip`` via :func:`PAWpy.Utils.odata_query`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PAWpy.Objects.Asset import Asset
from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import encode_path_twice, odata_query, odata_value_list

# Default base path of the content services API. Override via the constructor
# for deployments that expose content under a different prefix.
DEFAULT_CONTENT_BASE = "/pacontent/v1"


class ContentService(ObjectService):
    def __init__(self, rest: RestService, content_base: str = DEFAULT_CONTENT_BASE):
        super().__init__(rest)
        self._base = "/" + content_base.strip("/")

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #
    def get(self, asset_id: str, expand_content: bool = False) -> Asset:
        """Fetch a single asset by id."""
        params = odata_query(expand="content") if expand_content else None
        resp = self._rest.GET(f"{self._base}/Assets('{asset_id}')", params=params)
        return Asset(resp.json())

    def get_by_path(self, path: str, expand_content: bool = False) -> Asset:
        """Fetch a single asset by its content-store path (e.g. ``/shared/FP&A``)."""
        encoded = encode_path_twice(path)
        params = odata_query(expand="content") if expand_content else None
        resp = self._rest.GET(f"{self._base}/Assets(path='{encoded}')", params=params)
        return Asset(resp.json())

    def list_children(
        self,
        folder_path: str,
        *,
        filter: Optional[str] = None,
        select: Optional[str] = None,
        expand: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[Asset]:
        """List the child assets inside the folder at *folder_path*."""
        encoded = encode_path_twice(folder_path)
        params = odata_query(
            filter=filter, select=select, expand=expand,
            orderby=orderby, top=top, skip=skip,
        )
        resp = self._rest.GET(
            f"{self._base}/Assets(path='{encoded}')/Assets",
            params=params or None,
        )
        return [Asset(item) for item in odata_value_list(resp.json())]

    # ------------------------------------------------------------------ #
    # Create
    # ------------------------------------------------------------------ #
    def create(
        self,
        type: str,
        name: str,
        path: str,
        content: Any = None,
        custom_properties: Optional[Dict[str, Any]] = None,
    ) -> Asset:
        """Create a new asset (``type`` = ``folder`` or ``dashboard``)."""
        body: Dict[str, Any] = {"type": type, "name": name, "path": path}
        if content is not None:
            body["content"] = content
        if custom_properties is not None:
            body["custom_properties"] = custom_properties
        resp = self._rest.POST(f"{self._base}/Assets", json=body)
        return Asset(resp.json())

    def create_folder(self, name: str, path: str, **kwargs) -> Asset:
        return self.create("folder", name, path, **kwargs)

    # ------------------------------------------------------------------ #
    # Update
    # ------------------------------------------------------------------ #
    def update(
        self,
        asset_id: str,
        type: str,
        content: Any = None,
        custom_properties: Optional[Dict[str, Any]] = None,
        expand_content: bool = True,
    ) -> Asset:
        """Update an asset's ``content`` and/or ``custom_properties``."""
        body: Dict[str, Any] = {}
        if content is not None:
            body["content"] = content
        if custom_properties is not None:
            body["custom_properties"] = custom_properties
        params = odata_query(expand="content") if expand_content else None
        resp = self._rest.PUT(
            f"{self._base}/Assets(id='{asset_id}', type='{type}')",
            json=body,
            params=params,
        )
        return Asset(resp.json())

    # ------------------------------------------------------------------ #
    # Delete
    # ------------------------------------------------------------------ #
    def delete(self, asset_id: str, type: str) -> None:
        self._rest.DELETE(f"{self._base}/Assets(id='{asset_id}', type='{type}')")

    def delete_by_path(self, path: str) -> None:
        encoded = encode_path_twice(path)
        self._rest.DELETE(f"{self._base}/Assets(path='{encoded}')")

    # ------------------------------------------------------------------ #
    # Convenience
    # ------------------------------------------------------------------ #
    def exists(self, path: str) -> bool:
        from PAWpy.Exceptions.Exceptions import PAWNotFoundException
        try:
            self.get_by_path(path)
            return True
        except PAWNotFoundException:
            return False
