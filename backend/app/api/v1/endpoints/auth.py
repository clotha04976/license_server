from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .... import schemas
from ....core import security
from ....core.config import settings
from ....core.dependencies import get_db
from .... import schemas, crud
from ....core import security
from ....core.config import settings
from ....core.dependencies import get_db
from ....core.rate_limiter import limiter

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")  # 限制每分鐘最多 5 次登入嘗試
def login_for_access_token(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    admin = crud.admin.get_by_username(db, username=form_data.username)
    if not admin or not security.verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=admin.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}