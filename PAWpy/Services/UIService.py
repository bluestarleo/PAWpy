"""UIService — pure URL builder for the PAW UI API ``/ui`` endpoint.

These endpoints return an HTML page that renders a PAW widget (book, view,
dimension/set editor, websheet) and are meant to be dropped into an ``iframe``.
No HTTP call is made here — every method returns a fully-formed URL string.

Reference: https://ibm.github.io/planninganalyticsapi/  (Widget rendering)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService


class UIService(ObjectService):
    def __init__(self, rest: RestService):
        super().__init__(rest)

    def _url(self, params: Dict[str, Any]) -> str:
        # Drop None values so optional params are omitted entirely.
        clean = {k: v for k, v in params.items() if v is not None}
        # Booleans render as lowercase true/false per the UI API.
        for k, v in clean.items():
            if isinstance(v, bool):
                clean[k] = "true" if v else "false"
        return self._rest.build_url("/ui", clean)

    # ------------------------------------------------------------------ #
    # Books
    # ------------------------------------------------------------------ #
    def book_url(self, path: str, embed: Optional[bool] = None) -> str:
        """Embed URL for a PAW book at content-store *path*."""
        return self._url({"type": "book", "path": path, "embed": embed})

    # ------------------------------------------------------------------ #
    # Cube viewer / views
    # ------------------------------------------------------------------ #
    def cube_viewer_url(
        self,
        server: Optional[str] = None,
        cube: Optional[str] = None,
        view: Optional[str] = None,
        *,
        path: Optional[str] = None,
        private: Optional[bool] = None,
        toolbar: Optional[str] = None,
        properties: Optional[str] = None,
    ) -> str:
        """Embed URL for the Cube Viewer.

        Two addressing styles are supported (per the UI API):
          * by content path: pass ``path`` (+ optional ``server``)
          * by server/cube/view: pass ``server`` and ``cube`` (+ optional ``view``)
        """
        if path:
            params = {"type": "cube-viewer", "path": path, "server": server,
                      "toolbar": toolbar, "properties": properties}
        else:
            if not (server and cube):
                raise ValueError("cube_viewer_url requires either 'path' or both 'server' and 'cube'")
            params = {"type": "cube-viewer", "server": server, "cube": cube,
                      "view": view, "private": private, "toolbar": toolbar}
        return self._url(params)

    # ------------------------------------------------------------------ #
    # Dimension editor
    # ------------------------------------------------------------------ #
    def dimension_editor_url(
        self, server: str, dimension: str, hierarchy: Optional[str] = None
    ) -> str:
        return self._url({
            "type": "dimension-editor", "server": server,
            "dimension": dimension, "hierarchy": hierarchy,
        })

    # ------------------------------------------------------------------ #
    # Set editor
    # ------------------------------------------------------------------ #
    def set_editor_url(
        self,
        server: str,
        dimension: str,
        unique_name: str,
        *,
        cube: Optional[str] = None,
        hierarchy: Optional[str] = None,
        alias: Optional[str] = None,
        private: Optional[bool] = None,
        dimension_caption: Optional[str] = None,
        hierarchy_caption: Optional[str] = None,
    ) -> str:
        return self._url({
            "type": "set-editor", "server": server, "cube": cube,
            "dimension": dimension, "uniqueName": unique_name,
            "hierarchy": hierarchy, "alias": alias, "private": private,
            "dimensionCaption": dimension_caption,
            "hierarchyCaption": hierarchy_caption,
        })

    # ------------------------------------------------------------------ #
    # Websheet
    # ------------------------------------------------------------------ #
    def websheet_url(
        self,
        workbook: str,
        tm1_server: str,
        *,
        action: str = "Open",
        admin_host: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Embed URL for a TM1 Web websheet (params follow the TM1 Web URL API)."""
        params: Dict[str, Any] = {
            "type": "websheet", "Action": action,
            "Workbook": workbook, "TM1Server": tm1_server,
            "AdminHost": admin_host,
        }
        if extra:
            params.update(extra)
        return self._url(params)
