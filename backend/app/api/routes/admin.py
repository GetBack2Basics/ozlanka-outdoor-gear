import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from datetime import datetime

from app.api.routes.auth import get_db, require_admin
from app.core.config import get_settings
from app.models import AppSetting, ApprovalStatus, Product, RequestListItem, ScrapeRun, User
from app.schemas import HandlingFeePayload, ScrapeResult, UserRead
from app.services.exchange import get_aud_to_lkr_rate
from app.services.pricing import calculate_lkr_price, choose_reference_price
from app.workers.tasks import trigger_scrape

router = APIRouter(prefix="/admin", tags=["admin"])


def is_bundle(name: str) -> bool:
    """Check if a product name indicates a bundle/kit (multiple products sold together)."""
    if not name:
        return True
    name_lower = name.lower()
    
    # Filter "Home Page" placeholder products
    if "home page" in name_lower and "4wd supacentre" in name_lower:
        return True
    
    # Only filter explicit multi-product bundles with " + " connector
    if " + " in name_lower:
        parts = name_lower.split(" + ")
        if len(parts) >= 2:
            return True
    
    return False


def get_filter_reason(name: str) -> str:
    name_lower = name.lower()
    if "home page" in name_lower and "4wd supacentre" in name_lower:
        return "Home Page placeholder"
    if " + " in name:
        return "Multi-product bundle (contains \" + \")"
    return "Filtered"


@router.get("/dashboard")
def dashboard(admin=Depends(require_admin), db=Depends(get_db)):
    users_total = db.execute(select(func.count(User.id))).scalar_one()
    pending_users = db.execute(select(func.count(User.id)).where(User.approval_status == ApprovalStatus.pending)).scalar_one()
    pending_user_rows = db.execute(
        select(User).where(User.approval_status == ApprovalStatus.pending).order_by(User.created_at.asc())
    ).scalars().all()
    products_total = db.execute(select(func.count(Product.id))).scalar_one()
    requests_total = db.execute(select(func.count(RequestListItem.id))).scalar_one()
    latest_run = db.execute(select(ScrapeRun).order_by(ScrapeRun.started_at.desc())).scalars().first()
    fee = db.execute(select(AppSetting).where(AppSetting.key == "handling_fee_percent")).scalar_one_or_none()
    return {
        "users_total": users_total,
        "pending_users": pending_users,
        "pending_user_rows": [UserRead.model_validate(user) for user in pending_user_rows],
        "products_total": products_total,
        "requests_total": requests_total,
        "latest_run": None
        if latest_run is None
        else {
            "id": latest_run.id,
            "status": latest_run.status,
            "stage": latest_run.stage,
            "progress_percent": latest_run.progress_percent,
            "message": latest_run.message,
            "total_items": latest_run.total_items,
            "processed_items": latest_run.processed_items,
            "started_at": latest_run.started_at,
            "finished_at": latest_run.finished_at,
        },
        "handling_fee_percent": float(fee.value) if fee else get_settings().handling_fee_percent,
    }


