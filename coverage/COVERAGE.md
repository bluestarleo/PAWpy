# PAWpy Endpoint Coverage Matrix

> **This file is the single source of truth for what PAWpy implements.**
> It is both human-readable and machine-parsed by the local release-tracking
> workflow, which diffs the rows below against the latest PAW Postman collection /
> API reference on every PAW release. **Keep the method and path as the first two
> columns** of each table or the diff parser will skip rows.

- **PAWpy version:** 0.3.0
- **Last reconciled against PAW:** 2026-07-20 — Postman collection "Planning
  Analytics" (public workspace `martian-comet-648710/planning-analytics`,
  IBM-affiliated author, collection rev 49790523243). The collection documents
  the **OAuth-era API** ("requires PAW 2.1.21/3.1.8 or later") and does *not*
  cover the legacy surfaces (`/pacontent/v1`, `/api/v1/admin`, `/ui`, `/login`)
  — their rows are retained, no evidence of removal.
- Previous reconcile: 2026-06-23 (PA 2.1.x API references)

PAWpy is versioned against **two** axes: its own semver (`PAWpy.__version__`) and
the **minimum PAW build** each API group needs. The per-group minimums below are
the source of truth mirrored by `PAWpy/version_requirements.py` (`MIN_PAW_VERSION`)
and each service's `API_GROUP` / `requires()`. The `Since PAW` column on each
endpoint records when that specific endpoint first appeared. Reconcile both from
IBM PAW release notes; mark anything unconfirmed `UNVERIFIED`.

## PAW version requirements (per API group)

| API group | Min PAW build | PAWpy surface | Notes |
|-----------|---------------|---------------|-------|
| auth | 2.0.0 | RestService (login/logout/oauth) | baseline |
| ui | 2.0.0 | UIService | baseline (embed-URL builder) |
| tm1-proxy | 2.0.0 | TM1ProxyService | baseline (TM1 REST via legacy `/api/v0/tm1` proxy) |
| admin | 2.0.0 | AdminService | baseline |
| content | 2.1.21 | ContentService / BookService / ViewService | `/pacontent/v1` — UNVERIFIED, confirm vs IBM notes |
| tm1-proxy-v1 | 2.1.21 (2.x) / 3.1.8 (3.x) | TM1ProxyService(`proxy_base=PROXY_PREFIX_V1`) | `/api/v1/tm1` proxy — per the 2026-06 Postman collection ("requires 2.1.21/3.1.8+") |
| content-v1 | 2.1.21 (2.x) / 3.1.8 (3.x) | *(planned)* | `/api/v1/content` — folder tagged "new in 2.1.21 & 3.1.8" in the collection |

IBM ships features to the 2.x and 3.x release lines at different builds
("new in 2.1.21 **&** 3.1.8"), so dual-line groups carry **per-line minimums**
(`MIN_PAW_VERSION_BY_LINE` in `version_requirements.py`) — a 3.x build below
3.1.8 does not qualify merely by exceeding 2.1.21.

## Status legend

| Status | Meaning |
|--------|---------|
| `implemented` | A typed PAWpy method calls this endpoint. |
| `generic` | Reachable only through a generic pass-through (`AdminService.get`, `TM1ProxyService.get/post`) — no typed wrapper yet. |
| `partial` | Wrapped but missing documented options/variants. |
| `planned` | On the roadmap, not yet implemented. |
| `not-implemented` | Documented by IBM, no PAWpy coverage. New rows added by the diff land here. |

## Content Services API — `/pacontent/v1`

| Method | Path | API | PAWpy | Status | Since PAW |
|--------|------|-----|-------|--------|-----------|
| GET | /pacontent/v1/Assets('{id}') | content | ContentService.get | implemented | 2.1.21 |
| GET | /pacontent/v1/Assets(path='{path}') | content | ContentService.get_by_path | implemented | 2.1.21 |
| GET | /pacontent/v1/Assets(path='{path}')/Assets | content | ContentService.list_children | implemented | 2.1.21 |
| GET | /pacontent/v1/Assets | content | ContentService.list_children (path-scoped only) | partial | 2.1.21 |
| POST | /pacontent/v1/Assets | content | ContentService.create | implemented | 2.1.21 |
| PUT | /pacontent/v1/Assets(id='{id}',type='{type}') | content | ContentService.update | implemented | 2.1.21 |
| DELETE | /pacontent/v1/Assets(id='{id}',type='{type}') | content | ContentService.delete | implemented | 2.1.21 |
| DELETE | /pacontent/v1/Assets(path='{path}') | content | ContentService.delete_by_path | implemented | 2.1.21 |

