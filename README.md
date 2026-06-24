# PAWpy — Planning Analytics Workspace REST API Wrapper

[![PyPI version](https://img.shields.io/pypi/v/PAWpy.svg)](https://pypi.org/project/PAWpy/)
[![Python versions](https://img.shields.io/pypi/pyversions/PAWpy.svg)](https://pypi.org/project/PAWpy/)
[![License: MIT](https://img.shields.io/pypi/l/PAWpy.svg)](https://github.com/bluestarleo/PAWpy/blob/main/LICENSE)

A TM1py-inspired Python wrapper for the PAW REST API.

## Install

```bash
uv sync --extra dev         # installs PAWpy + pytest
uv run python -m pytest     # 21 offline tests (no live server needed)
```

Requires Python ≥3.11 and `requests`. The URL-builder calls (`paw.ui.*`,
`*.get_embed_url`) make no network request and work without a live PAW server.

## Releasing

Publishing is automated by `.github/workflows/publish.yml` via PyPI
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no API
token stored). To cut a release:

1. Bump `version` in `pyproject.toml` and add a `CHANGELOG.md` entry.
2. One-time on PyPI: add a Trusted Publisher for project `PAWpy` →
   `bluestarleo/PAWpy`, workflow `publish.yml`, environment `pypi`.
3. Tag and push:
   ```bash
   git tag v0.1.0 && git push origin v0.1.0
   ```
The workflow runs the tests (3.11–3.13), builds, checks the tag matches the
package version, and publishes the sdist + wheel to PyPI.

## Architecture

```
PAWService                  ← top-level entry point (mirrors TM1py's TM1Service)
├── RestService             ← session + auth + GET/POST/PATCH/PUT/DELETE core
├── ContentService          ← /pacontent/v1/Assets  (OData folders / books / assets)
├── BookService             ← books (type=book/dashboard) over ContentService
├── ViewService             ← views over ContentService
├── AdminService            ← /api/v1/admin  (servers, users, groups)
├── UIService               ← URL builder for /ui?type=… embed endpoints
└── TM1ProxyService         ← /api/v0/tm1/<db>/api/v1/…  (TM1 REST via PAW auth)
```

All base paths (`content_base`, `admin_base`) are constructor-overridable, since
they vary across PAW builds (`/pacontent/v1` vs `/api/v1/content`).

## Auth Modes

| Mode | How it works |
|------|--------------|
| `oauth` | Client-credentials grant against `token_url` → `Authorization: Bearer` |
| `cam` | CAM namespace login via `POST /login` → `x-csrf-token` |
| `native` | TM1 native username/password login via `POST /login` → `x-csrf-token` |
| `passport` | Cognos CAM passport (`camid`) via `POST /login` |
| `session` | Inject an existing `csrf_token` / `session_cookie` (dev/test) |

## Usage

### OAuth (Recommended)
```python
from PAWpy import PAWService

with PAWService(
    host="paw.mycompany.com",
    auth_mode="oauth",
    client_id="my-client-id",
    client_secret="my-client-secret",
    token_url="https://idp.mycompany.com/oauth2/token",  # required for oauth
    scope="paw",                    # optional
    database="Global FPA",          # optional default TM1 database
) as paw:

    # List books in a folder (returns Asset objects)
    books = paw.books.get_all("/shared/FP&A")

    # Get embed URL for an iframe (no HTTP call)
    url = paw.books.get_embed_url("/shared/FP&A/Monthly Report")

    # List registered TM1 servers
    servers = paw.admin.get_tm1_servers()

    # TM1 proxy call (MDX via PAW auth) — returns the raw cellset JSON
    tm1 = paw.tm1("Global FPA")
    data = tm1.execute_mdx("SELECT {[Account].[Revenue]} ON 0 FROM [Revenue Cube]")

    # Embed URL generation (no HTTP call)
    embed = paw.ui.cube_viewer_url("Global FPA", "Revenue Cube", view="Monthly View")
```

### Legacy CAM
```python
with PAWService(
    host="paw.mycompany.com",
    auth_mode="cam",
    namespace="LDAP",
    username="my-username",
    password="secret",
) as paw:
    ...
```

### Multi-tenant (PAW Cloud)
```python
with PAWService(
    host="planning-analytics.cloud.ibm.com",
    tenant_id="my-tenant-id",
    auth_mode="oauth",
    client_id="...",
    client_secret="...",
) as paw:
    ...
```

## Mapping to TM1py

| TM1py | PAWpy |
|-------|-------|
| `TM1Service` | `PAWService` |
| `CubeService` | `TM1ProxyService` (via PAW) |
| `DimensionService` | `TM1ProxyService` (via PAW) |
| `ProcessService` | `TM1ProxyService` (via PAW) |
| *(no equivalent)* | `BookService` |
| *(no equivalent)* | `ContentService` |
| *(no equivalent)* | `AdminService` |
| *(no equivalent)* | `UIService` |

## Versioning against PAW builds

The PAW REST API is still incomplete and grows with each IBM release, so PAWpy is
versioned against **two** axes: its own semver (`PAWpy.__version__`) and the
**minimum PAW build** each API group requires. Each service declares its
`API_GROUP`; the per-group minimums live in `PAWpy/version_requirements.py`
(`MIN_PAW_VERSION`) and are mirrored in `coverage/COVERAGE.md`.

```python
paw = PAWService(host="paw.acme.com", auth_mode="oauth", ..., paw_version="2.1.21")

paw.requires("content")          # -> "2.1.21"  (min PAW build for Content Services)
paw.supports("content")          # -> True / False against the known paw_version
paw.assert_supported("content")  # raises PAWVersionError if the build is too old
paw.detect_paw_version()         # best-effort probe (overridable path/field)
```

When `paw_version` is unknown, gating is a **no-op** — PAWpy never blocks a call
solely because it couldn't determine the version; the server still rejects
genuinely-unsupported requests. The coverage matrix and its per-group version
table are reconciled on each PAW release as part of a local maintenance workflow.

## Coverage matrix & release tracking

`coverage/COVERAGE.md` is the source of truth for which PAW endpoints PAWpy wraps
and which PAW build each needs. Because the PAW REST API is still growing, the
matrix is reconciled on each PAW release: IBM's endpoint inventory (a Postman
collection export or the published API references) is re-pulled and diffed
against the matrix to flag endpoints PAW now exposes that PAWpy doesn't yet wrap,
so the wrapper tracks IBM's cadence instead of drifting.

## Roadmap (aligned with IBM's "future releases" promise)

- [ ] `ViewService` — PAW view CRUD
- [ ] `UserGroupService` — full user/group management
- [ ] `EmbedTokenService` — generate scoped embed tokens
- [ ] `MCPService` — PAW MCP endpoint integration
- [ ] Token refresh / OAuth expiry handling
- [ ] Async support (`aiohttp`)
- [ ] Pydantic models for Books, Assets, Servers
