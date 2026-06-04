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

from typing import Dict

from PAWpy.Services.AdminService import AdminService, DEFAULT_ADMIN_BASE
from PAWpy.Services.BookService import BookService
from PAWpy.Services.ContentService import ContentService, DEFAULT_CONTENT_BASE
from PAWpy.Services.RestService import RestService
from PAWpy.Services.TM1ProxyService import TM1ProxyService
from PAWpy.Services.UIService import UIService
from PAWpy.Services.ViewService import ViewService


class PAWService:
    def __init__(
        self,
        host: str,
        *,
        database: str = None,
        content_base: str = DEFAULT_CONTENT_BASE,
        admin_base: str = DEFAULT_ADMIN_BASE,
        **rest_kwargs,
    ):
        """
        :param host: PAW hostname (no scheme), e.g. ``paw.acme.com``.
        :param database: default TM1 database/server for :meth:`tm1` when called
            with no argument.
        :param content_base: base path of the content services API.
        :param admin_base: base path of the admin API.
        :param rest_kwargs: forwarded to :class:`RestService` (auth_mode,
            client_id, port, ssl, verify, timeout, tenant_id, …).
        """
        self._default_database = database
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
            self._tm1_cache[db] = TM1ProxyService(self._rest, db)
        return self._tm1_cache[db]

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
