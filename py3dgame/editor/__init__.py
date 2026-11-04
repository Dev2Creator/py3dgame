"""Scene documents, previews and the local preview server.

This is the editor foundation, not a full IDE: a scene is a JSON document, the
preview server renders it, and the UI is yours to grow.
"""

from .document import MESHES, NodeDocument, SceneDocument
from .preview import render_document, render_document_png
from .server import PreviewServer

__all__ = [
    "MESHES",
    "NodeDocument",
    "PreviewServer",
    "SceneDocument",
    "render_document",
    "render_document_png",
]
