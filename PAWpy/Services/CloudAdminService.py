"""CloudAdminService — Planning Analytics on Cloud subscription admin
(``/api/v1/cloudadmin``).

**PA on Cloud (SaaS) only.** Subscription and tenant-invitation management for
IBM-hosted Planning Analytics; on-prem / Local PAW does not expose these.

Source: IBM's designated Postman collection, folder "PA on Cloud Admin
(2.1.24 & 3.1.11)". Not yet GA when the wrapper was written, so the
``cloudadmin`` API group is pinned at 2.1.24 / 3.1.11 but marked UNVERIFIED
until IBM's "What's new" confirms it — see :mod:`PAWpy.version_requirements`.

    GET    /api/v1/cloudadmin/subscriptionDetails          subscription details
    GET    /api/v1/cloudadmin/subscriptions                available subscriptions
    GET    /api/v1/cloudadmin/users/<id>/subscriptions     a user's subscriptions
    POST   /api/v1/cloudadmin/subscriptions                add users to a subscription
    DELETE /api/v1/cloudadmin/subscriptions                revoke subscriptions
    POST   /api/v1/cloudadmin/tenants/invitations          invite one new user
    POST   /api/v1/cloudadmin/bulk/users/invite            invite uploaded users
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import odata_value_list

DEFAULT_CLOUDADMIN_BASE = "/api/v1/cloudadmin"


def _json_or_none(resp: requests.Response) -> Any:
    if resp.status_code == 204 or not resp.content:
        return None
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "json" in ctype:
        return resp.json()
    return resp.text


class CloudAdminService(ObjectService):
    # PAW API group (see PAWpy.version_requirements / coverage/COVERAGE.md).
    API_GROUP = "cloudadmin"

    def __init__(self, rest: RestService, cloudadmin_base: str = DEFAULT_CLOUDADMIN_BASE):
        super().__init__(rest)
        self._base = "/" + cloudadmin_base.strip("/")

    # ------------------------------------------------------------------ #
    # Subscriptions
    # ------------------------------------------------------------------ #
    def get_subscription_details(self) -> Dict[str, Any]:
        return self._rest.GET(f"{self._base}/subscriptionDetails").json()

    def get_subscriptions(self) -> List[Dict[str, Any]]:
        return odata_value_list(self._rest.GET(f"{self._base}/subscriptions").json())

    def get_user_subscriptions(self, user_id: str) -> List[Dict[str, Any]]:
        """A user's subscriptions.

        IBM's collection spells this request ``users{id}/subscriptions`` (no
        slash); PAWpy sends the conventional ``users/<id>/subscriptions``.
        UNVERIFIED against a live SaaS tenant — override the path via
        :attr:`rest` if your tenant differs.
        """
        return odata_value_list(
            self._rest.GET(f"{self._base}/users/{user_id}/subscriptions").json()
        )

    def add_users_to_subscription(self, login_ids: List[str], subscription_id: str) -> Any:
        """Add users (identified by login id) to a subscription."""
        return _json_or_none(self._rest.POST(
            f"{self._base}/subscriptions",
            json={"users": login_ids, "subscriptionId": subscription_id},
        ))

    def revoke_subscriptions(
        self, tm1_subscription_ids: List[str], users: List[Dict[str, str]]
    ) -> Any:
        """Revoke subscriptions for users. *users* entries are
        ``{"userId": …, "email": …, "loginId": …}``."""
        return _json_or_none(self._rest.DELETE(
            f"{self._base}/subscriptions",
            json={"tm1SubscriptionIds": tm1_subscription_ids, "users": users},
        ))

    # ------------------------------------------------------------------ #
    # Invitations
    # ------------------------------------------------------------------ #
    def invite_user(
        self,
        first_name: str,
        last_name: str,
        contact_email: str,
        wa_role: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Invite one new user to the tenant. *wa_role* follows IBM's shape
        ``{"roleName", "roleId", "label", "source"}``."""
        body: Dict[str, Any] = {
            "firstName": first_name, "lastName": last_name, "contactEmail": contact_email,
        }
        if wa_role is not None:
            body["waRole"] = wa_role
        return _json_or_none(self._rest.POST(f"{self._base}/tenants/invitations", json=body))

    def bulk_invite_users(self, users: List[Dict[str, Any]], subscription_id: str) -> Any:
        """Invite already-uploaded users. *users* entries carry ``firstName``,
        ``lastName``, ``email``, ``role``, ``loginId``, ``displayName``."""
        return _json_or_none(self._rest.POST(
            f"{self._base}/bulk/users/invite",
            json={"users": users, "subscriptionId": subscription_id},
        ))
