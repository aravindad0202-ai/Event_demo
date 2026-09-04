import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.magic_link_token import MagicLinkToken
from app.models.vendor import Vendor
from app.schemas.requests import LoginRequest, MagicLinkRequest
from app.schemas.response import MagicLinkRequestResponse, TokenResponse, VendorResponse
from app.api.dependencies import get_current_vendor
from app.services.email_client import EmailClient

router = APIRouter(prefix="/auth", tags=["Authentication"])

MAGIC_LINK_TTL = timedelta(minutes=10)


def hash_magic_link_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

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


@router.post("/magic-link/request", response_model=MagicLinkRequestResponse)
async def request_magic_link(
    request: MagicLinkRequest, db: AsyncSession = Depends(get_db)
):
    vendor_result = await db.execute(select(Vendor).where(Vendor.email == str(request.email)))
    vendor = vendor_result.scalar_one_or_none()

    if vendor and vendor.is_active:
        await db.execute(delete(MagicLinkToken).where(MagicLinkToken.vendor_id == vendor.id))

        raw_token = secrets.token_urlsafe(32)
        db.add(
            MagicLinkToken(
                vendor_id=vendor.id,
                token_hash=hash_magic_link_token(raw_token),
                expires_at=datetime.now(timezone.utc) + MAGIC_LINK_TTL,
            )
        )
        await db.flush()

        verify_url = (
            f"{settings.MAGIC_LINK_BASE_URL.rstrip('/')}{settings.API_V1_STR}"
            f"/auth/magic-link/verify?token={raw_token}"
        )
        await EmailClient.send_email(
            to_email=vendor.email,
            subject="Your VendorFlow sign-in link",
            html_body=f'<p>Sign in to VendorFlow: <a href="{verify_url}">Continue</a></p>',
        )

    await db.commit()
    return MagicLinkRequestResponse(
        message="If an active vendor account exists for that email, a sign-in link has been sent."
    )


@router.get("/magic-link/verify", response_model=TokenResponse)
async def verify_magic_link(token: str, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    token_hash = hash_magic_link_token(token)
    token_result = await db.execute(
        select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash)
    )
    magic_link_token = token_result.scalar_one_or_none()

    expires_at = magic_link_token.expires_at if magic_link_token else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if magic_link_token is None or expires_at <= now or magic_link_token.used_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link",
        )

    consume_result = await db.execute(
        update(MagicLinkToken)
        .where(
            MagicLinkToken.id == magic_link_token.id,
            MagicLinkToken.used_at.is_(None),
            MagicLinkToken.expires_at > now,
        )
        .values(used_at=now)
    )
    if consume_result.rowcount != 1:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link",
        )

    vendor_result = await db.execute(select(Vendor).where(Vendor.id == magic_link_token.vendor_id))
    vendor = vendor_result.scalar_one_or_none()
    if vendor is None or not vendor.is_active:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link",
        )

    await db.commit()
    return TokenResponse(access_token=create_access_token(subject=vendor.id))

@router.get("/me", response_model=VendorResponse)
async def get_profile(current_vendor: Vendor = Depends(get_current_vendor)):
    return current_vendor