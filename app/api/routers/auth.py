from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.vendor import Vendor
from app.schemas.requests import LoginRequest
from app.schemas.responses import TokenResponse, VendorResponse
from app.api.dependencies import get_current_vendor

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.email == credentials.email))
    vendor = result.scalar_one_or_none()
    
    if not vendor or not verify_password(credentials.password, vendor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    if not vendor.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=vendor.id)
    return TokenResponse(access_token=access_token)

@router.get("/me", response_model=VendorResponse)
async def get_profile(current_vendor: Vendor = Depends(get_current_vendor)):
    return current_vendor