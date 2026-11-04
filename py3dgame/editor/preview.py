"""Render a scene document to an image or PNG bytes."""

from __future__ import annotations

from ..renderer2d.image import Image
from .document import SceneDocument


def render_document(document: SceneDocument, width: int = 640, height: int = 360) -> Image:
    """Render the document once and return an RGBA image."""
    if width <= 0 or height <= 0:
        raise ValueError("preview dimensions must be positive")
    renderer = document.build_renderer(width, height)
    return renderer.to_image()


def render_document_png(document: SceneDocument, width: int = 640, height: int = 360) -> bytes:
    """Render the document and encode it as PNG bytes."""
    return render_document(document, width, height).to_png()
