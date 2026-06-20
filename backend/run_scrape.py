#!/usr/bin/env python3
"""Run the sitemap-based scraper and save results to the database."""
import sys
sys.path.insert(0, '/app')

from datetime import datetime, timezone
from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.models import Product, ScrapeRun
from app.services.scraper import discover_product_targets, scrape_product_urls, build_pricing_payload, ProductTarget
from app.services.exchange import get_aud_to_lkr_rate
from app.core.config import get_settings


def main():
    settings = get_settings()
    urls = [url.strip() for url in settings.scrape_target_urls.split(",") if url.strip()]
    print(f"Seed URLs: {urls}")

    # Discover product targets from sitemap
    targets = discover_product_targets(urls)
    print(f"Discovered {len(targets)} product targets")

    # Use ALL targets
    target_urls = [t.source_url for t in targets]
    print(f"Scraping {len(target_urls)} URLs...")

    # Scrape (derive product data from URL slugs, with image URLs from sitemap)
    results = scrape_product_urls(target_urls, targets=targets)
    print(f"Scraped {len(results)} products")

    if not results:
        print("No products scraped, aborting.")
        return

    # Save to database
    db = SessionLocal()
    try:
        # Clear existing products
        from sqlalchemy import text
        db.execute(text("DELETE FROM products"))
        db.commit()
        print(f"Cleared existing products")

        # Insert new products
        rate = get_aud_to_lkr_rate()
        handling_fee = settings.handling_fee_percent
        count = 0
        for scraped in results:
            payload = build_pricing_payload(scraped, handling_fee)
            product = Product(**payload, handling_fee_percent=handling_fee)
            db.add(product)
            count += 1
            # Commit in batches of 500 to avoid memory issues
            if count % 500 == 0:
                db.commit()
                print(f"  Inserted {count}...")
        db.commit()
        print(f"Inserted {count} products into database")

        # Show sample
        from sqlalchemy import func
        total = db.execute(select(func.count(Product.id))).scalar_one()
        print(f"\nTotal products in DB: {total}")

        # Show category distribution
        from sqlalchemy import distinct
        cats = db.execute(select(distinct(Product.category))).scalars().all()
        print(f"Categories: {len(cats)}")
        for cat in sorted(cats):
            cat_count = db.execute(select(func.count(Product.id)).where(Product.category == cat)).scalar_one()
            print(f"  {cat}: {cat_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
