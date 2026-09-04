from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

# --- SHARED ENUMS ---
class DocumentType(str, Enum):
    W9 = "W9"
    NDA = "NDA"
    BANK_DETAILS = "BANK_DETAILS"

class InvoiceStatus(str, Enum):
    PENDING = "Pending"
    MANAGER_REVIEW = "Manager_Review"
    FINANCE_APPROVED = "Finance_Approved"
    PAID = "Paid"

# --- AUTH REQUESTS ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class MagicLinkRequest(BaseModel):
    email: EmailStr

# --- INVOICE REQUESTS ---
class InvoiceCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Invoice amount must be greater than zero")
    due_date: datetime
    description: str = Field(..., max_length=255)

class InvoiceStatusUpdate(BaseModel):
    new_status: InvoiceStatus
    approval_notes: str | None = Field(default=None, max_length=500)

# --- DOCUMENT REQUESTS ---
class DocumentUploadMetadata(BaseModel):
    document_type: DocumentType
    notes: str | None = Field(default=None, max_length=255)