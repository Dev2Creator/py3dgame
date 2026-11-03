"""PNG decoding, encoding and RGBA image buffers.

The core has no image dependency: PNG is decoded with ``zlib`` and ``struct``.
Only 8-bit, non-interlaced PNGs are accepted; anything else raises
``ImageFormatError`` instead of returning garbage.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Iterable, Tuple

from ..exceptions import AssetNotFoundError, ImageFormatError

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _rgba(colour: Iterable[int]) -> Tuple[int, int, int, int]:
    values = tuple(colour)
    if len(values) == 3:
        values = values + (255,)
    if len(values) != 4:
        raise ValueError("colour must have 3 or 4 components")
    out = []
    for value in values:
        if not isinstance(value, int) or not 0 <= value <= 255:
            raise ValueError(f"colour component out of range: {value!r}")
        out.append(value)
    return tuple(out)  # type: ignore[return-value]


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _channels(colour_type: int) -> int:
    try:
        return {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colour_type]
    except KeyError:
        raise ImageFormatError(f"unsupported PNG colour type {colour_type}") from None


class Image:
    """An RGBA pixel buffer with PNG input and output."""

    __slots__ = ("width", "height", "pixels")

    def __init__(self, width: int, height: int, pixels: bytes | bytearray | None = None):
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise ValueError("image dimensions must be positive")
        self.width, self.height = width, height
        if pixels is None:
            self.pixels = bytearray(width * height * 4)
        else:
            if len(pixels) != width * height * 4:
                raise ValueError("pixel buffer must be width*height*4 bytes")
            self.pixels = bytearray(pixels)

    # -- construction ---------------------------------------------------
    @classmethod
    def solid(cls, width: int, height: int, colour=(255, 255, 255, 255)) -> "Image":
        r, g, b, a = _rgba(colour)
        return cls(width, height, bytes((r, g, b, a)) * (width * height))

    @classmethod
    def load(cls, path: str | Path) -> "Image":
        file_path = Path(path)
        if not file_path.is_file():
            raise AssetNotFoundError(f"image not found: {file_path}")
        return cls.from_png(file_path.read_bytes())

    @classmethod
    def from_png(cls, data: bytes) -> "Image":
        if not data.startswith(PNG_SIGNATURE):
            raise ImageFormatError("not a PNG file")
        pos, header, palette, transparency = 8, None, None, None
        compressed = bytearray()
        while pos + 8 <= len(data):
            length, tag = struct.unpack(">I4s", data[pos:pos + 8])
            pos += 8
            payload = data[pos:pos + length]
            pos += length + 4  # skip CRC
            if len(payload) != length:
                raise ImageFormatError(f"truncated {tag.decode('latin-1')} chunk")
            if tag == b"IHDR":
                header = struct.unpack(">IIBBBBB", payload)
            elif tag == b"PLTE":
                palette = payload
            elif tag == b"tRNS":
                transparency = payload
            elif tag == b"IDAT":
                compressed += payload
            elif tag == b"IEND":
                break
        if header is None:
            raise ImageFormatError("missing IHDR chunk")
        width, height, depth, colour_type, compression, filter_method, interlace = header
        if depth != 8:
            raise ImageFormatError(f"only 8-bit PNGs are supported, got {depth}-bit")
        if compression != 0 or filter_method != 0:
            raise ImageFormatError("unsupported PNG compression or filter method")
        if interlace != 0:
            raise ImageFormatError("interlaced PNGs are not supported")
        channels = _channels(colour_type)
        if colour_type == 3 and not palette:
            raise ImageFormatError("palette PNG without a PLTE chunk")
        try:
            raw = zlib.decompress(bytes(compressed))
        except zlib.error as exc:
            raise ImageFormatError(f"corrupt image data: {exc}") from exc

        stride = width * channels
        if len(raw) < height * (stride + 1):
            raise ImageFormatError("image data is shorter than the header claims")

        scanlines = []
        previous = bytearray(stride)
        offset = 0
        bpp = channels
        for _ in range(height):
            filter_type = raw[offset]
            offset += 1
            line = bytearray(raw[offset:offset + stride])
            offset += stride
            if filter_type == 1:
                for i in range(bpp, stride):
                    line[i] = (line[i] + line[i - bpp]) & 0xFF
            elif filter_type == 2:
                for i in range(stride):
                    line[i] = (line[i] + previous[i]) & 0xFF
            elif filter_type == 3:
                for i in range(stride):
                    left = line[i - bpp] if i >= bpp else 0
                    line[i] = (line[i] + ((left + previous[i]) >> 1)) & 0xFF
            elif filter_type == 4:
                for i in range(stride):
                    left = line[i - bpp] if i >= bpp else 0
                    upper = previous[i]
                    upper_left = previous[i - bpp] if i >= bpp else 0
                    line[i] = (line[i] + _paeth(left, upper, upper_left)) & 0xFF
            elif filter_type != 0:
                raise ImageFormatError(f"unknown scanline filter {filter_type}")
            scanlines.append(line)
            previous = line

        pixels = bytearray(width * height * 4)
        out = 0
        transparent_gray = transparent_rgb = None
        if transparency is not None:
            if colour_type == 0 and len(transparency) >= 2:
                transparent_gray = struct.unpack(">H", transparency[:2])[0]
            elif colour_type == 2 and len(transparency) >= 6:
                transparent_rgb = struct.unpack(">HHH", transparency[:6])
        for line in scanlines:
            for x in range(width):
                if colour_type == 6:
                    pixels[out:out + 4] = line[x * 4:x * 4 + 4]
                elif colour_type == 2:
                    r, g, b = line[x * 3:x * 3 + 3]
                    a = 0 if transparent_rgb == (r, g, b) else 255
                    pixels[out:out + 4] = bytes((r, g, b, a))
                elif colour_type == 0:
                    value = line[x]
                    a = 0 if transparent_gray == value else 255
                    pixels[out:out + 4] = bytes((value, value, value, a))
                elif colour_type == 4:
                    value, a = line[x * 2:x * 2 + 2]
                    pixels[out:out + 4] = bytes((value, value, value, a))
                else:  # palette
                    index = line[x]
                    if index * 3 + 2 >= len(palette):
                        raise ImageFormatError("palette index outside PLTE")
                    r, g, b = palette[index * 3:index * 3 + 3]
                    a = transparency[index] if transparency and index < len(transparency) else 255
                    pixels[out:out + 4] = bytes((r, g, b, a))
                out += 4
        return cls(width, height, pixels)

    # -- pixels ---------------------------------------------------------
    def size(self) -> Tuple[int, int]:
        return self.width, self.height

    def _index(self, x: int, y: int) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"pixel ({x}, {y}) outside {self.width}x{self.height}")
        return (y * self.width + x) * 4

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
        i = self._index(x, y)
        return self.pixels[i], self.pixels[i + 1], self.pixels[i + 2], self.pixels[i + 3]

    def set_pixel(self, x: int, y: int, colour=(255, 255, 255, 255)) -> None:
        r, g, b, a = _rgba(colour)
        i = self._index(x, y)
        self.pixels[i:i + 4] = bytes((r, g, b, a))

    def crop(self, x: int, y: int, width: int, height: int) -> "Image":
        if width <= 0 or height <= 0:
            raise ValueError("crop size must be positive")
        if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
            raise ValueError("crop rectangle exceeds the image")
        out = Image(width, height)
        for row in range(height):
            src = self._index(x, y + row)
            dst = row * width * 4
            out.pixels[dst:dst + width * 4] = self.pixels[src:src + width * 4]
        return out

    def flip_x(self) -> "Image":
        out = Image(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                out.set_pixel(self.width - 1 - x, y, self.get_pixel(x, y))
        return out

    def flip_y(self) -> "Image":
        out = Image(self.width, self.height)
        for y in range(self.height):
            out.pixels[y * self.width * 4:(y + 1) * self.width * 4] = self.pixels[
                (self.height - 1 - y) * self.width * 4:(self.height - y) * self.width * 4
            ]
        return out

    # -- output ---------------------------------------------------------
    def to_png(self) -> bytes:
        stride = self.width * 4
        raw = bytearray()
        for y in range(self.height):
            raw.append(0)  # filter: none
            raw += self.pixels[y * stride:(y + 1) * stride]

        def chunk(tag: bytes, payload: bytes) -> bytes:
            crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
            return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)

        header = struct.pack(">IIBBBBB", self.width, self.height, 8, 6, 0, 0, 0)
        return (
            PNG_SIGNATURE
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b"")
        )

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.to_png())
        return target
