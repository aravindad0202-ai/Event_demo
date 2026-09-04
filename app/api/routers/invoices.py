from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.vendor import Vendor
from app.models.invoice import Invoice
from app.schemas.requests import InvoiceCreate, InvoiceStatusUpdate
from app.schemas.response import InvoiceResponse
from app.api.dependencies import get_current_vendor

router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.post("/", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    new_invoice = Invoice(
        vendor_id=current_vendor.id,
        amount=payload.amount,
        due_date=payload.due_date,
        description=payload.description
    )
    db.add(new_invoice)
    await db.commit()
    await db.refresh(new_invoice)
    return new_invoice

@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    result = await db.execute(
        select(Invoice).where(Invoice.vendor_id == current_vendor.id).order_by(Invoice.created_at.desc())
    )
    return result.scalars().all()