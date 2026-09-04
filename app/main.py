from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.audit_middleware import AuditLogMiddleware
from app.api.routers import auth, invoices, dashboard

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Custom Middleware
app.add_middleware(AuditLogMiddleware)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(invoices.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
# app.include_router(documents.router, prefix=settings.API_V1_STR) # (Omitted for brevity, follows same pattern)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}