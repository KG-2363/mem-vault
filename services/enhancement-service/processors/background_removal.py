"""
Removes the photo background using rembg (U2-Net model).
Returns PNG bytes with a transparent background.
"""
from rembg import remove


def remove_background(image_bytes: bytes) -> bytes:
    return remove(image_bytes)
