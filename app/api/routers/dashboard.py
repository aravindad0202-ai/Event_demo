from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.vendor import Vendor
from app.schemas.response import DashboardMetricsResponse
from app.services.analytics_service import AnalyticsService
from app.api.dependencies import get_current_vendor

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    metrics = await AnalyticsService.get_vendor_metrics(db, current_vendor.id)
    return DashboardMetricsResponse(**metrics)