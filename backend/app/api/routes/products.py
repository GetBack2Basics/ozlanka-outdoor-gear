from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.routes.auth import get_db
from app.models import Product
from app.schemas import ProductRead


router = APIRouter(prefix="/products", tags=["products"])

# Limit for final displayed products
PRODUCTS_LIMIT = 500

# Fetch limit before filtering - get all items to account for filtered bundles
FETCH_LIMIT = 500


def is_bundle(name: str) -> bool:
    """Check if a product name indicates a bundle/kit (multiple products sold together).
    
    Only filters explicit multi-product bundles where names contain " + " 
    connecting distinct product names (e.g., "Product A + Product B").
    
    Does NOT filter:
    - Gift vouchers/cards (single products)
    - Product names with specs separated by " | " 
    - Products with "kit" in name that's just the product name
    - Survival kits that are single products
    """
    if not name:
        return True
    name_lower = name.lower()
    
    # Filter "Home Page" placeholder products
    if "home page" in name_lower and "4wd supacentre" in name_lower:
        return True
    
    # Only filter explicit multi-product bundles with " + " connector
    if " + " in name_lower:
        # Check it's actually multiple products, not just specs
        parts = name_lower.split(" + ")
        if len(parts) >= 2:
            # Likely a bundle if it has distinct product types
            return True
    
    return False


@router.get("", response_model=list[ProductRead])
def list_products(db=Depends(get_db)):
    # Fetch more items first, then filter, then limit
    products = db.execute(
        select(Product)
        .where(Product.active.is_(True))
        .order_by(Product.scraped_at.desc())
        .limit(FETCH_LIMIT)
    ).scalars().all()
    
    # Filter out bundles/kits
    filtered = [p for p in products if not is_bundle(p.name)]
    return filtered[:PRODUCTS_LIMIT]
