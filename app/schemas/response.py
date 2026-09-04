from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict
from app.schemas.requests import DocumentType, InvoiceStatus

# --- AUTH RESPONSES ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MagicLinkRequestResponse(BaseModel):
    message: str

# --- VENDOR RESPONSES ---
class VendorResponse(BaseModel):
    id: int
    company_name: str
    email: EmailStr
    compliance_status: str
    
    # Allows Pydantic to read from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)

# --- INVOICE RESPONSES ---
class InvoiceResponse(BaseModel):
    id: int
    vendor_id: int
    amount: float
    due_date: datetime
    description: str
    status: InvoiceStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedInvoiceResponse(BaseModel):
    items: list[InvoiceResponse]
    total_count: int
    page: int

# --- DOCUMENT RESPONSES ---
class DocumentResponse(BaseModel):
    id: int
    document_type: DocumentType
    uploaded_at: datetime
    file_size_bytes: int
    
    model_config = ConfigDict(from_attributes=True)

class PresignedUrlResponse(BaseModel):
    download_url: HttpUrl
    expires_in_seconds: int

# --- DASHBOARD RESPONSES ---
class DashboardMetricsResponse(BaseModel):
    ytd_earned: float
    pending_approval_balance: float
    overdue_balance: float
    invoice_count_this_month: int