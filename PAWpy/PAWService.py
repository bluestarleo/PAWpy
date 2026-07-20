"""PAWService — the top-level entry point (mirrors TM1py's ``TM1Service``).

Construct one ``PAWService`` with connection + auth parameters and reach every
sub-service through it::

    with PAWService(host="paw.acme.com", auth_mode="oauth",
                    client_id="id", client_secret="secret",
                    token_url="https://idp/token") as paw:
        books   = paw.books.get_all("/shared/FP&A")
        url     = paw.books.get_embed_url("/shared/FP&A/Monthly Report")
        servers = paw.admin.get_tm1_servers()
        data    = paw.tm1("Global FPA").execute_mdx("SELECT ...")
        embed   = paw.ui.cube_viewer_url("Global FPA", "Revenue Cube", "Monthly View")

All keyword arguments are forwarded to :class:`RestService`, which performs
authentication on construction (unless ``connect=False``).
"""

from __future__ import annotations

from typing import Dict, Optional

from PAWpy.Services.AdminService import AdminService, DEFAULT_ADMIN_BASE
from PAWpy.Services.BookService import BookService
from PAWpy.Services.ContentService import ContentService, DEFAULT_CONTENT_BASE
from PAWpy.Services.RestService import RestService
from PAWpy.Services.TM1ProxyService import PROXY_PREFIX, TM1ProxyService
from PAWpy.Services.UIService import UIService
from PAWpy.Services.ViewService import ViewService
from PAWpy.version_requirements import (
    assert_supported as _assert_supported,
    is_supported as _is_supported,
    min_version_for as _min_version_for,
)


class PAWService:
    def __init__(
        self,
        host: str,
        *,
        database: str = None,
        content_base: str = DEFAULT_CONTENT_BASE,
        admin_base: str = DEFAULT_ADMIN_BASE,
        tm1_proxy_base: str = PROXY_PREFIX,
        paw_version: Optional[str] = None,
        **rest_kwargs,
    ):
        """
        :param host: PAW hostname (no scheme), e.g. ``paw.acme.com``.
        :param database: default TM1 database/server for :meth:`tm1` when called
            with no argument.
        :param content_base: base path of the content services API.
        :param admin_base: base path of the admin API.
        :param tm1_proxy_base: base path of PAW's TM1 REST proxy. Defaults to the
            legacy ``/api/v0/tm1``; pass
            :data:`~PAWpy.Services.TM1ProxyService.PROXY_PREFIX_V1`
            (``/api/v1/tm1``) on PAW 2.1.21+ / 3.1.8+ (the OAuth-era API).
        :param paw_version: the connected PAW build version (e.g. ``"2.1.21"``).
            Optional — set it (or call :meth:`detect_paw_version`) to enable
            :meth:`supports` / :meth:`assert_supported` version gating. When
            unknown, gating is a no-op (PAWpy never blocks a call solely because
            the version is unknown — see :mod:`PAWpy.version_requirements`).
        :param rest_kwargs: forwarded to :class:`RestService` (auth_mode,
            client_id, port, ssl, verify, timeout, tenant_id, …).
        """
        self._default_database = database
        self._tm1_proxy_base = tm1_proxy_base
        self._paw_version = paw_version
        self._rest = RestService(host=host, **rest_kwargs)

        # Core services
        self.content = ContentService(self._rest, content_base=content_base)
        self.ui = UIService(self._rest)
        self.books = BookService(self._rest, self.content, self.ui)
        self.views = ViewService(self._rest, self.content, self.ui)
        self.admin = AdminService(self._rest, admin_base=admin_base)

        # Cache of per-database TM1 proxy services.
        self._tm1_cache: Dict[str, TM1ProxyService] = {}

    # ------------------------------------------------------------------ #
    # TM1 proxy access
    # ------------------------------------------------------------------ #
    def tm1(self, database: str = None) -> TM1ProxyService:
        """Return a :class:`TM1ProxyService` for *database* (or the default).

        Instances are cached per database name so repeated calls are cheap.
        """
        db = database or self._default_database
        if not db:
            raise ValueError(
                "No TM1 database specified and no default 'database' was set on PAWService"
            )
        if db not in self._tm1_cache:
            self._tm1_cache[db] = TM1ProxyService(self._rest, db, proxy_base=self._tm1_proxy_base)
        return self._tm1_cache[db]

    # ------------------------------------------------------------------ #
    # Instance-level probes (OAuth-era API; PAW 2.1.21+ / 3.1.8+ documents
    # these, availability on older builds is unverified)
    # ------------------------------------------------------------------ #
    def ping(self) -> str:
        """``GET /api/v1/Ping`` — liveness probe; returns the response text."""
        return self._rest.GET("/api/v1/Ping").text

    def health(self) -> Dict:
        """``GET /api/v1/health`` — component health report as parsed JSON."""
        return self._rest.GET("/api/v1/health").json()

    # ------------------------------------------------------------------ #
    # PAW build-version awareness
    # ------------------------------------------------------------------ #
    @property
    def paw_version(self) -> Optional[str]:
        """The connected PAW build version, if known (else ``None``)."""
        return self._paw_version

    @paw_version.setter
    def paw_version(self, value: Optional[str]) -> None:
        self._paw_version = value

    def detect_paw_version(
        self, path: str = "api/v1/version", field: str = "version"
    ) -> Optional[str]:
        """Best-effort: GET *path* and read *field* as the PAW build version.

        PAW builds surface their version inconsistently across deployments, so
        the *path* and JSON *field* are overridable. Returns ``None`` (and
        leaves :attr:`paw_version` untouched) on any failure; on success caches
        and returns the detected version.
        """
        try:
            body = self._rest.GET(path).json()
        except Exception:
            return None
        value = body.get(field) if isinstance(body, dict) else None
        if value:
            self._paw_version = str(value)
        return self._paw_version

    def requires(self, api_group: str) -> str:
        """Minimum PAW build required for *api_group* (``"content"``, ``"admin"``,
        ``"ui"``, ``"auth"``, ``"tm1-proxy"``, ``"tm1-proxy-v1"``,
        ``"content-v1"``). Mirrors a service's ``API_GROUP``. When
        :attr:`paw_version` is known, the minimum for its release line is
        returned (IBM ships features to 2.x and 3.x at different builds).
        """
        return _min_version_for(api_group, self._paw_version)

    def supports(self, api_group: str) -> bool:
        """True if the known :attr:`paw_version` satisfies *api_group*'s minimum.

        Returns ``True`` when the version is unknown (see
        :mod:`PAWpy.version_requirements`).
        """
        return _is_supported(api_group, self._paw_version)

    def assert_supported(self, api_group: str) -> None:
        """Raise :class:`~PAWpy.Exceptions.Exceptions.PAWVersionError` if the
        known PAW version is too old for *api_group*. No-op if version unknown.
        """
        _assert_supported(api_group, self._paw_version)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    @property
    def rest(self) -> RestService:
        return self._rest

    @property
    def base_url(self) -> str:
        return self._rest.base_url

    def logout(self) -> None:
        self._rest.logout()

    def __enter__(self) -> "PAWService":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.logout()
