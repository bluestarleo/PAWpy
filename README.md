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
├── ContentService          ← /pacontent/v1/Assets  (legacy OData folders / books / assets)
├── ContentV1Service        ← /api/v1/content  (OAuth-era assets, permissions,
│                             bulk ops, asset types — PAW 2.1.21+/3.1.8+)
├── UserGroupService        ← /api/v1/content/users|groups  (PAW 2.1.21+/3.1.8+)
├── BookService             ← books (type=book/dashboard) over ContentService
├── ViewService             ← views over ContentService
├── AdminService            ← /api/v1/admin  (servers, users, groups)
├── UIService               ← URL builder for /ui?type=… embed endpoints
└── TM1ProxyService         ← /api/v0/tm1/<db>/api/v1/…  (TM1 REST via PAW auth;
                              pass tm1_proxy_base="/api/v1/tm1" on PAW 2.1.21+/3.1.8+)
```

All base paths (`content_base`, `admin_base`) are constructor-overridable, since
they vary across PAW builds (`/pacontent/v1` vs `/api/v1/content`).

## Auth Modes

| Mode | How it works |
|------|--------------|
| `oauth` | Client-credentials grant against an IdP `token_url` → `Authorization: Bearer` (see caveat below) |
| `cam` | CAM namespace login via `POST /login` → `x-csrf-token` — the proven headless mode for on-prem PAW |
| `native` | TM1 native username/password login via `POST /login` → `x-csrf-token` |
| `passport` | Cognos CAM passport (`camid`) via `POST /login` |
| `session` | Inject an existing `csrf_token` / `session_cookie` (dev/test) |

> **On-prem OAuth caveat** (per IBM Docs, "Configuring authorized applications
> (OAuth)"): PAW's built-in OAuth (Administration → Integrations tile,
> PAW 2.1.21+/3.1.8+) supports **only the interactive authorization-code flow**
> (scope `v0userContext`) — *"client credentials (not interactive) flows are
> not supported"* against PAW's own `/oauth2/token`. Use `oauth` mode only
> where an external IdP issues bearer tokens your PAW deployment accepts. For
> **headless/scripted** access to on-prem PAW, use `cam` mode with directory
> credentials (PAW shares the CAM directory with TM1, so TM1 service
> credentials typically work). Authorization-code + refresh-token support is
> on the roadmap.

## Usage

### OAuth (IdP-issued tokens — see caveat above)
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

    # OAuth-era content API (PAW 2.1.21+/3.1.8+): permissions, bulk ops, users
    assets = paw.content_v1.list_children("shared")
    perms  = paw.content_v1.get_effective_permissions(assets[0].id)
    users  = paw.user_groups.get_users()

    # TM1 proxy call (MDX via PAW auth) — returns the raw cellset JSON
    tm1 = paw.tm1("Global FPA")
    data = tm1.execute_mdx("SELECT {[Account].[Revenue]} ON 0 FROM [Revenue Cube]")

    # Embed URL generation (no HTTP call)
    embed = paw.ui.cube_viewer_url("Global FPA", "Revenue Cube", view="Monthly View")
```

### CAM (headless on-prem — recommended for scripts)
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
(`MIN_PAW_VERSION`).

```python
paw = PAWService(host="paw.acme.com", auth_mode="oauth", ..., paw_version="2.1.21")

paw.requires("content")          # -> "2.1.21"  (min PAW build for Content Services)
paw.supports("content")          # -> True / False against the known paw_version
paw.assert_supported("content")  # raises PAWVersionError if the build is too old
paw.detect_paw_version()         # best-effort probe (overridable path/field)
```

When `paw_version` is unknown, gating is a **no-op** — PAWpy never blocks a call
solely because it couldn't determine the version; the server still rejects
genuinely-unsupported requests. The version pins are reconciled on each PAW
release as part of a maintainer-local workflow.

## Coverage & release tracking

PAWpy's endpoint coverage is tracked in a maintainer-local coverage matrix (not
part of this repo). Because the PAW REST API is still growing, it is reconciled
on each PAW release: IBM's endpoint inventory (the IBM-linked Postman collection
or the published API references) is re-pulled and diffed against the matrix to
flag endpoints PAW now exposes that PAWpy doesn't yet wrap, so the wrapper
tracks IBM's cadence instead of drifting. New coverage lands here as `Added`
entries in `CHANGELOG.md` and Roadmap items below.

## Roadmap (aligned with IBM's "future releases" promise)

- [x] Content API v1 (`/api/v1/content`, PAW 2.1.21+/3.1.8+) — `ContentV1Service`:
      assets incl. content retrieval, permissions (get/set/effective),
      bulk copy/move/delete/permissions, asset types
- [x] `UserGroupService` — PAW users/groups reads (`/api/v1/content/users|groups`);
      write endpoints not yet documented by IBM
- [ ] `ViewService` — PAW view CRUD
- [ ] `EmbedTokenService` — generate scoped embed tokens
- [ ] `MCPService` — PAW MCP endpoint integration
- [ ] OAuth authorization-code + refresh-token flow — the only OAuth on-prem
      PAW supports (client-credentials is rejected per IBM Docs)
- [ ] Async support (`aiohttp`)
- [ ] Pydantic models for Books, Assets, Servers
