import hashlib
import os
from urllib.parse import urlparse
import requests
from sqlalchemy.orm import Session
from app.core.config import get_settings

settings = get_settings()
PRODUCT_IMAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "product-images",
)
os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)


def _filename_for_url(image_url: str) -> str:
    parsed = urlparse(image_url)
    basename = os.path.basename(parsed.path)
    if not basename:
        basename = "image"
    digest = hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:8]
    if basename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        base, _ = os.path.splitext(basename)
    else:
        base = basename
    return f"{base}-{digest}.jpg"


def download_product_image(image_url: str, source_url: str | None = None) -> str | None:
    if not image_url:
        return None

    try:
        response = requests.get(
            image_url,
            timeout=20,
            headers={"User-Agent": "OzLankaBot/1.0"},
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    filename = _filename_for_url(image_url)
    destination = os.path.join(PRODUCT_IMAGE_DIR, filename)
    try:
        with open(destination, "wb") as file_handle:
            file_handle.write(response.content)
    except OSError:
        return None

    return f"/product-images/{filename}"


def local_path_for(public_path: str) -> str | None:
    if not public_path:
        return None
    relative = public_path.lstrip("/")
    if not relative.startswith("product-images/"):
        return None
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        relative,
    )
