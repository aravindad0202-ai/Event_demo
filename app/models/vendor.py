from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    bank_routing_number: Mapped[str | None] = mapped_column(String(50))
    tax_id: Mapped[str | None] = mapped_column(String(50))
    compliance_status: Mapped[str] = mapped_column(String(50), default="pending")
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    invoices = relationship("Invoice", back_populates="vendor", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="vendor", cascade="all, delete-orphan")
    magic_link_tokens = relationship(
        "MagicLinkToken", back_populates="vendor", cascade="all, delete-orphan"
    )