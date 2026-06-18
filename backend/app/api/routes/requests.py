from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.routes.auth import get_current_user, get_db
from app.models import ApprovalStatus, RequestListItem, User
from app.schemas import RequestListCreate, RequestListRead

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=RequestListRead)
def create_request(payload: RequestListCreate, user: User = Depends(get_current_user), db=Depends(get_db)):
    if not user.is_active or user.approval_status != ApprovalStatus.approved:
        raise HTTPException(status_code=403, detail="User is not approved")
    item = RequestListItem(user_id=user.id, product_name=payload.product_name, quantity=payload.quantity, notes=payload.notes)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/me", response_model=list[RequestListRead])
def my_requests(user: User = Depends(get_current_user), db=Depends(get_db)):
    if user.approval_status != ApprovalStatus.approved:
        raise HTTPException(status_code=403, detail="User is not approved")
    return db.execute(select(RequestListItem).where(RequestListItem.user_id == user.id).order_by(RequestListItem.created_at.desc())).scalars().all()
