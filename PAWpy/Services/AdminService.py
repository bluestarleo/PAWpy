"""AdminService — PAW administration REST surface (``/api/v1/admin``).

Covers the administrative endpoints exposed by recent PAW builds: the list of
registered TM1 / database servers, users and groups. IBM documents the broad
shape (``/api/v1/admin/...``) but the per-build resource names vary, so this
service offers typed helpers for the common resources **and** a generic
:meth:`get` escape hatch for anything not yet wrapped.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import odata_value_list

DEFAULT_ADMIN_BASE = "/api/v1/admin"


class AdminService(ObjectService):
    # PAW API group (see PAWpy.version_requirements / coverage/COVERAGE.md).
    API_GROUP = "admin"

    def __init__(self, rest: RestService, admin_base: str = DEFAULT_ADMIN_BASE):
        super().__init__(rest)
        self._base = "/" + admin_base.strip("/")

    def get(self, resource: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Generic GET against an admin sub-resource (e.g. ``"servers"``)."""
        resp = self._rest.GET(f"{self._base}/{resource.lstrip('/')}", params=params)
        return resp.json()

    def get_tm1_servers(self) -> List[Dict[str, Any]]:
        """List the TM1 / database servers registered with this PAW instance."""
        return odata_value_list(self.get("servers"))

    def get_databases(self) -> List[Dict[str, Any]]:
        """List TM1 databases via ``GET /api/v1/tm1/Servers`` — the OAuth-era
        (PAW 2.1.21+ / 3.1.8+) successor to :meth:`get_tm1_servers`. Note this
        endpoint lives outside ``admin_base``."""
        return odata_value_list(self._rest.GET("/api/v1/tm1/Servers").json())

    def get_users(self) -> List[Dict[str, Any]]:
        return odata_value_list(self.get("users"))

    def get_groups(self) -> List[Dict[str, Any]]:
        return odata_value_list(self.get("groups"))
