"""User LLM settings endpoints."""
import base64
import os
from datetime import datetime, timezone
import time

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.user_llm_settings import UserLlmSettings
from app.schemas.settings import (
    LlmSettingsRequest,
    LlmSettingsResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


def _get_encrypt_key() -> bytes:
    raw = os.environ.get("NOVELCRAFT_ENCRYPT_KEY", settings.jwt_secret)
    return base64.urlsafe_b64encode(raw.encode("utf-8").ljust(32, b"\x00")[:32])


def _encrypt_api_key(plain: str) -> str:
    key = _get_encrypt_key()
    data = plain.encode("utf-8")
    encrypted = bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))
    return base64.urlsafe_b64encode(encrypted).decode()


def _decrypt_api_key(encrypted: str) -> str:
    key = _get_encrypt_key()
    data = base64.urlsafe_b64decode(encrypted)
    decrypted = bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))
    return decrypted.decode("utf-8")


def _mask_api_key(key: str | None) -> str | None:
    if not key or len(key) < 8:
        return None
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


async def _get_user_settings(user_id: str, db: AsyncSession) -> UserLlmSettings | None:
    result = await db.execute(
        select(UserLlmSettings).where(UserLlmSettings.user_id == user_id)
    )
    return result.scalar_one_or_none()


def _settings_to_response(record: UserLlmSettings | None, user_id: str) -> LlmSettingsResponse:
    if not record:
        return LlmSettingsResponse(
            id="", user_id=user_id,
            api_key_masked=None, base_url=None, model=None,
            created_at="", updated_at="",
        )
    masked = None
    if record.api_key_encrypted:
        try:
            masked = _mask_api_key(_decrypt_api_key(record.api_key_encrypted))
        except Exception:
            masked = "****"
    return LlmSettingsResponse(
        id=record.id, user_id=record.user_id,
        api_key_masked=masked, base_url=record.base_url, model=record.model,
        created_at=record.created_at.isoformat() if record.created_at else "",
        updated_at=record.updated_at.isoformat() if record.updated_at else "",
    )


@router.get("/llm", response_model=LlmSettingsResponse)
async def get_llm_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_user_settings(current_user.id, db)
    return _settings_to_response(record, current_user.id)


@router.put("/llm", response_model=LlmSettingsResponse)
async def update_llm_settings(
    body: LlmSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_user_settings(current_user.id, db)

    if record:
        if body.api_key is not None:
            record.api_key_encrypted = _encrypt_api_key(body.api_key) if body.api_key else None
        if body.base_url is not None:
            record.base_url = body.base_url
        if body.model is not None:
            record.model = body.model
        record.updated_at = datetime.now(timezone.utc)
    else:
        encrypted = _encrypt_api_key(body.api_key) if body.api_key else None
        record = UserLlmSettings(
            user_id=current_user.id,
            api_key_encrypted=encrypted,
            base_url=body.base_url,
            model=body.model,
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)
    return _settings_to_response(record, current_user.id)


@router.post("/llm/test", response_model=ConnectionTestResponse)
async def test_llm_connection(
    body: ConnectionTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    api_key = body.api_key
    base_url = body.base_url
    model = body.model

    # Resolve from saved settings if not provided in body
    if not api_key or not base_url or not model:
        record = await _get_user_settings(current_user.id, db)
        if record:
            if not api_key and record.api_key_encrypted:
                try:
                    api_key = _decrypt_api_key(record.api_key_encrypted)
                except Exception:
                    pass
            if not base_url and record.base_url:
                base_url = record.base_url
            if not model and record.model:
                model = record.model

    # Fallback to .env
    api_key = api_key or settings.llm_api_key
    base_url = base_url or settings.llm_base_url
    model = model or settings.llm_model

    if not api_key:
        return ConnectionTestResponse(
            success=False,
            message="No API key configured. Please save your API key in settings first.",
        )

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                },
            )
            elapsed = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return ConnectionTestResponse(
                    success=True,
                    message=f"Connection successful. Ping response: {content}",
                    elapsed_ms=elapsed,
                )
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                detail = resp.text[:200]
            return ConnectionTestResponse(
                success=False,
                message=f"API error ({resp.status_code}): {detail}",
                elapsed_ms=elapsed,
            )
    except httpx.ConnectError:
        elapsed = int((time.time() - start) * 1000)
        return ConnectionTestResponse(
            success=False,
            message=f"Cannot connect to {base_url}. Check the URL and network.",
            elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return ConnectionTestResponse(
            success=False,
            message=str(e)[:300],
            elapsed_ms=elapsed,
        )