## Admin API — `/api/v1/admin`

| Method | Path | API | PAWpy | Status | Since PAW |
|--------|------|-----|-------|--------|-----------|
| GET | /api/v1/admin/servers | admin | AdminService.get_tm1_servers | implemented | 2.0.0 |
| GET | /api/v1/admin/users | admin | AdminService.get_users | implemented | 2.0.0 |
| GET | /api/v1/admin/groups | admin | AdminService.get_groups | implemented | 2.0.0 |
| GET | /api/v1/admin/{resource} | admin | AdminService.get (generic) | generic | 2.0.0 |

## PAW instance endpoints — `/api/v1` (OAuth-era)

Documented in the 2026-06 Postman collection without a "new in" tag, so their
introduction build is unconfirmed.

| Method | Path | API | PAWpy | Status | Since PAW |
|--------|------|-----|-------|--------|-----------|
| GET | /api/v1/Ping | admin | PAWService.ping | implemented | UNVERIFIED |
| GET | /api/v1/health | admin | PAWService.health | implemented | UNVERIFIED |
| GET | /api/v1/tm1/Servers | admin | AdminService.get_databases | implemented | UNVERIFIED |

## Content API v1 — `/api/v1/content` (new in PAW 2.1.21 & 3.1.8)

The OAuth-era successor to `/pacontent/v1`: different casing (`assets`), no
`type` predicate on delete, plus genuinely new capabilities — asset content
retrieval, permissions, bulk operations, asset types, and PAW users/groups.
Planned as a ContentService v1 mode + `UserGroupService` (see README Roadmap).

| Method | Path | API | PAWpy | Status | Since PAW |
|--------|------|-----|-------|--------|-----------|
| GET | /api/v1/content/assets('{id}') | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/assets(path='{path}')/assets | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/assets('{id}')/content | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| POST | /api/v1/content/assets(path='{path}')/assets | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| DELETE | /api/v1/content/assets('{id}') | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/assets('{id}')/permissions | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| PUT | /api/v1/content/assets('{id}')/permissions | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/assets('{id}')/effectivepermissions | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| POST | /api/v1/content/bulkcopy | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| POST | /api/v1/content/bulkdelete | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| POST | /api/v1/content/bulkmove | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| POST | /api/v1/content/bulkpermissions | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/assettypes | content-v1 | — | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/users | content-v1 | — (roadmap: UserGroupService) | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/users('{id}') | content-v1 | — (roadmap: UserGroupService) | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/groups | content-v1 | — (roadmap: UserGroupService) | planned | 2.1.21 / 3.1.8 |
| GET | /api/v1/content/groups('{id}') | content-v1 | — (roadmap: UserGroupService) | planned | 2.1.21 / 3.1.8 |

## Auth — login / token

| Method | Path | API | PAWpy | Status | Since PAW |
|--------|------|-----|-------|--------|-----------|
| POST | /login | auth | RestService._login (cam/native/passport) | implemented | 2.0.0 |
| POST | /logout | auth | RestService.logout | implemented | 2.0.0 |
| POST | {token_url} | auth | RestService._fetch_oauth_token (client-credentials) | implemented | 2.0.0 |

## UI API — `/ui` (embed-URL builder, no HTTP call)

| Method | Path | API | PAWpy | Status | Since PAW |
|--------|------|-----|-------|--------|-----------|
| GET | /ui?type=book | ui | UIService.book_url | implemented | 2.0.0 |
| GET | /ui?type=cube-viewer | ui | UIService.cube_viewer_url | implemented | 2.0.0 |
| GET | /ui?type=dimension-editor | ui | UIService.dimension_editor_url | implemented | 2.0.0 |
| GET | /ui?type=set-editor | ui | UIService.set_editor_url | implemented | 2.0.0 |
| GET | /ui?type=websheet | ui | UIService.websheet_url | implemented | 2.0.0 |

## TM1 proxy — `/api/v0/tm1/{db}/api/v1/...` (legacy) and `/api/v1/tm1/{db}/api/v1/...` (2.1.21+/3.1.8+)

