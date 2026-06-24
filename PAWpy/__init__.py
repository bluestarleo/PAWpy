"""PAWpy — a TM1py-inspired Python wrapper for the IBM Planning Analytics
Workspace (PAW) REST API.

    from PAWpy import PAWService
"""

from PAWpy.PAWService import PAWService
from PAWpy.Services.RestService import RestService
from PAWpy.Objects.Asset import Asset
from PAWpy.Exceptions.Exceptions import (
    PAWException,
    PAWRestException,
    PAWAuthenticationException,
    PAWConfigException,
    PAWNotFoundException,
    PAWTimeoutException,
    PAWVersionError,
)
from PAWpy.version_requirements import (
    BASELINE_PAW_VERSION,
    MIN_PAW_VERSION,
    min_version_for,
    is_supported,
)

__version__ = "0.1.0"

__all__ = [
    "PAWService",
    "RestService",
    "Asset",
    "PAWException",
    "PAWRestException",
    "PAWAuthenticationException",
    "PAWConfigException",
    "PAWNotFoundException",
    "PAWTimeoutException",
    "PAWVersionError",
    "BASELINE_PAW_VERSION",
    "MIN_PAW_VERSION",
    "min_version_for",
    "is_supported",
]
