# Changelog

All notable changes to PAWpy are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-09-18

### Added
- `DatabaseService` (`paw.databases`) — the `/api/v1/databases` administration
  API from IBM's Postman collection folder "Databases (2.1.24 & 3.1.11)":
  list databases; start / stop / force-stop (`endProcess`) / restart; TM1 12
  database create / delete; manual & automatic backup list, create, download,
  delete. New API group `databases` (min PAW 2.1.24 / 3.1.11, **UNVERIFIED**:
  pre-release at reconcile time — IBM Docs' latest GA What's new was 2.1.23).
  Base path overridable via `PAWService(databases_base=...)`.
- `UserAdminService` (`paw.user_admin`) — the write-capable `/api/v1/useradmin`
  API (collection folder "User admin (2.1.25 & 3.1.12)"): user CRUD, profile /
  roles / groups / environments per user, bulk role & state changes, CSV
  export/import; group CRUD (create / replace / patch / delete, bulk delete),
  membership add/remove, CSV export, bulk add; roles, quota, environments,
  copy/remove users across environments. New API group `useradmin` (min PAW
  2.1.25 / 3.1.12, **UNVERIFIED**). Base path overridable via
  `PAWService(useradmin_base=...)`.
- `CloudAdminService` (`paw.cloud_admin`) — the **PA on Cloud (SaaS) only**
  `/api/v1/cloudadmin` API (collection folder "PA on Cloud Admin (2.1.24 &
  3.1.11)"): subscription details / list / per-user, add users to and revoke
  subscriptions, invite one or many users. New API group `cloudadmin` (min PAW
  2.1.24 / 3.1.11, **UNVERIFIED**; cannot be live-validated on-prem). Base
  path overridable via `PAWService(cloudadmin_base=...)`.
- `TM1ProxyService.get_metrics(cube=None, database_only=False, filter=None)`
  — typed helper for the TM1 Metrics API (`GET {db}/api/v1/Metrics()`, the
  endpoint IBM's PAW 2.1.22 "What's coming next" page cites for the Agent MCP
  metrics tool), with `$filter` shortcuts for one cube or database-level rows.
- `PAWpy.Services` now also exports `ContentV1Service`, `UserGroupService`,
  `DatabaseService`, `UserAdminService`, `CloudAdminService`.
- Offline tests for the new services' wiring, base overrides, version gating,
  backup-type validation and the metrics `$filter` shortcuts.

