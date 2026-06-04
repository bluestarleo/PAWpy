"""ViewService — convenience layer over ContentService for PAW views.

A PAW "view" is a saved cube-viewer asset in the content store. This mirrors
:class:`BookService`: list views in a folder, fetch one by path, and produce a
cube-viewer embed URL via :class:`UIService`.
"""

from __future__ import annotations

from typing import List, Optional

from PAWpy.Objects.Asset import Asset
from PAWpy.Services.ContentService import ContentService
from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Services.UIService import UIService

_VIEW_TYPES = {"view", "cube-viewer", "cubeviewer"}


class ViewService(ObjectService):
    def __init__(self, rest: RestService, content: ContentService, ui: UIService):
        super().__init__(rest)
        self._content = content
        self._ui = ui

    def get_all(self, folder_path: str) -> List[Asset]:
        children = self._content.list_children(folder_path)
        return [a for a in children if (a.type or "").lower() in _VIEW_TYPES]

    def get(self, path: str, expand_content: bool = False) -> Asset:
        return self._content.get_by_path(path, expand_content=expand_content)

    def get_embed_url(self, path: str, server: Optional[str] = None, toolbar: Optional[str] = None) -> str:
        """Cube-viewer embed URL for a saved view addressed by content path."""
        return self._ui.cube_viewer_url(path=path, server=server, toolbar=toolbar)
