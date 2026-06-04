"""BookService — convenience layer over ContentService for PAW books.

A "book" is just a content asset of type ``book``/``dashboard``. This service
filters the content store down to books and pairs each with an embed URL from
:class:`UIService`, so the common "list the books in a folder and get an iframe
URL" workflow is one call.
"""

from __future__ import annotations

from typing import List

from PAWpy.Objects.Asset import Asset
from PAWpy.Services.ContentService import ContentService
from PAWpy.Services.ObjectService import ObjectService
from PAWpy.Services.RestService import RestService
from PAWpy.Services.UIService import UIService


class BookService(ObjectService):
    def __init__(self, rest: RestService, content: ContentService, ui: UIService):
        super().__init__(rest)
        self._content = content
        self._ui = ui

    def get_all(self, folder_path: str) -> List[Asset]:
        """List the books/dashboards directly under *folder_path*."""
        children = self._content.list_children(folder_path)
        return [a for a in children if a.is_book]

    def get(self, path: str, expand_content: bool = False) -> Asset:
        """Fetch a single book by content-store path."""
        return self._content.get_by_path(path, expand_content=expand_content)

    def get_embed_url(self, path: str, embed: bool = True) -> str:
        """Build the ``/ui?type=book`` iframe URL for the book at *path*."""
        return self._ui.book_url(path, embed=embed)

    def exists(self, path: str) -> bool:
        return self._content.exists(path)

    def delete(self, path: str) -> None:
        self._content.delete_by_path(path)