The full TM1 REST surface is reachable through PAW's proxy via the generic
pass-throughs, so the whole family is `generic` unless a typed helper exists.
Diff hits under either prefix are TM1 REST endpoints (TM1py territory), not new
*PAW* surface — triage them as "covered by generic proxy" unless a typed
convenience method is wanted (both prefixes are also in the IGNORE block below
so they stop surfacing). The v1 prefix is selected with
`TM1ProxyService(..., proxy_base=PROXY_PREFIX_V1)` or
`PAWService(..., tm1_proxy_base="/api/v1/tm1")`; typed helpers work identically
against either prefix. TM1-database start/stop and async-status polling
(`POST {proxy root}`, `GET {proxy root}/{asyncId}`) ride the same pass-throughs.

| Method | Path | API | PAWpy | Status | Since PAW |
|--------|------|-----|-------|--------|-----------|
| GET | /api/v0/tm1/{db}/api/v1/{tm1_path} | tm1-proxy | TM1ProxyService.get (generic) | generic | 2.0.0 |
| POST | /api/v0/tm1/{db}/api/v1/{tm1_path} | tm1-proxy | TM1ProxyService.post (generic) | generic | 2.0.0 |
| PATCH | /api/v0/tm1/{db}/api/v1/{tm1_path} | tm1-proxy | TM1ProxyService.patch (generic) | generic | 2.0.0 |
| PUT | /api/v0/tm1/{db}/api/v1/{tm1_path} | tm1-proxy | TM1ProxyService.put (generic) | generic | 2.0.0 |
| DELETE | /api/v0/tm1/{db}/api/v1/{tm1_path} | tm1-proxy | TM1ProxyService.delete (generic) | generic | 2.0.0 |
| GET | /api/v1/tm1/{db}/api/v1/{tm1_path} | tm1-proxy-v1 | TM1ProxyService.get (generic) | generic | 2.1.21 / 3.1.8 |
| POST | /api/v1/tm1/{db}/api/v1/{tm1_path} | tm1-proxy-v1 | TM1ProxyService.post (generic) | generic | 2.1.21 / 3.1.8 |
| PATCH | /api/v1/tm1/{db}/api/v1/{tm1_path} | tm1-proxy-v1 | TM1ProxyService.patch (generic) | generic | 2.1.21 / 3.1.8 |
| PUT | /api/v1/tm1/{db}/api/v1/{tm1_path} | tm1-proxy-v1 | TM1ProxyService.put (generic) | generic | 2.1.21 / 3.1.8 |
| DELETE | /api/v1/tm1/{db}/api/v1/{tm1_path} | tm1-proxy-v1 | TM1ProxyService.delete (generic) | generic | 2.1.21 / 3.1.8 |
| GET | /api/v0/tm1/{db}/api/v1/Cubes | tm1-proxy | TM1ProxyService.get_cubes | implemented | 2.0.0 |
| GET | /api/v0/tm1/{db}/api/v1/Cubes('{cube}')/Dimensions | tm1-proxy | TM1ProxyService.get_cube_dimensions | implemented | 2.0.0 |
| GET | /api/v0/tm1/{db}/api/v1/Dimensions | tm1-proxy | TM1ProxyService.get_dimensions | implemented | 2.0.0 |
| GET | /api/v0/tm1/{db}/api/v1/Cubes('{cube}')/Views | tm1-proxy | TM1ProxyService.get_views | implemented | 2.0.0 |
| POST | /api/v0/tm1/{db}/api/v1/ExecuteMDX | tm1-proxy | TM1ProxyService.execute_mdx | implemented | 2.0.0 |

## Environment migration — `/api/v0/neo/idvisualizations/migrate/v1/...`

Present in the 2026-06 Postman collection but folder-labeled **"(unsupported)"**
by its IBM-affiliated author. Deliberately not wrapped and ignore-listed below;
revisit if IBM ever documents it as supported.

## Ignore list (not endpoints to wrap)

Path families the diff should treat as out-of-scope noise rather than gaps.
One canonicalized prefix per line, `#` comments allowed.

<!-- IGNORE
# OAuth/identity-provider token endpoints live outside PAW
/oauth2
/oidc
# Static assets / health probes
/health
/ping
/v1/ready
# TM1 REST surface behind PAW's proxy — TM1py territory, covered by the
# generic TM1ProxyService pass-throughs (get/post/patch/put/delete)
/api/v0/tm1/{}/api/v1
/api/v1/tm1/{}/api/v1
# SaaS tenant-prefixed sample URLs that appear in the Postman collection
/api/{}/v0/tm1
# Environment migration API — explicitly "(unsupported)" in IBM's collection
/api/v0/neo/idvisualizations/migrate
-->
