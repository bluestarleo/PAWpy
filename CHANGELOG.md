# Changelog

All notable changes to PAWpy are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
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

[Unreleased]: https://github.com/bluestarleo/PAWpy/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/bluestarleo/PAWpy/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/bluestarleo/PAWpy/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bluestarleo/PAWpy/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/bluestarleo/PAWpy/releases/tag/v0.1.0
