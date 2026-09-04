from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog

class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Intercepts write requests (POST, PUT, DELETE) and logs them for compliance.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only log state-changing requests
        if request.method in ["POST", "PUT", "DELETE"]:
            # Run the DB insert in a separate session context to avoid locking the request
            async with AsyncSessionLocal() as db:
                audit_entry = AuditLog(
                    action_type=f"{request.method} {request.url.path}",
                    ip_address=request.client.host if request.client else "unknown",
                    # Note: Extracting Vendor ID from JWT in middleware requires decoding token here.
                    # For performance, we just log the action and IP in this layer.
                )
                db.add(audit_entry)
                await db.commit()
                
        return response