#!/usr/bin/env python3
"""Diagnose the product filtering pipeline."""
from app.services.scraper import discover_product_targets, _extract_product_from_slug
from app.core.config import get_settings
from sqlalchemy import select, func
from app.core.database import SessionLocal
from app.models import Product

BUNDLE_KEYWORDS = (
    "kit-mkii", "kit-mk-ii", "jump-starter-kit", "starter-kit", "bundle",
    "combo-deals", "value-pack", "twin-pack", "double-pack", "gift-voucher",
    "gift-card", "survival-vehicle", "seat-organiser",
)
CATEGORY_SKIP = {
    "4wd", "solar-power", "camping", "4wd-accessories", "driving-lights",
    "electrical", "roof-racks", "4wd-electrical", "4wd-driving-lights",
    "4wd-roof-racks", "4wd-4wd-accessories", "4wd-4wd", "fridges",
    "camping-power", "recovery", "recovery-gear", "watersport-activities",
    "specials", "new-products", "combo-deals", "model-runout-specials",
    "diy-projects", "complete-guides", "tips-techniques",
}

settings = get_settings()
urls = [url.strip() for url in settings.scrape_target_urls.split(',') if url.strip()]
targets = discover_product_targets(urls)
print(f'1. Sitemap targets: {len(targets)}')

valid = 0
skipped_bundle = 0
skipped_category = 0
skipped_short = 0
for t in targets:
    slug = t.source_url.rstrip('/').split('/')[-1].replace('.html', '').lower()
    if any(kw in slug for kw in BUNDLE_KEYWORDS):
        skipped_bundle += 1
        continue
    if slug in CATEGORY_SKIP:
        skipped_category += 1
        continue
    if len(slug) < 10:
        skipped_short += 1
        continue
    valid += 1

print(f'2. Valid after filtering: {valid}')
print(f'   Skipped: {skipped_bundle} bundles, {skipped_category} category pages, {skipped_short} short slugs')

product_count = 0
categories = {}
for t in targets:
    slug = t.source_url.rstrip('/').split('/')[-1].replace('.html', '').lower()
    if any(kw in slug for kw in BUNDLE_KEYWORDS): continue
    if slug in CATEGORY_SKIP: continue
    if len(slug) < 10: continue
    p = _extract_product_from_slug(t.source_url)
    if p:
        product_count += 1
        cat = p.category or 'Unknown'
        categories[cat] = categories.get(cat, 0) + 1

print(f'3. Products that extract successfully: {product_count}')
print(f'4. Category distribution:')
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f'   {cat}: {count}')

db = SessionLocal()
total = db.execute(select(func.count(Product.id))).scalar_one()
active = db.execute(select(func.count(Product.id)).where(Product.active.is_(True))).scalar_one()
print(f'\n5. Database: {total} total, {active} active')

all_products = db.execute(select(Product).where(Product.active.is_(True)).order_by(Product.scraped_at.desc()).limit(500)).scalars().all()
print(f'6. Products API fetches: {len(all_products)} (up to FETCH_LIMIT=500)')

def is_bundle(name):
    if not name: return True
    name_lower = name.lower()
    if "home page" in name_lower and "4wd supacentre" in name_lower: return True
    if " + " in name_lower:
        parts = name_lower.split(" + ")
        if len(parts) >= 2: return True
    return False

filtered = [p for p in all_products if not is_bundle(p.name)]
bundles_removed = len(all_products) - len(filtered)
print(f'7. Bundle filter removes: {bundles_removed}, leaving: {len(filtered)}')
print(f'8. Final API output (PRODUCTS_LIMIT=50): {min(len(filtered), 50)}')

db.close()
