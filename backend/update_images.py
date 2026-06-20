#!/usr/bin/env python3
"""Update products with image URLs from sitemap image:image extension."""
import xml.etree.ElementTree as ET
import requests, sys, time
from sqlalchemy import select, update
from app.core.database import SessionLocal, engine
from app.models import Product

SITEMAP_NAMESPACE = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
IMAGE_NS = "http://www.google.com/schemas/sitemap-image/1.1"

def fetch_image_map():
    """Fetch all product→image mappings from sitemaps."""
    image_map = {}
    for i in range(1, 4):
        sitemap_url = f'https://www.4wdsupacentre.com.au/media/sitemap_4wdsc-9-{i}.xml'
        print(f'Fetching sitemap {i}...', file=sys.stderr)
        try:
            resp = requests.get(sitemap_url, timeout=60)
            root = ET.fromstring(resp.text)
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            continue
        
        for url_node in root.findall('sm:url', SITEMAP_NAMESPACE):
            loc = url_node.find('sm:loc', SITEMAP_NAMESPACE)
            if loc is None or not loc.text:
                continue
            product_url = loc.text.strip()
            
            image_node = url_node.find(f'{{{IMAGE_NS}}}image')
            if image_node is not None:
                img_loc = image_node.find(f'{{{IMAGE_NS}}}loc')
                if img_loc is not None and img_loc.text:
                    image_url = img_loc.text.strip().replace('&amp;', '&')
                    image_map[product_url] = image_url
    
    return image_map


def main():
    # Step 1: Fetch image map from sitemaps
    print('Fetching image URLs from sitemaps...', file=sys.stderr)
    image_map = fetch_image_map()
    print(f'Found {len(image_map)} image URLs', file=sys.stderr)
    
    # Step 2: Update products in DB
    db = SessionLocal()
    try:
        # Get all products
        products = db.execute(select(Product)).scalars().all()
        print(f'Updating {len(products)} products...', file=sys.stderr)
        
        updated = 0
        for product in products:
            if product.source_url in image_map:
                product.image_url = image_map[product.source_url]
                updated += 1
        
        db.commit()
        print(f'Updated {updated} products with image URLs', file=sys.stderr)
        
        # Verify
        from sqlalchemy import func
        total_with_images = db.execute(
            select(func.count(Product.id)).where(Product.image_url.is_not(None))
        ).scalar_one()
        print(f'Products with images: {total_with_images}/{len(products)}', file=sys.stderr)
        
        # Show a few examples
        sample = db.execute(
            select(Product).where(Product.image_url.is_not(None)).limit(3)
        ).scalars().all()
        for p in sample:
            print(f'  {p.name[:50]}')
            print(f'    {p.image_url[:120]}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
