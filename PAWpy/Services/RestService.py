"""RestService — the HTTP + authentication backbone of PAWpy.

This is the PAW analogue of TM1py's ``RestService``. It owns a persistent
``requests.Session``, builds the base URL, performs authentication according to
the selected ``auth_mode``, attaches the right credentials to every request
(Bearer token for OAuth, ``x-csrf-token`` + cookies for login-based modes), and
exposes thin ``GET/POST/PATCH/PUT/DELETE`` helpers that raise typed exceptions
on failure.

Auth modes (see README):
    oauth   — OAuth client-credentials grant -> ``Authorization: Bearer <tok>``
    cam     — Cognos CAM namespace login via POST /login -> x-csrf-token
    native  — TM1 native username/password login via POST /login
    passport— Cognos CAM passport (camid cookie) via POST /login
    session — inject an existing browser session cookie / csrf token (dev/test)

PAW only documents a few authoritative facts about its wire protocol, so this
class deliberately keeps the auth header/cookie handling configurable rather
than hard-coding one deployment's behaviour.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Mapping, Optional
from urllib.parse import quote, urlencode

import requests

from PAWpy.Exceptions.Exceptions import (
    PAWAuthenticationException,
    PAWConfigException,
    PAWNotFoundException,
    PAWRestException,
    PAWTimeoutException,
)

# Auth modes that authenticate by POSTing to /login and then carry an
# x-csrf-token header + session cookies on subsequent requests.
_LOGIN_MODES = {"cam", "native", "passport"}
_VALID_MODES = _LOGIN_MODES | {"oauth", "session"}

# HTTP methods that PAW requires the CSRF token on (anything that mutates state).
_CSRF_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


class RestService:
    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        ssl: bool = True,
        base_path: str = "",
        auth_mode: str = "oauth",
        # --- OAuth ---
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
        scope: Optional[str] = None,
        access_token: Optional[str] = None,
        # --- login modes (cam / native / passport) ---
        username: Optional[str] = None,
        password: Optional[str] = None,
        namespace: Optional[str] = None,
        camid: Optional[str] = None,
        # --- session mode ---
        csrf_token: Optional[str] = None,
        session_cookie: Optional[str] = None,
        # --- multi-tenant cloud ---
        tenant_id: Optional[str] = None,
        # --- transport options ---
        verify: bool = True,
        timeout: float = 60.0,
        proxies: Optional[Mapping[str, str]] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        connect: bool = True,
    ):
        self._auth_mode = (auth_mode or "").lower()
        if self._auth_mode not in _VALID_MODES:
            raise PAWConfigException(
                f"Unknown auth_mode '{auth_mode}'. Valid: {sorted(_VALID_MODES)}"
            )

        self._host = host.rstrip("/")
        self._port = port
        self._ssl = ssl
        self._base_path = ("/" + base_path.strip("/")) if base_path.strip("/") else ""
        self._tenant_id = tenant_id

        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._scope = scope
        self._access_token = access_token
        self._token_expires_at: Optional[float] = None

        self._username = username
        self._password = password
        self._namespace = namespace
        self._camid = camid

        self._csrf_token = csrf_token
        self._session_cookie = session_cookie

        self._verify = verify
        self._timeout = timeout
        self._extra_headers = dict(extra_headers or {})

        self._session = requests.Session()
        self._session.verify = verify
        if proxies:
            self._session.proxies.update(proxies)
        if session_cookie:
            # session_cookie is a raw "name=value; name2=value2" cookie string.
            for pair in session_cookie.split(";"):
                if "=" in pair:
                    name, _, value = pair.strip().partition("=")
                    self._session.cookies.set(name, value)

        self._base_url = self._build_base_url()

        if connect:
            self.connect()

    # ------------------------------------------------------------------ #
    # URL construction
    # ------------------------------------------------------------------ #
    @property
    def base_url(self) -> str:
        return self._base_url

    def _build_base_url(self) -> str:
        scheme = "https" if self._ssl else "http"
        netloc = self._host
        if self._port:
            netloc = f"{netloc}:{self._port}"
        url = f"{scheme}://{netloc}"
        if self._tenant_id:
            url = f"{url}/{self._tenant_id.strip('/')}"
        return url + self._base_path

    def build_url(self, path: str, params: Optional[Mapping[str, Any]] = None) -> str:
        """Join *path* onto the base URL and append a query string.

        ``path`` may be absolute (``/ui?...``) or relative (``Cubes``). Already
        URL-encoded paths are passed through untouched.
        """
        if path.startswith(("http://", "https://")):
            url = path
        else:
            url = f"{self._base_url}/{path.lstrip('/')}"
        if params:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{urlencode(params, quote_via=quote)}"
        return url

    # ------------------------------------------------------------------ #
    # Authentication
    # ------------------------------------------------------------------ #
    def connect(self) -> None:
        if self._auth_mode == "oauth":
            if not self._access_token:
                self._fetch_oauth_token()
        elif self._auth_mode in _LOGIN_MODES:
            self._login()
        elif self._auth_mode == "session":
            if not (self._csrf_token or self._session_cookie):
                raise PAWConfigException(
                    "auth_mode='session' requires csrf_token and/or session_cookie"
                )

    def _fetch_oauth_token(self) -> None:
        if not self._token_url:
            raise PAWConfigException("auth_mode='oauth' requires token_url")
        if not (self._client_id and self._client_secret):
            raise PAWConfigException(
                "auth_mode='oauth' requires client_id and client_secret"
            )
        data = {"grant_type": "client_credentials"}
        if self._scope:
            data["scope"] = self._scope
        try:
            resp = self._session.post(
                self._token_url,
                data=data,
                auth=(self._client_id, self._client_secret),
                headers={"Accept": "application/json"},
                timeout=self._timeout,
                verify=self._verify,
            )
        except requests.Timeout:
            raise PAWTimeoutException("POST", self._token_url, self._timeout)
        if not resp.ok:
            raise PAWAuthenticationException(
                f"OAuth token request failed: {resp.status_code} {resp.reason} — {resp.text[:500]}"
            )
        payload = resp.json()
        self._access_token = payload.get("access_token")
        if not self._access_token:
            raise PAWAuthenticationException(
                f"OAuth token response missing 'access_token': {payload}"
            )
        expires_in = payload.get("expires_in")
        if expires_in:
            # refresh 30s early to avoid using a token that expires mid-flight
            self._token_expires_at = time.time() + float(expires_in) - 30

    def _login(self) -> None:
        """POST /login per the PAW UI API; store the returned x-csrf-token."""
        body: Dict[str, str] = {}
        if self._auth_mode == "passport":
            if not self._camid:
                raise PAWConfigException("auth_mode='passport' requires camid")
            body["camid"] = self._camid
        else:  # cam / native
            if not (self._username and self._password):
                raise PAWConfigException(
                    f"auth_mode='{self._auth_mode}' requires username and password"
                )
            body["username"] = self._username
            body["password"] = self._password
            if self._namespace:
                body["namespace"] = self._namespace

        url = self.build_url("login")
        try:
            resp = self._session.post(
                url,
                json=body,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=self._timeout,
                verify=self._verify,
            )
        except requests.Timeout:
            raise PAWTimeoutException("POST", url, self._timeout)
        if not resp.ok:
            raise PAWAuthenticationException(
                f"Login failed: {resp.status_code} {resp.reason} — {resp.text[:500]}"
            )
        # The csrf token is returned either as a header or a cookie depending on
        # the PAW build; capture whichever is present.
        token = resp.headers.get("x-csrf-token") or self._session.cookies.get("ba-sso-csrf")
        if token:
            self._csrf_token = token

    def _ensure_token_fresh(self) -> None:
        if self._auth_mode != "oauth":
            return
        if self._token_expires_at and time.time() >= self._token_expires_at:
            self._fetch_oauth_token()

    # ------------------------------------------------------------------ #
    # Headers
    # ------------------------------------------------------------------ #
    def _build_headers(self, method: str, extra: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        headers.update(self._extra_headers)
        if self._auth_mode == "oauth" and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        if self._csrf_token and method.upper() in _CSRF_METHODS:
            headers["x-csrf-token"] = self._csrf_token
        if extra:
            headers.update(extra)
        return headers

    # ------------------------------------------------------------------ #
    # Core request
    # ------------------------------------------------------------------ #
    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
        expect_json: bool = True,
    ) -> requests.Response:
        self._ensure_token_fresh()
        method = method.upper()
        url = self.build_url(path, params)
        req_headers = self._build_headers(method, headers)
        try:
            resp = self._session.request(
                method,
                url,
                json=json,
                data=data,
                headers=req_headers,
                timeout=timeout or self._timeout,
                verify=self._verify,
            )
        except requests.Timeout:
            raise PAWTimeoutException(method, url, timeout or self._timeout)

        if not resp.ok:
            exc_cls = PAWNotFoundException if resp.status_code == 404 else PAWRestException
            raise exc_cls(resp.status_code, resp.reason, method, url, resp.text)
        return resp

    def GET(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def POST(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def PATCH(self, path: str, **kwargs) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def PUT(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def DELETE(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def logout(self) -> None:
        # Best-effort: PAW exposes POST /logout in login-based deployments.
        try:
            if self._auth_mode in _LOGIN_MODES:
                self._session.post(
                    self.build_url("logout"),
                    headers=self._build_headers("POST"),
                    timeout=self._timeout,
                    verify=self._verify,
                )
        except Exception:
            pass
        finally:
            self._session.close()

    def __enter__(self) -> "RestService":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.logout()
