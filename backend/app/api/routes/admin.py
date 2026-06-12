from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from app.api.routes.auth import get_db, require_admin
from app.core.config import get_settings
from app.models import AppSetting, ApprovalStatus, Product, RequestListItem, ScrapeRun, User
from app.schemas import HandlingFeePayload, ScrapeResult, UserRead
from app.workers.tasks import trigger_scrape

router = APIRouter(prefix="/admin", tags=["admin"])


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
