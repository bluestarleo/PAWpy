"""Base object — a light wrapper around the raw JSON body PAW returns.

Like TM1py's object layer, every concrete object keeps the original ``body``
dict around (``raw``) so nothing the API returns is ever lost, while exposing
the common fields as typed properties.
"""

from __future__ import annotations

from typing import Any, Dict


class PAWObject:
    def __init__(self, body: Dict[str, Any]):
        self._body: Dict[str, Any] = dict(body or {})

    @property
    def raw(self) -> Dict[str, Any]:
        """The untouched JSON dict PAW returned for this resource."""
        return self._body

    def get(self, key: str, default: Any = None) -> Any:
        return self._body.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._body[key]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._body!r})"
