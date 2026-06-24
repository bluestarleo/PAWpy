# Changelog

All notable changes to PAWpy are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/bluestarleo/PAWpy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bluestarleo/PAWpy/releases/tag/v0.1.0
