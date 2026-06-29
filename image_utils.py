import uuid
from enum import Enum
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

PROFILE_PICS_DIR = Path("media/profile_pics")


class ImageExtensions(str, Enum):
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    JPG = "jpg"


class ImageModes(str, Enum):
    RGBA = "RGBA"
    RGB = "RGB"
    LA = "LA"
    P = "P"

    @classmethod
    def list_modes(cls):
        return list(cls)

    @classmethod
    def to_dict(cls):
        return {mode.name: mode.value for mode in cls}


def process_profile_image(content: bytes) -> str:
    with Image.open(BytesIO(content)) as original:
        img = ImageOps.exif_transpose(original)
        img = ImageOps.fit(img, (300, 300), method=Image.Resampling.LANCZOS)

        if img.mode in ImageModes.list_modes():
            img = img.convert(ImageModes.RGB.value)

        filename = f"{uuid.uuid4().hex}.{ImageExtensions.JPG.value}"
        filepath = PROFILE_PICS_DIR / filename
        PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)

        img.save(filepath, ImageExtensions.JPEG.value.upper(), quality=85, optimize=True)

    return filename


def delete_profile_image(filename: str | None) -> None:
    if filename is None:
        return
    filepath = PROFILE_PICS_DIR / filename
    if filepath.exists():
        filepath.unlink()
