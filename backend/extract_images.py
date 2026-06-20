#!/usr/bin/env python3
"""Extract product URL → image URL mapping from sitemaps."""
import xml.etree.ElementTree as ET
import requests, sys, time

ns = {
    'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'image': 'http://www.google.com/schemas/sitemap-image/1.1'
}

total_images = 0
total_urls = 0

for i in range(1, 4):
    sitemap_url = f'https://www.4wdsupacentre.com.au/media/sitemap_4wdsc-9-{i}.xml'
    print(f'Fetching sitemap {i}...', file=sys.stderr)
    try:
        resp = requests.get(sitemap_url, timeout=60)
        root = ET.fromstring(resp.text)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        continue
    
    for url_node in root.findall('sm:url', ns):
        loc = url_node.find('sm:loc', ns)
        if loc is None or not loc.text:
            continue
        product_url = loc.text.strip()
        total_urls += 1
        
        image_node = url_node.find('image:image', ns)
        if image_node is not None:
            img_loc = image_node.find('image:loc', ns)
            if img_loc is not None and img_loc.text:
                image_url = img_loc.text.strip().replace('&amp;', '&')
                print(f'{product_url}\t{image_url}')
                total_images += 1

print(f'\nTotal URLs: {total_urls}, with images: {total_images}', file=sys.stderr)
