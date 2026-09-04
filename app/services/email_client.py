import logging

logger = logging.getLogger(__name__)

class EmailClient:
    """
    Enterprise Email Client wrapper (SMTP / SendGrid / SES).
    For this environment, it securely logs the action without external network calls.
    """
    @staticmethod
    async def send_email(to_email: str, subject: str, html_body: str) -> bool:
        # In production, this would use aiosmtplib or an async cloud SDK
        logger.info(f"Connecting to SMTP server...")
        logger.info(f"Email sent to: {to_email} | Subject: {subject}")
        logger.debug(f"Body: {html_body}")
        return True