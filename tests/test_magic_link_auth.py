from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from jose import jwt
from sqlalchemy import select

from app.api.routers.auth import hash_magic_link_token
from app.core.config import settings
from app.models.magic_link_token import MagicLinkToken
from app.models.vendor import Vendor
from app.services.email_client import EmailClient


async def create_vendor(db_session, *, email="vendor@example.com", is_active=True):
    vendor = Vendor(
        company_name="Example Vendor",
        email=email,
        hashed_password="not-used-in-this-test",
        is_active=is_active,
    )
    db_session.add(vendor)
    await db_session.commit()
    await db_session.refresh(vendor)
    return vendor


def token_from_email(email_body):
    verify_url = email_body.split('href="', 1)[1].split('"', 1)[0]
    return parse_qs(urlparse(verify_url).query)["token"][0]


@pytest.mark.asyncio
async def test_request_magic_link_stores_hash_and_sends_ten_minute_link(
    client, db_session, monkeypatch
):
    vendor = await create_vendor(db_session)
    sent_emails = []

    async def fake_send_email(to_email, subject, html_body):
        sent_emails.append((to_email, subject, html_body))
        return True

    monkeypatch.setattr(EmailClient, "send_email", fake_send_email)

    response = await client.post("/api/auth/magic-link/request", json={"email": vendor.email})

    assert response.status_code == 200
    assert response.json()["message"] == (
        "If an active vendor account exists for that email, a sign-in link has been sent."
    )
    assert len(sent_emails) == 1
    assert sent_emails[0][0] == vendor.email

    raw_token = token_from_email(sent_emails[0][2])
    stored_token = (
        await db_session.execute(
            select(MagicLinkToken).where(MagicLinkToken.vendor_id == vendor.id)
        )
    ).scalar_one()

    assert stored_token.token_hash == hash_magic_link_token(raw_token)
    assert stored_token.token_hash != raw_token
    expires_at = stored_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    remaining = expires_at - datetime.now(timezone.utc)
    assert timedelta(minutes=9, seconds=55) <= remaining <= timedelta(minutes=10, seconds=5)


@pytest.mark.asyncio
async def test_request_magic_link_deletes_previous_tokens(client, db_session, monkeypatch):
    vendor = await create_vendor(db_session)
    sent_emails = []

    async def fake_send_email(to_email, subject, html_body):
        sent_emails.append(html_body)
        return True

    monkeypatch.setattr(EmailClient, "send_email", fake_send_email)

    await client.post("/api/auth/magic-link/request", json={"email": vendor.email})
    first_token = token_from_email(sent_emails[0])
    await client.post("/api/auth/magic-link/request", json={"email": vendor.email})
    second_token = token_from_email(sent_emails[1])

    stored_tokens = (
        await db_session.execute(
            select(MagicLinkToken).where(MagicLinkToken.vendor_id == vendor.id)
        )
    ).scalars().all()

    assert len(stored_tokens) == 1
    assert stored_tokens[0].token_hash == hash_magic_link_token(second_token)
    assert first_token != second_token


@pytest.mark.asyncio
async def test_request_magic_link_does_not_reveal_unknown_or_inactive_accounts(
    client, db_session, monkeypatch
):
    inactive_vendor = await create_vendor(db_session, is_active=False)
    sent_emails = []

    async def fake_send_email(to_email, subject, html_body):
        sent_emails.append(to_email)
        return True

    monkeypatch.setattr(EmailClient, "send_email", fake_send_email)

    unknown_response = await client.post(
        "/api/auth/magic-link/request", json={"email": "unknown@example.com"}
    )
    inactive_response = await client.post(
        "/api/auth/magic-link/request", json={"email": inactive_vendor.email}
    )

    assert unknown_response.status_code == 200
    assert inactive_response.status_code == 200
    assert unknown_response.json() == inactive_response.json()
    assert sent_emails == []


@pytest.mark.asyncio
async def test_verify_magic_link_issues_jwt_and_rejects_reuse(client, db_session, monkeypatch):
    vendor = await create_vendor(db_session)
    sent_emails = []

    async def fake_send_email(to_email, subject, html_body):
        sent_emails.append(html_body)
        return True

    monkeypatch.setattr(EmailClient, "send_email", fake_send_email)
    await client.post("/api/auth/magic-link/request", json={"email": vendor.email})
    raw_token = token_from_email(sent_emails[0])

    response = await client.get(
        "/api/auth/magic-link/verify", params={"token": raw_token}
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    payload = jwt.decode(
        response.json()["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    assert payload["sub"] == str(vendor.id)

    reused_response = await client.get(
        "/api/auth/magic-link/verify", params={"token": raw_token}
    )
    assert reused_response.status_code == 401


@pytest.mark.asyncio
async def test_verify_magic_link_rejects_expired_token(client, db_session):
    vendor = await create_vendor(db_session)
    expired_token = "expired-token"
    db_session.add(
        MagicLinkToken(
            vendor_id=vendor.id,
            token_hash=hash_magic_link_token(expired_token),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
    )
    await db_session.commit()

    response = await client.get(
        "/api/auth/magic-link/verify", params={"token": expired_token}
    )

    assert response.status_code == 401
    stored_token = (
        await db_session.execute(
            select(MagicLinkToken).where(MagicLinkToken.vendor_id == vendor.id)
        )
    ).scalar_one()
    assert stored_token.used_at is None


@pytest.mark.asyncio
async def test_verify_magic_link_rejects_unknown_token(client):
    response = await client.get(
        "/api/auth/magic-link/verify", params={"token": "does-not-exist"}
    )

    assert response.status_code == 401
