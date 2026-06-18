#!/usr/bin/env python3
"""
Download images for all products in the database that have image_url set
but don't have local image files.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import Product
from app.services.images import download_product_image
from sqlalchemy import select

PRODUCT_IMAGE_DIR = "/app/product-images"


def download_missing_images():
    db = SessionLocal()
    try:
        # Get all products with remote image URLs
        products = db.execute(
            select(Product).where(Product.image_url.isnot(None))
        ).scalars().all()

        if not products:
            print("No products with images found.")
            return 0

        print(f"Found {len(products)} products with image URLs.")
        downloaded = 0

        for product in products:
            # Check if local file already exists
            if product.image_url and product.image_url.startswith("/product-images/"):
                filename = product.image_url.replace("/product-images/", "")
                local_path = os.path.join(PRODUCT_IMAGE_DIR, filename)
                if os.path.exists(local_path):
                    print(f"  SKIP: {product.name} - already has local image")
                    continue

            # Download the image
            remote_url = product.image_url
            if remote_url and remote_url.startswith("http"):
                print(f"  DOWNLOADING: {product.name} from {remote_url}")
                local_path = download_product_image(remote_url, product.source_url)
                if local_path:
                    product.image_url = local_path
                    db.commit()
                    downloaded += 1
                    print(f"    SUCCESS: {local_path}")
                else:
                    print(f"    FAILED: Could not download")
            else:
                print(f"  SKIP: {product.name} - no remote URL (current: {product.image_url})")

        print(f"\nDownloaded {downloaded} new images.")
        return downloaded

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Downloading missing product images...")
    download_missing_images()
    print("Done.")