"""Gmail acquisition endpoints (Phase 3).

Picker surface: connection status, OAuth start/callback, search, selected
message metadata, analyze, and revoke/disconnect. ``analyze`` resolves the
message id through the authenticated connection's own access token
(``userId=me``), so there is no cross-account read path. No code, token, or
secret ever appears in a response or a redirect URL.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from schemas import (
    GmailAnalyzeRequest,
    GmailAuthStartResponse,
    GmailMessageOut,
    GmailRevokeResponse,
    GmailSearchResponse,
    GmailStatusResponse,
    UploadResponse,
)
from services.gmail.acquisition import GmailService, build_gmail_service
from services.gmail.errors import (
    GmailAuthError,
    GmailAuthRequiredError,
    GmailConfigError,
    GmailDuplicateError,
    GmailError,
    GmailMalformedRawError,
    GmailMessageNotFoundError,
    GmailNetworkError,
    GmailPermissionError,
    GmailRateLimitError,
    GmailServerError,
    GmailStateExpiredError,
    GmailStateInvalidError,
    GmailStateReusedError,
    GmailTooLargeError,
)

router = APIRouter(prefix="/api/gmail", tags=["gmail"])

_service: GmailService | None = None


def get_gmail_service() -> GmailService:
    """Single service instance (holds the expiring OAuth state store)."""
    global _service
    if _service is None:
        _service = build_gmail_service()
    return _service


def _as_http(exc: GmailError) -> HTTPException:
    if isinstance(exc, GmailConfigError):
        return HTTPException(503, str(exc))
    if isinstance(exc, GmailAuthRequiredError):
        return HTTPException(401, "Gmail is not connected. Connect Gmail and retry.")
    if isinstance(exc, GmailAuthError):
        return HTTPException(401, str(exc))
    if isinstance(exc, GmailPermissionError):
        return HTTPException(403, str(exc))
    if isinstance(exc, GmailMessageNotFoundError):
        return HTTPException(404, str(exc))
    if isinstance(exc, GmailRateLimitError):
        return HTTPException(429, str(exc))
    if isinstance(exc, GmailServerError):
        return HTTPException(502, str(exc))
    if isinstance(exc, GmailNetworkError):
        return HTTPException(502, str(exc))
    if isinstance(exc, GmailTooLargeError):
        return HTTPException(413, str(exc))
    if isinstance(exc, GmailMalformedRawError):
        return HTTPException(422, str(exc))
    if isinstance(exc, GmailDuplicateError):
        return HTTPException(409, str(exc))
    if isinstance(exc, GmailStateExpiredError):
        return HTTPException(400, "OAuth state expired; start over")
    if isinstance(exc, (GmailStateInvalidError, GmailStateReusedError)):
        return HTTPException(400, "OAuth state invalid; start over")
    return HTTPException(502, "Gmail acquisition failed")


@router.get("/auth/start", response_model=GmailAuthStartResponse)
async def gmail_auth_start(service: GmailService = Depends(get_gmail_service)):
    try:
        auth_url = await service.auth_url()
    except GmailError as exc:
        raise _as_http(exc)
    return GmailAuthStartResponse(auth_url=auth_url)


@router.get("/oauth/callback")
async def gmail_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    service: GmailService = Depends(get_gmail_service),
):
    target = await service.complete_callback(state or "", code or "", error)
    return RedirectResponse(status_code=303, url=target)


@router.get("/status", response_model=GmailStatusResponse)
async def gmail_status(service: GmailService = Depends(get_gmail_service)):
    return GmailStatusResponse(**await service.status())


@router.post("/revoke", response_model=GmailRevokeResponse)
async def gmail_revoke(service: GmailService = Depends(get_gmail_service)):
    await service.revoke()
    return GmailRevokeResponse(status="disconnected")


@router.get("/search", response_model=GmailSearchResponse)
async def gmail_search(
    q: str = "",
    page_token: Optional[str] = None,
    max_results: int = 10,
    service: GmailService = Depends(get_gmail_service),
):
    try:
        data = await service.search(q, page_token, max_results)
    except GmailError as exc:
        raise _as_http(exc)
    return GmailSearchResponse(**data)


@router.get("/messages/{message_id}/metadata", response_model=GmailMessageOut)
async def gmail_message_metadata(
    message_id: str,
    service: GmailService = Depends(get_gmail_service),
):
    try:
        data = await service.get_metadata(message_id)
    except GmailError as exc:
        raise _as_http(exc)
    return GmailMessageOut(**data)


@router.post("/analyze", response_model=UploadResponse)
async def gmail_analyze(
    payload: GmailAnalyzeRequest,
    service: GmailService = Depends(get_gmail_service),
):
    try:
        result = await service.analyze(payload.message_id)
    except GmailError as exc:
        raise _as_http(exc)
    return UploadResponse(
        case_id=result["case_id"],
        case_number=result["case_number"],
        status="active",
        source_type="gmail",
        evidence_id=result["evidence_id"],
        analysis_status="completed",
        message=(
            f"Analysis complete. Threat: {result['threat_type']}, "
            f"Risk: {result['risk_level']} ({result['risk_score']}/100)"
        ),
    )