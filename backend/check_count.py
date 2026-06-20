#!/usr/bin/env python3
from sqlalchemy import select, func
from app.core.database import SessionLocal
from app.models import Product
db = SessionLocal()
total = db.execute(select(func.count(Product.id))).scalar_one()
active = db.execute(select(func.count(Product.id)).where(Product.active.is_(True))).scalar_one()
print(f'DB total: {total}, active: {active}')
db.close()
