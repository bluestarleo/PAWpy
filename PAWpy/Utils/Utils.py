"""Small helpers shared across services."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional
from urllib.parse import quote


def odata_query(
    filter: Optional[str] = None,
    select: Optional[str] = None,
    expand: Optional[str] = None,
    orderby: Optional[str] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build an OData ``$``-prefixed query-parameter dict for the Content API.

    Only the options that were supplied are included, so callers can pass just
    the ones they need.
    """
    params: Dict[str, Any] = {}
    if filter is not None:
        params["$filter"] = filter
    if select is not None:
        params["$select"] = select
    if expand is not None:
        params["$expand"] = expand
    if orderby is not None:
        params["$orderby"] = orderby
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip
    if extra:
        params.update(extra)
    return params


def encode_path_twice(path: str) -> str:
    """The Content Services API requires asset paths URL-encoded **twice**."""
    return quote(quote(path, safe=""), safe="")


def odata_value_list(response_json: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Extract the list from an OData collection response.

    PAW returns collections either under a ``value`` key (OData convention) or,
    in some content endpoints, as a bare list. Normalise both to a list.
    """
    if isinstance(response_json, list):
        return response_json
    value = response_json.get("value")
    if isinstance(value, list):
        return value
    return []
