import os
import re
from typing import Optional

import requests

PRODUCT_IMAGE_DIR = "/app/product-images"
os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)


def _slugify_product_source(source_url: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", source_url)
    return slug.strip("_")[:120]


def download_product_image(url: Optional[str], source_url: str) -> Optional[str]:
    if not url:
        return None
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20, stream=True)
        if resp.status_code != 200:
            return None
        ctype = resp.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            return None
        slug = _slugify_product_source(source_url)
        path = os.path.join(PRODUCT_IMAGE_DIR, f"{slug}.jpg")
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return f"/product-images/{slug}.jpg"
    except Exception:
        return None
