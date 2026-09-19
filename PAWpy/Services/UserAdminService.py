"""UserAdminService — Workspace user & group administration (``/api/v1/useradmin``).

The write-capable successor to the read-only ``/api/v1/content/users|groups``
surface wrapped by :class:`~PAWpy.Services.UserGroupService.UserGroupService`:
create / update / delete users and groups, manage group membership, change
roles and states in bulk, CSV import/export, and (multi-environment
deployments) copy users between environments.

Source: IBM's designated Postman collection, folder "User admin (2.1.25 &
3.1.12)", plus the IBM Community announcement thread (Sept 2026 update:
"adding supported endpoints for users, groups, and database management").
These builds were not yet GA when the wrapper was written, so the
``useradmin`` API group is pinned at 2.1.25 / 3.1.12 but marked UNVERIFIED
until IBM's "What's new" confirms it — see :mod:`PAWpy.version_requirements`.

Users
    GET    /api/v1/useradmin/users                         list
    GET    /api/v1/useradmin/users/<id>                    one user
    GET    /api/v1/useradmin/users/<id>/profile            profile
    GET    /api/v1/useradmin/users/<id>/roles              roles
    GET    /api/v1/useradmin/users/<id>/groups             groups
    GET    /api/v1/useradmin/users/<id>/environments       environments
    POST   /api/v1/useradmin/users                         create
    PATCH  /api/v1/useradmin/users/<id>                    patch
    DELETE /api/v1/useradmin/users/<id>                    delete one
    DELETE /api/v1/useradmin/users            {users:[…]}  delete many
    PATCH  /api/v1/useradmin/users/role       {users, waRole}
    PATCH  /api/v1/useradmin/users/state      {users, userState}
    GET    /api/v1/useradmin/users/bulk                    CSV export
    POST   /api/v1/useradmin/users/bulk                    CSV import
Groups
    GET    /api/v1/useradmin/groups                        list
    GET    /api/v1/useradmin/groups/<id>                   one group
    GET    /api/v1/useradmin/groups/<id>/users             members
    POST   /api/v1/useradmin/groups                        create
    PUT    /api/v1/useradmin/groups/<id>                   replace
    PATCH  /api/v1/useradmin/groups/<id>                   update
    DELETE /api/v1/useradmin/groups/<id>                   delete one
    DELETE /api/v1/useradmin/groups           {groups:[…]} delete many
    POST   /api/v1/useradmin/groups/<id>/users             add member
    DELETE /api/v1/useradmin/groups/<id>/users/<userId>    remove member
    GET    /api/v1/useradmin/groups/bulk                   CSV export
    POST   /api/v1/useradmin/groups/bulk                   bulk add
Environment
    GET    /api/v1/useradmin/roles
    GET    /api/v1/useradmin/quota
    GET    /api/v1/useradmin/environments
    POST   /api/v1/useradmin/environments                  copy users to env
    DELETE /api/v1/useradmin/environments/users            remove users from env
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import odata_value_list

# Default base path of the user admin API. Override via the constructor for
# deployments that expose it under a different prefix.
DEFAULT_USERADMIN_BASE = "/api/v1/useradmin"

CSV_CONTENT_TYPE = "application/csv"


def _json_or_none(resp: requests.Response) -> Any:
    if resp.status_code == 204 or not resp.content:
        return None
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "json" in ctype:
        return resp.json()
    return resp.text


def _drop_none(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class UserAdminService(ObjectService):
    # PAW API group (see PAWpy.version_requirements / coverage/COVERAGE.md).
    API_GROUP = "useradmin"

    def __init__(self, rest: RestService, useradmin_base: str = DEFAULT_USERADMIN_BASE):
        super().__init__(rest)
        self._base = "/" + useradmin_base.strip("/")

    # ------------------------------------------------------------------ #
    # Users — read
    # ------------------------------------------------------------------ #
    def get_users(self) -> List[Dict[str, Any]]:
        """List the users in the current environment."""
        return odata_value_list(self._rest.GET(f"{self._base}/users").json())

    def get_user(self, user_id: str) -> Dict[str, Any]:
        return self._rest.GET(f"{self._base}/users/{user_id}").json()

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        return self._rest.GET(f"{self._base}/users/{user_id}/profile").json()

    def get_user_roles(self, user_id: str) -> Any:
        return self._rest.GET(f"{self._base}/users/{user_id}/roles").json()

    def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        return odata_value_list(self._rest.GET(f"{self._base}/users/{user_id}/groups").json())

    def get_user_environments(self, user_id: str) -> List[Dict[str, Any]]:
        return odata_value_list(
            self._rest.GET(f"{self._base}/users/{user_id}/environments").json()
        )

    # ------------------------------------------------------------------ #
    # Users — write
    # ------------------------------------------------------------------ #
    def create_user(
        self,
        login_id: str,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> Any:
        """Create a user. *role* is a Workspace role name (see :meth:`get_roles`)."""
        body = _drop_none({
            "loginId": login_id, "firstName": first_name, "lastName": last_name,
            "email": email, "role": role, "displayName": display_name,
        })
        return _json_or_none(self._rest.POST(f"{self._base}/users", json=body))

    def update_user(self, user_id: str, **fields: Any) -> Any:
        """Patch a user. *fields* use the API's camelCase names (``firstName``,
        ``lastName``, ``email``, ``role``, ``loginId``, ``displayName``)."""
        return _json_or_none(self._rest.PATCH(f"{self._base}/users/{user_id}", json=fields))

    def delete_user(self, user_id: str) -> None:
        self._rest.DELETE(f"{self._base}/users/{user_id}")

    def delete_users(self, user_ids: List[str]) -> Any:
        """Delete several users from the current environment in one call."""
        return _json_or_none(self._rest.DELETE(f"{self._base}/users", json={"users": user_ids}))

    def set_users_role(self, user_ids: List[str], wa_role: Dict[str, Any]) -> Any:
        """Change the Workspace role of several users.

        *wa_role* follows IBM's shape: ``{"roleName": …, "roleId": …,
        "label": …, "source": …}`` (take it from :meth:`get_roles`).
        """
        return _json_or_none(
            self._rest.PATCH(f"{self._base}/users/role", json={"users": user_ids, "waRole": wa_role})
        )

    def set_users_state(self, user_ids: List[str], state: str) -> Any:
        """Change the state of several users (e.g. ``"ACTIVE"``)."""
        return _json_or_none(
            self._rest.PATCH(f"{self._base}/users/state", json={"users": user_ids, "userState": state})
        )

    def export_users_csv(self) -> str:
        """Download all users as CSV text."""
        return self._rest.GET(f"{self._base}/users/bulk", headers={"Accept": "*/*"}).text

    def import_users_csv(self, csv_text: str) -> Any:
        """Bulk-add users from CSV text (one user per line, IBM's column order:
        ``firstName,lastName,displayName,role,<state>,<status>,<action>,loginId``
        per the collection example ``Bob,Bob,Bob,Modeler,NOT_SET,ACTIVE,ADD,Reed``)."""
        resp = self._rest.POST(
            f"{self._base}/users/bulk",
            data=csv_text.encode("utf-8"),
            headers={"Content-Type": CSV_CONTENT_TYPE},
        )
        return _json_or_none(resp)

    # ------------------------------------------------------------------ #
    # Groups — read
    # ------------------------------------------------------------------ #
    def get_groups(self) -> List[Dict[str, Any]]:
        return odata_value_list(self._rest.GET(f"{self._base}/groups").json())

    def get_group(self, group_id: str) -> Dict[str, Any]:
        return self._rest.GET(f"{self._base}/groups/{group_id}").json()

    def get_group_users(self, group_id: str) -> List[Dict[str, Any]]:
        return odata_value_list(self._rest.GET(f"{self._base}/groups/{group_id}/users").json())

    # ------------------------------------------------------------------ #
    # Groups — write
    # ------------------------------------------------------------------ #
    @staticmethod
    def _group_body(display_name, description, role_name, users) -> Dict[str, Any]:
        return _drop_none({
            "displayName": display_name, "description": description,
            "roleName": role_name, "users": users,
        })

    def create_group(
        self,
        display_name: str,
        *,
        description: Optional[str] = None,
        role_name: Optional[str] = None,
        users: Optional[List[Dict[str, str]]] = None,
    ) -> Any:
        """Create a group. *users* entries are ``{"id": …, "loginId": …}``."""
        body = self._group_body(display_name, description, role_name, users)
        return _json_or_none(self._rest.POST(f"{self._base}/groups", json=body))

    def replace_group(
        self,
        group_id: str,
        display_name: str,
        *,
        description: Optional[str] = None,
        role_name: Optional[str] = None,
        users: Optional[List[Dict[str, str]]] = None,
    ) -> Any:
        """Replace a group's definition (PUT)."""
        body = self._group_body(display_name, description, role_name, users)
        return _json_or_none(self._rest.PUT(f"{self._base}/groups/{group_id}", json=body))

    def update_group(self, group_id: str, **fields: Any) -> Any:
        """Patch a group (``displayName``, ``description``, ``roleName``, ``users``)."""
        return _json_or_none(self._rest.PATCH(f"{self._base}/groups/{group_id}", json=fields))

    def delete_group(self, group_id: str) -> None:
        self._rest.DELETE(f"{self._base}/groups/{group_id}")

    def delete_groups(self, group_ids: List[str]) -> Any:
        return _json_or_none(self._rest.DELETE(f"{self._base}/groups", json={"groups": group_ids}))

    def add_user_to_group(
        self, group_id: str, user_id: Optional[str] = None, login_id: Optional[str] = None
    ) -> Any:
        """Add a user to a group by *user_id* and/or *login_id*."""
        if not (user_id or login_id):
            raise ValueError("add_user_to_group requires user_id and/or login_id")
        body = _drop_none({"id": user_id, "loginId": login_id})
        return _json_or_none(self._rest.POST(f"{self._base}/groups/{group_id}/users", json=body))

    def remove_user_from_group(self, group_id: str, user_id: str) -> None:
        self._rest.DELETE(f"{self._base}/groups/{group_id}/users/{user_id}")

    def export_groups_csv(self) -> str:
        """Download all groups as CSV text."""
        return self._rest.GET(f"{self._base}/groups/bulk", headers={"Accept": "*/*"}).text

    def import_groups_bulk(self, data: Any, content_type: str = CSV_CONTENT_TYPE) -> Any:
        """Bulk-add groups (``POST groups/bulk``).

        IBM's collection shows an empty body for this request, so the payload
        format is not documented; *data* is sent as-is (``str``/``bytes`` are
        sent raw with *content_type*, anything else as JSON).
        """
        if isinstance(data, (str, bytes)):
            raw = data.encode("utf-8") if isinstance(data, str) else data
            resp = self._rest.POST(
                f"{self._base}/groups/bulk", data=raw, headers={"Content-Type": content_type}
            )
        else:
            resp = self._rest.POST(f"{self._base}/groups/bulk", json=data)
        return _json_or_none(resp)

    # ------------------------------------------------------------------ #
    # Roles / quota / environments
    # ------------------------------------------------------------------ #
    def get_roles(self) -> List[Dict[str, Any]]:
        """List the Workspace roles available in this environment."""
        return odata_value_list(self._rest.GET(f"{self._base}/roles").json())

    def get_quota(self) -> Dict[str, Any]:
        """The current environment's user quota."""
        return self._rest.GET(f"{self._base}/quota").json()

    def get_environments(self) -> List[Dict[str, Any]]:
        return odata_value_list(self._rest.GET(f"{self._base}/environments").json())

    def copy_users_to_environment(
        self, dest_environment_id: str, users: List[Dict[str, str]]
    ) -> Any:
        """Copy users into another environment. *users* entries are
        ``{"srcTenantId": …, "srcUserId": …, "loginId": …}``."""
        return _json_or_none(self._rest.POST(
            f"{self._base}/environments",
            json={"destEnvironmentId": dest_environment_id, "users": users},
        ))

    def remove_users_from_environment(
        self, dest_environment_id: str, users: List[Dict[str, str]]
    ) -> Any:
        """Remove users from an environment. *users* entries are
        ``{"userId": …, "email": …, "loginId": …}``."""
        return _json_or_none(self._rest.DELETE(
            f"{self._base}/environments/users",
            json={"destEnvironmentId": dest_environment_id, "users": users},
        ))
