#!/usr/bin/env python3
from sqlalchemy import select, func
from app.core.database import SessionLocal
from app.models import Product
db = SessionLocal()
total = db.execute(select(func.count(Product.id))).scalar_one()
with_images = db.execute(select(func.count(Product.id)).where(Product.image_url.is_not(None))).scalar_one()
print(f'Total: {total}, with images: {with_images}, without: {total - with_images}')

# Show a few with images
products = db.execute(select(Product).where(Product.image_url.is_not(None)).limit(5)).scalars().all()
for p in products:
    print(f'  {p.name[:50]}')
    print(f'    Image: {p.image_url[:100]}')
    print(f'    Source: {p.source_url}')
    print()
db.close()
