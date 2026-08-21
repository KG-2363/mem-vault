"""
Generates WebP thumbnails using libvips (pyvips) for fast, memory-efficient resizing.
pyvips uses streaming and avoids loading the full image into Python memory.
"""
import io
from typing import Iterator

import pyvips


def generate_thumbnails(image_bytes: bytes, sizes: list[int]) -> Iterator[tuple[int, bytes]]:
    """Yields (size_px, webp_bytes) for each requested size."""
    img = pyvips.Image.new_from_buffer(image_bytes, "")

    for size in sizes:
        scale = size / max(img.width, img.height)
        thumb = img.resize(scale, kernel=pyvips.enums.Kernel.LANCZOS3)
        webp_bytes = thumb.write_to_buffer(".webp[Q=85,strip=true]")
        yield size, webp_bytes
