from fastapi import FastAPI

from app.api.routes import admin, auth, health, products, requests
from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.security import hash_password
from app.models import ApprovalStatus, User, UserRole
from app.workers.tasks import ensure_schema as ensure_scrape_schema

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(products.router)
app.include_router(requests.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_scrape_schema()
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == settings.seed_admin_email).one_or_none()
        if admin_user is None:
            admin_user = User(
                email=settings.seed_admin_email,
                password_hash=hash_password(settings.seed_admin_password),
                role=UserRole.admin,
                approval_status=ApprovalStatus.approved,
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()
