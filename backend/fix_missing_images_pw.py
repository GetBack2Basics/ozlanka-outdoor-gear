#!/usr/bin/env python3
"""
Download missing product images using Playwright (like the scraper does).
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import Product
from sqlalchemy import select
from playwright.async_api import async_playwright

PRODUCT_IMAGE_DIR = "/app/product-images"


async def download_missing_images():
    db = SessionLocal()
    try:
        products = db.execute(
            select(Product).where(Product.active.is_(True))
        ).scalars().all()

        missing = []
        for p in products:
            if p.image_url and p.image_url.startswith("/product-images/"):
                fname = p.image_url.replace("/product-images/", "")
                path = os.path.join(PRODUCT_IMAGE_DIR, fname)
                if not os.path.exists(path):
                    missing.append(p)

        if not missing:
            print("No missing images")
            return 0

        print(f"Found {len(missing)} products with missing images")
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            fixed = 0
            for p in missing:
                print(f"\nProcessing {p.id}: {p.name}")
                print(f"  Source: {p.source_url}")
                
                try:
                    await page.goto(p.source_url, wait_until="domcontentloaded", timeout=60000)
                    
                    # Try to get og:image
                    og_image = await page.locator('meta[property="og:image"]').first.get_attribute("content")
                    if not og_image:
                        # Try first product image
                        img_selector = 'img[class*="product"], img.product-image, .product-image img, [itemprop="image"]'
                        img = await page.locator(img_selector).first.get_attribute("src")
                        og_image = img
                    
                    if og_image:
                        print(f"  Found image: {og_image}")
                        
                        # Download using existing function
                        from app.services.images import download_product_image
                        local_path = download_product_image(og_image, p.source_url)
                        
                        if local_path:
                            p.image_url = local_path
                            db.commit()
                            print(f"  SUCCESS: {local_path}")
                            fixed += 1
                        else:
                            print(f"  FAILED: download_product_image returned None")
                    else:
                        print(f"  Could not find image on page")
                        
                except Exception as e:
                    print(f"  Error: {e}")
                    
            await browser.close()
        
        print(f"\nFixed {fixed}/{len(missing)} products")
        return fixed

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Fixing missing product images with Playwright...")
    asyncio.run(download_missing_images())
    print("Done.")