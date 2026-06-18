from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password, verify_password
from app.models import ApprovalStatus, User, UserRole
from app.schemas import Token, UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> User:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


@router.post("/signup", response_model=UserRead)
def signup(payload: UserCreate, db=Depends(get_db)):
    if db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), approval_status=ApprovalStatus.pending)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db=Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if user.approval_status != ApprovalStatus.approved:
        raise HTTPException(status_code=403, detail="Awaiting admin approval")
    return Token(access_token=create_access_token(str(user.id), user.role.value))


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user
