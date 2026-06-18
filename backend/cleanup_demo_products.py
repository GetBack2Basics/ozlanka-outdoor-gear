#!/usr/bin/env python3
"""
Cleanup script to remove demo/fake products from the database.
These are products that were seeded via the old /admin/seed-products endpoint
and have known SKU patterns.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models import Product
from sqlalchemy import delete, select

# List of demo product SKUs that were seeded via the old seed-products endpoint
DEMO_SKUS = {
    "ARB-SNK-01",
    "RR-RB-02",
    "GME-UHF-03",
    "KNG-SWAG-04",
    "RED-BCDC-05",
    "ARB-ZFR-06",
    "IRON-SUS-07",
    "GH-STP-08",
    "KNI-CO-09",
    "XTM-LB-10",
}


def cleanup_demo_products() -> int:
    """Delete demo products from the database. Returns count of deleted products."""
    db = SessionLocal()
    try:
        # Find demo products by SKU
        demo_products = db.execute(
            select(Product).where(Product.sku.in_(DEMO_SKUS))
        ).scalars().all()

        if not demo_products:
            print("No demo products found to delete.")
            return 0

        print(f"Found {len(demo_products)} demo products to delete:")
        for product in demo_products:
            print(f"  - {product.sku}: {product.name}")

        # Delete them
        for product in demo_products:
            db.delete(product)

        db.commit()
        print(f"Successfully deleted {len(demo_products)} demo products.")
        return len(demo_products)

    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Cleaning up demo products...")
    deleted_count = cleanup_demo_products()
    print(f"Done. Deleted {deleted_count} products.")