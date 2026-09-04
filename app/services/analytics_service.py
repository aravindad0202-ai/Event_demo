from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invoice import Invoice
from app.schemas.requests import InvoiceStatus

class AnalyticsService:
    @staticmethod
    async def get_vendor_metrics(db: AsyncSession, vendor_id: int) -> dict:
        # Aggregate Paid Invoices (YTD Earned)
        ytd_query = select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.vendor_id == vendor_id,
            Invoice.status == InvoiceStatus.PAID
        )
        ytd_result = await db.execute(ytd_query)
        ytd_earned = ytd_result.scalar()

        # Aggregate Pending Approvals
        pending_query = select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.vendor_id == vendor_id,
            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.MANAGER_REVIEW])
        )
        pending_result = await db.execute(pending_query)
        pending_balance = pending_result.scalar()

        # Count Invoices
        count_query = select(func.count(Invoice.id)).where(Invoice.vendor_id == vendor_id)
        count_result = await db.execute(count_query)
        invoice_count = count_result.scalar()

        return {
            "ytd_earned": float(ytd_earned),
            "pending_approval_balance": float(pending_balance),
            "overdue_balance": 0.0,  # Placeholder for complex date logic
            "invoice_count_this_month": invoice_count
        }