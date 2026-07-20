"""TM1ProxyService — reach the TM1 REST API *through* PAW's gateway/auth.

PAW proxies the underlying TM1 (database) REST API at:

    /api/v0/tm1/<server>/api/v1/...   (legacy builds — the default)
    /api/v1/tm1/<server>/api/v1/...   (PAW 2.1.21+ / 3.1.8+, the OAuth-era API)

so an external app authenticated to PAW can run MDX, read cube/dimension
metadata, etc. without holding separate TM1 credentials. This is PAWpy's
analogue of TM1py's Cube/Dimension/Process services — except every call is
relayed by PAW. Pass ``proxy_base=PROXY_PREFIX_V1`` (or set ``tm1_proxy_base``
on ``PAWService``) to target the v1 proxy.

The methods here cover the high-value reads; ``get``/``post``/``patch``/
``put``/``delete`` are generic pass-throughs to any TM1 REST path for
everything else.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import odata_value_list

# PAW's AJAX proxy prefix (avoids CORS) per the UI API docs.
PROXY_PREFIX = "/api/v0/tm1"
# The proxy prefix on the OAuth-era API (PAW 2.1.21+ / 3.1.8+); see the
# "tm1-proxy-v1" group in PAWpy.version_requirements.
PROXY_PREFIX_V1 = "/api/v1/tm1"


class TM1ProxyService(ObjectService):
    # PAW API group (see PAWpy.version_requirements / coverage/COVERAGE.md).
    # Version-gate the v1 proxy path via the "tm1-proxy-v1" group.
    API_GROUP = "tm1-proxy"

    def __init__(self, rest: RestService, server: str, proxy_base: str = PROXY_PREFIX):
        super().__init__(rest)
        if not server:
            raise ValueError("TM1ProxyService requires a TM1 server/database name")
        self._server = server
        self._proxy_base = "/" + proxy_base.strip("/")

    @property
    def server(self) -> str:
        return self._server

    def _path(self, tm1_path: str) -> str:
        # tm1_path is a TM1 REST path like "Cubes" or "Cubes('x')/Views".
        return f"{self._proxy_base}/{self._server}/api/v1/{tm1_path.lstrip('/')}"

    # ------------------------------------------------------------------ #
    # Generic pass-throughs
    # ------------------------------------------------------------------ #
    def get(self, tm1_path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._rest.GET(self._path(tm1_path), params=params).json()

    def post(self, tm1_path: str, json: Any = None, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = self._rest.POST(self._path(tm1_path), json=json, params=params)
        # Some TM1 POSTs (e.g. ExecuteMDX) return JSON; others 204 No Content.
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def patch(self, tm1_path: str, json: Any = None, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = self._rest.PATCH(self._path(tm1_path), json=json, params=params)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def put(self, tm1_path: str, json: Any = None, params: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """PUT to a TM1 REST path. Extra *kwargs* (e.g. ``data=`` for raw file
        content uploads like ``Contents('Files')/.../Content``) go to requests."""
        resp = self._rest.PUT(self._path(tm1_path), json=json, params=params, **kwargs)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def delete(self, tm1_path: str, params: Optional[Dict[str, Any]] = None) -> None:
        self._rest.DELETE(self._path(tm1_path), params=params)

    # ------------------------------------------------------------------ #
    # Metadata reads
    # ------------------------------------------------------------------ #
    def get_cubes(self) -> List[Dict[str, Any]]:
        return odata_value_list(self.get("Cubes"))

    def get_cube_dimensions(self, cube: str) -> List[str]:
        body = self.get(f"Cubes('{cube}')/Dimensions", params={"$select": "Name"})
        return [d.get("Name") for d in odata_value_list(body)]

    def get_dimensions(self) -> List[Dict[str, Any]]:
        return odata_value_list(self.get("Dimensions"))

    def get_views(self, cube: str, private: bool = False) -> List[Dict[str, Any]]:
        scope = "PrivateViews" if private else "Views"
        return odata_value_list(self.get(f"Cubes('{cube}')/{scope}"))

    # ------------------------------------------------------------------ #
    # MDX
    # ------------------------------------------------------------------ #
    def execute_mdx(self, mdx: str) -> Dict[str, Any]:
        """Run an MDX statement and return the raw cellset JSON (Cells + Axes)."""
        return self.post(
            "ExecuteMDX",
            json={"MDX": mdx},
            params={"$expand": "Cells,Axes($expand=Tuples($expand=Members))"},
        )

    def get_cube_data(self, cube: str, mdx: str) -> Dict[str, Any]:
        """Alias matching the README example — execute MDX against *cube*.

        The cube name is informational (the MDX already targets it); kept for a
        TM1py-familiar call signature.
        """
        return self.execute_mdx(mdx)
