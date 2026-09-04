import uuid
from datetime import datetime, timezone, timedelta

class StorageService:
    """
    Wrapper for Azure Blob Storage or AWS S3 async operations.
    """
    @staticmethod
    async def upload_file(file_bytes: bytes, filename: str, content_type: str) -> str:
        # In production: await s3_client.put_object(...)
        unique_name = f"{uuid.uuid4()}_{filename}"
        s3_url = f"s3://vendorflow-secure-bucket/documents/{unique_name}"
        return s3_url

    @staticmethod
    async def generate_presigned_url(s3_url: str, expires_in_minutes: int = 15) -> str:
        # In production: generate temporary cryptographic URL for the private bucket
        token = uuid.uuid4().hex
        return f"https://storage.vendorflow.com/download?file={s3_url.split('/')[-1]}&token={token}"