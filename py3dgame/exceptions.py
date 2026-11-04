"""Exception hierarchy for py3dgame.

Callers should be able to distinguish a bad configuration from a missing
backend or an invalid scene operation without parsing messages.
"""

from __future__ import annotations


class Py3DGameError(Exception):
    """Base class for every error raised by the library."""


class ConfigurationError(Py3DGameError):
    """A value supplied by the developer is invalid."""


class BackendError(Py3DGameError):
    """A requested platform backend is unavailable or failed to start."""


class SceneError(Py3DGameError):
    """An invalid scene-graph operation, such as creating a cycle."""


class AssetNotFoundError(Py3DGameError):
    """A requested asset does not exist or could not be read."""


class DocumentError(Py3DGameError):
    """A scene document is malformed or violates the schema."""


class ImageFormatError(Py3DGameError):
    """An image file is malformed or uses an unsupported encoding."""
