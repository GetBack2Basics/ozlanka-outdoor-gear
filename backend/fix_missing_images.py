#!/usr/bin/env python3
"""
Download missing product images by fetching og:image from source URLs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import Product
from app.services.images import download_product_image
from sqlalchemy import select
import requests
from bs4 import BeautifulSoup

PRODUCT_IMAGE_DIR = "/app/product-images"


def get_og_image_from_url(url: str) -> str | None:
    """Extract og:image from a product page."""
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]
        # Fallback: look for first product image
        img = soup.find("img", class_=lambda x: x and "product" in x.lower())
        if img and img.get("src"):
            return img["src"]
    except Exception:
        pass
    return None


def fix_missing_images():
    db = SessionLocal()
    try:
        products = db.execute(
            select(Product).where(Product.active.is_(True))
        ).scalars().all()

        fixed = 0
        for p in products:
            if p.image_url and p.image_url.startswith("/product-images/"):
                fname = p.image_url.replace("/product-images/", "")
                path = os.path.join(PRODUCT_IMAGE_DIR, fname)
                if not os.path.exists(path):
                    print(f"Fixing {p.id}: {p.name}")
                    print(f"  Source: {p.source_url}")
                    
                    # Try to get og:image from source URL
                    og_image = get_og_image_from_url(p.source_url)
                    if og_image:
                        print(f"  Found og:image: {og_image}")
                        p.image_url = None  # Clear to trigger re-download
                        db.commit()
                        
                        # Download using the original function
                        local_path = download_product_image(og_image, p.source_url)
                        if local_path:
                            p.image_url = local_path
                            db.commit()
                            print(f"  SUCCESS: {local_path}")
                            fixed += 1
                        else:
                            print(f"  FAILED to download")
                    else:
                        print(f"  Could not find og:image")
                        
        print(f"\nFixed {fixed} products")
        return fixed

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Fixing missing product images from source URLs...")
    fix_missing_images()
    print("Done.")