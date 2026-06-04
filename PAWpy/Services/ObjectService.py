"""Base for every service — holds the shared RestService handle."""

from __future__ import annotations

from PAWpy.Services.RestService import RestService


class ObjectService:
    def __init__(self, rest: RestService):
        self._rest = rest

    @property
    def rest(self) -> RestService:
        return self._rest