### Changed
- Coverage reconciled 2026-09-18 against IBM's Postman collection rev
  51028184402 (updated 2026-09-01; was 49790523243): 50 new endpoints, all
  triaged and wrapped (one `partial`: `POST /useradmin/groups/bulk`, whose
  payload IBM's example leaves empty). No MCP requests in the collection and
  still no official Swagger/OpenAPI page — the MCP scope decision stays open.
  IBM Docs' REST API overview now lists MCP as PAW's third API class; the
  2.1.22 release (26 June 2026) consolidated all Planning Analytics Agent MCP
  tools under the unified `/ibm-pa-tools` endpoint and removed the discrete
  cube-tools/analysis-tools endpoints.
- `content` API group minimum PAW build corrected from `2.1.21` (UNVERIFIED) to
  the `2.0.0` baseline in `version_requirements.py` and `coverage/COVERAGE.md`
  (incl. the `/pacontent/v1` rows' `Since PAW` cells): the Content Services API
  is the legacy pre-2.1.21 surface per IBM's reference, and 0.4.1's live
  validation confirmed it works on a 2.0.x build. Version gating no longer
  wrongly blocks `ContentService` on pre-2.1.21 deployments with a detected
  PAW version.
- Roadmap: MCP scope decision queued for PAW 2.1.22 (unified `/ibm-pa-tools`
  endpoint, breaking) and an optional typed `TM1ProxyService.get_metrics()`
  helper (TM1 Metrics API), per the 2026-07-22 PAW REST API research
  assessment.

## [0.4.1] - 2026-07-20

### Changed
- Repository anonymized for open-source distribution: examples now use IBM's
  public Planning Sample database objects; author/maintainer metadata is
  `PAWpy Maintainers <opensource@example.com>`; LICENSE copyright holder is
  "PAWpy contributors". No functional changes.
- README auth guidance corrected per IBM Docs and live validation: on-prem
  PAW's built-in OAuth supports only the interactive authorization-code flow
  (scope `v0userContext`) — client-credentials is not accepted by PAW's own
  `/oauth2/token`, so `oauth` mode applies to IdP-issued tokens only. `cam`
  mode is now documented as the recommended headless path for on-prem PAW
  (verified against a live 2.0.x deployment: login, `/pacontent/v1` content
  and the `/api/v0/tm1` proxy all work; `/api/v1/*` 404s on pre-2.1.21
  builds). Roadmap item updated to authorization-code + refresh-token flow.

## [0.4.0] - 2026-07-20

### Added
- `ContentV1Service` (`paw.content_v1`) — the OAuth-era `/api/v1/content` API
  (PAW 2.1.21+/3.1.8+): asset get/list/create/delete, content retrieval,
  permissions (get/set/effective), bulk copy/move/delete/permissions, and
  asset types. Base path overridable via `PAWService(content_v1_base=...)`.
- `UserGroupService` (`paw.user_groups`) — PAW users/groups reads
  (`/api/v1/content/users|groups`); returns the principal ids consumed by the
  permissions endpoints.

## [0.3.0] - 2026-07-20

### Added
- Support for PAW's OAuth-era (2.1.21+/3.1.8+) TM1 proxy path `/api/v1/tm1`:
  `TM1ProxyService` accepts `proxy_base` (new `PROXY_PREFIX_V1` constant) and
  `PAWService` accepts `tm1_proxy_base`. The legacy `/api/v0/tm1` remains the
  default.
- `TM1ProxyService.patch/put/delete` generic pass-throughs (previously only
  `get`/`post`), completing verb coverage for the proxied TM1 REST surface.
- `PAWService.ping()` (`GET /api/v1/Ping`) and `PAWService.health()`
  (`GET /api/v1/health`).
- `AdminService.get_databases()` — `GET /api/v1/tm1/Servers`, the OAuth-era
  successor to `get_tm1_servers()`.
- Per-release-line version minimums (`MIN_PAW_VERSION_BY_LINE`): dual-track
  IBM features ("new in 2.1.21 & 3.1.8") now gate correctly on 3.x builds
  below 3.1.8. New API groups `tm1-proxy-v1` and `content-v1`.

### Changed
- `coverage/COVERAGE.md` reconciled against the IBM-affiliated "Planning
  Analytics" Postman collection (2026-07-20): new sections for the
  `/api/v1/content` Content API v1 (assets content/permissions/bulk
  ops/assettypes, PAW users/groups — recorded as `planned`), PAW instance
  endpoints, and the v1 TM1 proxy; environment-migration API ignore-listed as
  IBM-unsupported.

## [0.2.0] - 2026-06-24

### Added
- PAW build-version awareness: `PAWpy/version_requirements.py` declares the
  minimum PAW build per API group (`MIN_PAW_VERSION`); each service exposes an
  `API_GROUP`; `PAWService` gains `paw_version`, `requires()`, `supports()`,
  `assert_supported()`, and a best-effort `detect_paw_version()`. New
  `PAWVersionError`.
- `coverage/COVERAGE.md` — endpoint coverage matrix (source of truth for what
  PAWpy wraps) with per-group minimum-PAW-build and `Since PAW` columns, reconciled
  on each PAW release against IBM's endpoint inventory to flag endpoints PAWpy
  doesn't yet wrap.

## [0.1.0] - 2026-06-03

### Added
- Initial release.
- `PAWService` top-level entry point (mirrors TM1py's `TM1Service`).
- `RestService` — session/auth backbone with `oauth`, `cam`, `native`,
  `passport`, and `session` auth modes; typed `GET/POST/PATCH/PUT/DELETE`.
- `ContentService` — OData CRUD over `/pacontent/v1/Assets`
  (`$filter/$select/$expand/$orderby/$top/$skip`).
- `BookService` and `ViewService` — convenience layers over content + embed URLs.
- `AdminService` — `/api/v1/admin` (servers, users, groups) + generic `get()`.
- `UIService` — pure URL builder for `/ui?type=…` embed endpoints.
- `TM1ProxyService` — TM1 REST via PAW's `/api/v0/tm1/<db>/api/v1/…` proxy
  (cubes, dimensions, views, `ExecuteMDX`).
- Typed exception hierarchy (`PAWException` and subclasses).
- 14 offline tests covering URL building, OData/path encoding, and config validation.

[Unreleased]: https://github.com/bluestarleo/PAWpy/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/bluestarleo/PAWpy/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/bluestarleo/PAWpy/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/bluestarleo/PAWpy/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/bluestarleo/PAWpy/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bluestarleo/PAWpy/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/bluestarleo/PAWpy/releases/tag/v0.1.0
