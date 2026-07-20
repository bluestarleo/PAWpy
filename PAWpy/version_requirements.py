"""PAW build-version requirements per API group.

PAWpy wraps the PAW REST API, which — unlike the mature TM1 REST API behind
TM1py — is still incomplete and grows release-to-release. So PAWpy is versioned
against *two* axes:

* its own **library** version (semver, ``PAWpy.__version__``), and
* the **minimum PAW build** each API group needs to function.

This module is the single source of truth for the second axis. Each PAW API
group (matching the ``API`` column in ``coverage/COVERAGE.md``) declares the
oldest PAW build it is known to work against. The services reference these
values via their ``API_GROUP`` / ``MIN_PAW_VERSION`` class attributes, and
``PAWService`` uses them to gate or warn at runtime once it knows the server's
version.

Maintenance: these values are reconciled from IBM PAW release notes by the
``/update-paw-coverage`` skill on each PAW release, alongside the coverage
matrix. Entries flagged ``# UNVERIFIED`` are conservative lower bounds (PAWpy
will simply not gate them too aggressively) — tighten them as release notes are
confirmed. Never assert a version you cannot cite.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from PAWpy.Exceptions.Exceptions import PAWVersionError

# The oldest PAW build PAWpy targets at all. API groups with no tighter
# requirement inherit this; gating against it is effectively a no-op for any
# supported deployment.
BASELINE_PAW_VERSION = "2.0.0"

# Minimum PAW build version per API group. Keep the keys in sync with the `API`
# column in coverage/COVERAGE.md and the `API_GROUP` attribute on each service.
MIN_PAW_VERSION: Dict[str, str] = {
    "auth":         BASELINE_PAW_VERSION,  # POST /login, /logout, OAuth token grant
    "ui":           BASELINE_PAW_VERSION,  # /ui embed-URL builder
    "tm1-proxy":    BASELINE_PAW_VERSION,  # /api/v0/tm1/<db>/api/v1 proxy (legacy path)
    "admin":        BASELINE_PAW_VERSION,  # /api/v1/admin
    "content":      "2.1.21",              # /pacontent/v1 Content Services API  # UNVERIFIED — confirm vs IBM release notes
    "tm1-proxy-v1": "2.1.21",              # /api/v1/tm1/<db>/api/v1 proxy — CONFIRMED: IBM Docs + IBM Community announcement (REST API introduced 2.1.21/3.1.8)
    "content-v1":   "2.1.21",              # /api/v1/content assets/users/groups — CONFIRMED: same sources; collection folder "new in 2.1.21 & 3.1.8"
}

# IBM ships PAW on two release lines at once (e.g. "new in 2.1.21 & 3.1.8"), so
# a single minimum can mis-gate the other line: 3.1.0 is "newer" than 2.1.21
# but *lacks* features introduced at 2.1.21/3.1.8. For groups listed here, the
# effective minimum is chosen by the major version of the server's build; other
# lines/groups fall back to MIN_PAW_VERSION.
MIN_PAW_VERSION_BY_LINE: Dict[str, Dict[int, str]] = {
    "tm1-proxy-v1": {2: "2.1.21", 3: "3.1.8"},
    "content-v1":   {2: "2.1.21", 3: "3.1.8"},
}


def parse_version(v: str) -> Tuple[int, ...]:
    """Parse a dotted version string into a tuple of ints for comparison.

    Tolerant of pre-release/build suffixes (``2.1.21-rc1`` -> ``(2, 1, 21)``)
    and of a leading ``v`` (``v2.0`` -> ``(2, 0)``). Non-numeric leading
    segments yield ``()`` so an unknown version never spuriously "meets" a
    requirement.
    """
    if not v:
        return ()
    v = v.strip().lstrip("vV")
    parts = []
    for seg in v.split("."):
        num = ""
        for ch in seg:
            if ch.isdigit():
                num += ch
            else:
                break
        if not num:
            break
        parts.append(int(num))
    return tuple(parts)


def version_meets(version: Optional[str], minimum: str) -> bool:
    """True if *version* is >= *minimum*. Unknown/empty *version* -> False."""
    pv = parse_version(version or "")
    if not pv:
        return False
    return pv >= parse_version(minimum)


def min_version_for(api_group: str, paw_version: Optional[str] = None) -> str:
    """Minimum PAW build required for *api_group* (falls back to the baseline).

    When *paw_version* is given and the group has per-release-line minimums
    (``MIN_PAW_VERSION_BY_LINE``), the minimum for that version's line is
    returned — e.g. ``min_version_for("content-v1", "3.1.0")`` -> ``"3.1.8"``.
    """
    lines = MIN_PAW_VERSION_BY_LINE.get(api_group)
    if lines and paw_version:
        parsed = parse_version(paw_version)
        if parsed and parsed[0] in lines:
            return lines[parsed[0]]
    return MIN_PAW_VERSION.get(api_group, BASELINE_PAW_VERSION)


def is_supported(api_group: str, paw_version: Optional[str]) -> bool:
    """True if *paw_version* satisfies *api_group*'s requirement.

    When *paw_version* is unknown (``None``/empty) this returns ``True`` — PAWpy
    does not block calls just because version detection failed; the server
    itself will reject genuinely-unsupported requests.
    """
    if not paw_version:
        return True
    return version_meets(paw_version, min_version_for(api_group, paw_version))


def assert_supported(api_group: str, paw_version: Optional[str]) -> None:
    """Raise :class:`PAWVersionError` if a *known* version is too old.

    No-op when *paw_version* is unknown (see :func:`is_supported`).
    """
    if paw_version and not is_supported(api_group, paw_version):
        raise PAWVersionError(api_group, min_version_for(api_group, paw_version), paw_version)
