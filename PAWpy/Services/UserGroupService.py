"""UserGroupService — PAW users and groups (``/api/v1/content/users|groups``).

Read endpoints for Workspace users and user groups, part of the officially
supported REST API introduced in PAW 2.1.21 / 3.1.8 ("Users and groups (new in
2.1.21 & 3.1.8)" in IBM's designated Postman collection). The ids returned
here are the principal ids consumed by
:meth:`~PAWpy.Services.ContentV1Service.ContentV1Service.set_permissions` /
``bulk_permissions``.

    GET /api/v1/content/users             list users
    GET /api/v1/content/users('<id>')     one user
    GET /api/v1/content/groups            list groups
    GET /api/v1/content/groups('<id>')    one group

IBM documents these as read (GET) endpoints; there is no documented
create/update/delete surface yet — expect it in a future PAW release.
"""

from __future__ import annotations

from typing import Any, Dict, List

from PAWpy.Services.ContentV1Service import DEFAULT_CONTENT_V1_BASE
from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import odata_value_list


class UserGroupService(ObjectService):
    # PAW API group (see PAWpy.version_requirements / coverage matrix) —
    # same base and minimum build as the v1 content API.
    API_GROUP = "content-v1"

    def __init__(self, rest: RestService, content_base: str = DEFAULT_CONTENT_V1_BASE):
        super().__init__(rest)
        self._base = "/" + content_base.strip("/")

    def get_users(self) -> List[Dict[str, Any]]:
        """List Workspace users."""
        return odata_value_list(self._rest.GET(f"{self._base}/users").json())

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Fetch one user by id."""
        return self._rest.GET(f"{self._base}/users('{user_id}')").json()

    def get_groups(self) -> List[Dict[str, Any]]:
        """List Workspace user groups."""
        return odata_value_list(self._rest.GET(f"{self._base}/groups").json())

    def get_group(self, group_id: str) -> Dict[str, Any]:
        """Fetch one group by id."""
        return self._rest.GET(f"{self._base}/groups('{group_id}')").json()
