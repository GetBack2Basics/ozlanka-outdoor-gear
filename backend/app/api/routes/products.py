from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.routes.auth import get_db
from app.models import Product
from app.schemas import ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(db=Depends(get_db)):
    return db.execute(select(Product).where(Product.active.is_(True)).order_by(Product.scraped_at.desc())).scalars().all()
