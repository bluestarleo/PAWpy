"""DatabaseService — PAW database administration (``/api/v1/databases``).

The REST counterpart of the buttons on the Planning Analytics Administration
"database details" page: list the databases PAW knows about, start / stop /
force-stop / restart a database, and (TM1 12 / v12 databases only) create or
delete a database and manage its backups.

Source: IBM's designated Postman collection, folder "Databases (2.1.24 &
3.1.11)", plus the IBM Community announcement thread (Sept 2026 update:
"adding supported endpoints for users, groups, and database management …
options that mirror the buttons in PAA database details"). These builds were
not yet GA when the wrapper was written, so the ``databases`` API group is
pinned at 2.1.24 / 3.1.11 but marked UNVERIFIED until IBM's "What's new"
confirms it — see :mod:`PAWpy.version_requirements`.

    GET    /api/v1/databases                                              list
    POST   /api/v1/databases/servers('<db>')/start                        start
    POST   /api/v1/databases/servers('<db>')/stop                         stop
    POST   /api/v1/databases/servers('<db>')/endProcess                   force stop
    POST   /api/v1/databases/servers('<db>')/restart                      restart
    POST   /api/v1/databases/v12db                                        create (TM1 12)
    DELETE /api/v1/databases/v12db('<db>')                                delete (TM1 12)
    POST   /api/v1/databases/v12db('<db>')/backup                         create backup
    GET    /api/v1/databases/v12db('<db>')/backups/MANUAL | AUTO          list backups
    GET    /api/v1/databases/v12db('<db>')/backups('<type>')/files('<f>') download backup
    DELETE /api/v1/databases/v12db('<db>')/backups('<type>')/files('<f>') delete backup
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Utils.Utils import odata_value_list

# Default base path of the database admin API. Override via the constructor
# for deployments that expose it under a different prefix.
DEFAULT_DATABASES_BASE = "/api/v1/databases"

BACKUP_TYPES = ("MANUAL", "AUTO")


def _json_or_none(resp: requests.Response) -> Any:
    if resp.status_code == 204 or not resp.content:
        return None
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "json" in ctype:
        return resp.json()
    return resp.text


class DatabaseService(ObjectService):
    # PAW API group (see PAWpy.version_requirements / coverage/COVERAGE.md).
    API_GROUP = "databases"

    def __init__(self, rest: RestService, databases_base: str = DEFAULT_DATABASES_BASE):
        super().__init__(rest)
        self._base = "/" + databases_base.strip("/")

    # ------------------------------------------------------------------ #
    # Listing
    # ------------------------------------------------------------------ #
    def get_all(self) -> List[Dict[str, Any]]:
        """List every database registered with this PAW instance."""
        return odata_value_list(self._rest.GET(self._base).json())

    # ------------------------------------------------------------------ #
    # Lifecycle — mirrors the PAA "database details" buttons
    # ------------------------------------------------------------------ #
    def _server_action(self, database: str, action: str) -> Any:
        resp = self._rest.POST(f"{self._base}/servers('{database}')/{action}")
        return _json_or_none(resp)

    def start(self, database: str) -> Any:
        """Start a stopped database."""
        return self._server_action(database, "start")

    def stop(self, database: str) -> Any:
        """Stop a running database gracefully."""
        return self._server_action(database, "stop")

    def force_stop(self, database: str) -> Any:
        """Force-stop a database (``endProcess`` — kills the server process)."""
        return self._server_action(database, "endProcess")

    def restart(self, database: str) -> Any:
        """Restart a database."""
        return self._server_action(database, "restart")

    # ------------------------------------------------------------------ #
    # TM1 12 (v12) databases — create / delete
    # ------------------------------------------------------------------ #
    def create_v12(
        self,
        name: str,
        *,
        replicas: int = 1,
        resources: Optional[Dict[str, Any]] = None,
        auto_backup_opt_out: bool = False,
        schedule: Optional[str] = None,
        **extra: Any,
    ) -> Any:
        """Create a TM1 12 database.

        *resources* follows IBM's example shape::

            {"replica": {"memory": {"requests": "2G", "limits": "2G"}},
             "storage": {"size": "20G"}}

        *schedule* is the automatic-backup cron expression (e.g. ``"0 23 * * *"``).
        Any *extra* keyword is passed through into the request body.
        """
        body: Dict[str, Any] = {
            "name": name,
            "replicas": replicas,
            "autoBackupOptOut": auto_backup_opt_out,
        }
        if resources is not None:
            body["resources"] = resources
        if schedule is not None:
            body["schedule"] = schedule
        body.update(extra)
        return _json_or_none(self._rest.POST(f"{self._base}/v12db", json=body))

    def delete_v12(self, database: str) -> None:
        """Delete a TM1 12 database. Irreversible."""
        self._rest.DELETE(f"{self._base}/v12db('{database}')")

    # ------------------------------------------------------------------ #
    # TM1 12 (v12) backups
    # ------------------------------------------------------------------ #
    @staticmethod
    def _backup_type(backup_type: str) -> str:
        bt = (backup_type or "").upper()
        if bt not in BACKUP_TYPES:
            raise ValueError(f"backup_type must be one of {BACKUP_TYPES}, got {backup_type!r}")
        return bt

    def create_backup(self, database: str, url: str) -> Any:
        """Create a manual backup of a TM1 12 database; *url* is the backup
        file name/URL (e.g. ``"nightly.tgz"``)."""
        return _json_or_none(
            self._rest.POST(f"{self._base}/v12db('{database}')/backup", json={"url": url})
        )

    def get_backups(self, database: str, backup_type: str = "MANUAL") -> List[Dict[str, Any]]:
        """List a TM1 12 database's backups; *backup_type* is ``MANUAL`` or ``AUTO``."""
        bt = self._backup_type(backup_type)
        return odata_value_list(
            self._rest.GET(f"{self._base}/v12db('{database}')/backups/{bt}").json()
        )

    def download_backup(self, database: str, backup_type: str, file_name: str) -> bytes:
        """Download one backup file; returns the raw bytes."""
        bt = self._backup_type(backup_type)
        resp = self._rest.GET(
            f"{self._base}/v12db('{database}')/backups('{bt}')/files('{file_name}')",
            headers={"Accept": "*/*"},
        )
        return resp.content

    def delete_backup(self, database: str, backup_type: str, file_name: str) -> None:
        """Delete one backup file."""
        bt = self._backup_type(backup_type)
        self._rest.DELETE(
            f"{self._base}/v12db('{database}')/backups('{bt}')/files('{file_name}')"
        )