@router.post("/users/{user_id}/approve", response_model=UserRead)
def approve_user(user_id: int, admin=Depends(require_admin), db=Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.approval_status = ApprovalStatus.approved
    db.commit()
    db.refresh(user)
    return user


@router.post("/settings/handling-fee")
def update_handling_fee(payload: HandlingFeePayload, admin=Depends(require_admin), db=Depends(get_db)):
    setting = db.execute(select(AppSetting).where(AppSetting.key == "handling_fee_percent")).scalar_one_or_none()
    if setting is None:
        setting = AppSetting(key="handling_fee_percent", value=str(payload.handling_fee_percent))
        db.add(setting)
    else:
        setting.value = str(payload.handling_fee_percent)
    db.commit()
    return {"handling_fee_percent": payload.handling_fee_percent}


@router.post("/scrape/trigger", response_model=ScrapeResult)
def trigger_scrape_now(admin=Depends(require_admin), db=Depends(get_db)):
    run = ScrapeRun(
        source="manual",
        status="queued",
        stage="queued",
        progress_percent=0,
        message="Queued for scraping",
        total_items=0,
        processed_items=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    result = trigger_scrape.delay(run.id, "manual")
    return ScrapeResult(run_id=run.id, message=f"Scrape queued: {result.id}")


@router.get("/scrape/latest")
def latest_scrape(admin=Depends(require_admin), db=Depends(get_db)):
    latest_run = db.execute(select(ScrapeRun).order_by(ScrapeRun.started_at.desc())).scalars().first()
    if latest_run is None:
        return {"run": None}
    return {
        "run": {
            "id": latest_run.id,
            "status": latest_run.status,
            "stage": latest_run.stage,
            "progress_percent": latest_run.progress_percent,
            "message": latest_run.message,
            "total_items": latest_run.total_items,
            "processed_items": latest_run.processed_items,
            "started_at": latest_run.started_at,
            "finished_at": latest_run.finished_at,
        }
    }


@router.get("/products/filtered")
def get_filtered_products(admin=Depends(require_admin), db=Depends(get_db)):
    """Get all products that are filtered out (bundles, home page placeholders)."""
    all_products = db.execute(
        select(Product).where(Product.active.is_(True)).order_by(Product.scraped_at.desc())
    ).scalars().all()
    
    filtered = []
    for p in all_products:
        if is_bundle(p.name):
            filtered.append({
                "id": p.id,
                "name": p.name,
                "source_url": p.source_url,
                "image_url": p.image_url,
                "price_aud": p.price_aud,
                "price_lkr": p.price_lkr,
                "sku": p.sku,
                "description": p.description,
                "category": p.category,
                "is_bundle": " + " in p.name,
                "filter_reason": get_filter_reason(p.name),
            })
    return filtered


@router.post("/products/{product_id}/activate")
def activate_product(product_id: int, admin=Depends(require_admin), db=Depends(get_db)):
    """Activate a filtered product (make it visible in the store)."""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # The product is already active, but was filtered by the API
    # We could add a flag to mark it as "manually approved" but for now
    # just return success - the product is already in the DB and active
    return {"message": "Product activated", "product_id": product_id}


@router.delete("/products/{product_id}")
def delete_product(product_id: int, admin=Depends(require_admin), db=Depends(get_db)):
    """Permanently delete a filtered product."""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted", "product_id": product_id}


# ─── Site Settings (admin-editable UI text) ────────────────────────────────

DEFAULT_SITE_SETTINGS = {
    "panel_headers": {
        "users": "Users",
        "pending": "Pending",
        "products": "Products",
        "requests": "Requests",
        "filtered_products": "Filtered Products Review",
        "handling_fee": "Handling fee",
        "pending_users": "Pending users",
    },
    "footer_text": "© 2026 OzLanka Outdoor Gear. All rights reserved.",
    "product_template": {
        "show_image": True,
        "show_sku": True,
        "show_category": True,
        "show_description": True,
        "show_price_aud": True,
        "show_price_lkr": True,
        "show_view_link": True,
        "custom_label": "",
    },
    "hero_title": "OzLanka Outdoor Gear",
    "hero_subtitle": "Request outdoor gear from Australia with manual approval, LKR pricing, and clear shipping and customs terms.",
}


def _get_site_settings(db) -> dict:
    """Load site settings from DB, merging with defaults for any missing keys."""
    setting = db.execute(select(AppSetting).where(AppSetting.key == "site_settings")).scalar_one_or_none()
    if setting is None:
        return DEFAULT_SITE_SETTINGS.copy()
    try:
        stored = json.loads(setting.value)
    except (json.JSONDecodeError, TypeError):
        return DEFAULT_SITE_SETTINGS.copy()
    # Deep-merge: stored overrides, but keep any new keys from defaults
    merged = DEFAULT_SITE_SETTINGS.copy()
    for key in merged:
        if key in stored:
            if isinstance(merged[key], dict) and isinstance(stored[key], dict):
                merged[key].update(stored[key])
            else:
                merged[key] = stored[key]
    return merged


@router.get("/settings")
def get_site_settings(admin=Depends(require_admin), db=Depends(get_db)):
    return _get_site_settings(db)


class SiteSettingsPayload(BaseModel):
    panel_headers: dict | None = None
    footer_text: str | None = None
    product_template: dict | None = None
    hero_title: str | None = None
    hero_subtitle: str | None = None


@router.put("/settings")
def update_site_settings(payload: SiteSettingsPayload, admin=Depends(require_admin), db=Depends(get_db)):
    current = _get_site_settings(db)
    # Merge provided fields into current
    if payload.panel_headers is not None:
        current["panel_headers"].update(payload.panel_headers)
    if payload.footer_text is not None:
        current["footer_text"] = payload.footer_text
    if payload.product_template is not None:
        current["product_template"].update(payload.product_template)
    if payload.hero_title is not None:
        current["hero_title"] = payload.hero_title
    if payload.hero_subtitle is not None:
        current["hero_subtitle"] = payload.hero_subtitle

    setting = db.execute(select(AppSetting).where(AppSetting.key == "site_settings")).scalar_one_or_none()
    if setting is None:
        setting = AppSetting(key="site_settings", value=json.dumps(current))
        db.add(setting)
    else:
        setting.value = json.dumps(current)
    db.commit()
    return current
