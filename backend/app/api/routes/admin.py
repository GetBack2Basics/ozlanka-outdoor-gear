from fastapi import APIRouter, Depends, HTTPException
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

DEMO_PRODUCTS = [
  {
    "name": "ARB 4x4 Snorkel",
    "source_url": "https://www.4wdsupacentre.com.au/arb-snorkel.html",
    "price_aud": 450,
    "msrp_aud": 420,
    "rrp_aud": 480,
    "image_url": "https://www.4wdsupacentre.com.au/media/snorkel.jpg",
    "sku": "ARB-SNK-01",
    "description": "Heavy-duty snorkel for Australian outback crossings.",
  },
  {
    "name": "Rhino-Rack Roof Bars",
    "source_url": "https://www.4wdsupacentre.com.au/rhino-roof-bars.html",
    "price_aud": 890,
    "msrp_aud": 849,
    "rrp_aud": 929,
    "image_url": "https://www.4wdsupacentre.com.au/media/roof-bars.jpg",
    "sku": "RR-RB-02",
    "description": "Lockable mounted roof bars for long-distance touring.",
  },
  {
    "name": "GME UHF Radio Pack",
    "source_url": "https://www.4wdsupacentre.com.au/gme-uhf.html",
    "price_aud": 320,
    "msrp_aud": 299,
    "rrp_aud": 349,
    "image_url": "https://www.4wdsupacentre.com.au/media/uhf.jpg",
    "sku": "GME-UHF-03",
    "description": "Compact UHF radio pack for remote trail calls.",
  },
  {
    "name": "Kings Canvas Swag",
    "source_url": "https://www.4wdsupacentre.com.au/kings-swag.html",
    "price_aud": 180,
    "msrp_aud": 169,
    "rrp_aud": 199,
    "image_url": "https://www.4wdsupacentre.com.au/media/swag.jpg",
    "sku": "KNG-SWAG-04",
    "description": "Single canvas swag with built-in mosquito net.",
  },
  {
    "name": "Redarc BCDC Charger",
    "source_url": "https://www.4wdsupacentre.com.au/redarc-bcdc.html",
    "price_aud": 520,
    "msrp_aud": 499,
    "rrp_aud": 549,
    "image_url": "https://www.4wdsupacentre.com.au/media/bcdc.jpg",
    "sku": "RED-BCDC-05",
    "description": "Dual battery charger with solar input support.",
  },
  {
    "name": "ARB Zero Fridge",
    "source_url": "https://www.4wdsupacentre.com.au/arb-zero-fridge.html",
    "price_aud": 1250,
    "msrp_aud": 1199,
    "rrp_aud": 1299,
    "image_url": "https://www.4wdsupacentre.com.au/media/fridge.jpg",
    "sku": "ARB-ZFR-06",
    "description": "Portable zero fridge for camp kitchens.",
  },
  {
    "name": "Ironman 4x4 Suspension",
    "source_url": "https://www.4wdsupacentre.com.au/ironman-suspension.html",
    "price_aud": 2100,
    "msrp_aud": 1999,
    "rrp_aud": 2199,
    "image_url": "https://www.4wdsupacentre.com.au/media/suspension.jpg",
    "sku": "IRON-SUS-07",
    "description": "Lifted suspension kit with remote reservoir shocks.",
  },
  {
    "name": "GripHero Steps",
    "source_url": "https://www.4wdsupacentre.com.au/griphero-steps.html",
    "price_aud": 470,
    "msrp_aud": 449,
    "rrp_aud": 499,
    "image_url": "https://www.4wdsupacentre.com.au/media/steps.jpg",
    "sku": "GH-STP-08",
    "description": "Tub-mounted side steps with anti-slip tread.",
  },
  {
    "name": "KniCo Camp Oven",
    "source_url": "https://www.4wdsupacentre.com.au/knico-camp-oven.html",
    "price_aud": 95,
    "msrp_aud": 89,
    "rrp_aud": 109,
    "image_url": "https://www.4wdsupacentre.com.au/media/oven.jpg",
    "sku": "KNI-CO-09",
    "description": "Classic camp oven set for open-fire cooking.",
  },
  {
    "name": "XTM 4x4 Light Bar",
    "source_url": "https://www.4wdsupacentre.com.au/xtm-lightbar.html",
    "price_aud": 380,
    "msrp_aud": 349,
    "rrp_aud": 399,
    "image_url": "https://www.4wdsupacentre.com.au/media/lightbar.jpg",
    "sku": "XTM-LB-10",
    "description": "Wide beam spot light bar for night recovery work.",
  },
]



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


@router.post("/seed-products")
def seed_demo_products(admin=Depends(require_admin), db=Depends(get_db)):
    inserted = 0
    for item in DEMO_PRODUCTS:
        existing = db.execute(select(Product).where(Product.sku == item["sku"])).scalar_one_or_none()
        if existing is not None:
            continue
        price_aud = choose_reference_price(item.get("msrp_aud"), item.get("rrp_aud"), item["price_aud"])
        fee = get_settings().handling_fee_percent
        rate = get_aud_to_lkr_rate()
        price_lkr = calculate_lkr_price(price_aud, rate, fee)
        product = Product(
            source_url=item["source_url"],
            source_name="4WD Supacentre",
            name=item["name"],
            sku=item["sku"],
            description=item["description"],
            image_url=item["image_url"],
            price_aud=price_aud,
            msrp_aud=item.get("msrp_aud"),
            rrp_aud=item.get("rrp_aud"),
            price_lkr=price_lkr,
            handling_fee_percent=fee,
            exchange_rate_aud_lkr=rate,
            active=True,
        )
        db.add(product)
        inserted += 1
    db.commit()
    return {"inserted": inserted}

