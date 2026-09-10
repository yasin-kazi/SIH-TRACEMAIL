"""Composite risk scoring engine."""
from __future__ import annotations
from typing import Any


def calculate_risk_score(
    identity_score: int,
    spf_result: str,
    dkim_result: str,
    dmarc_result: str,
    has_reply_to_mismatch: bool,
    is_typosquat: bool,
    domain_age_days: int | None = None,
    threat_feeds: int = 0,
) -> dict[str, Any]:
    """Calculate composite risk score from multiple signals.

    Returns risk_score (0-100), risk_level, model_confidence, evidence_confidence.
    """
    score = 0

    # Identity inconsistency (0-35 points)
    identity_risk = max(0, (100 - identity_score)) * 0.35
    score += identity_risk

    # Authentication failures (0-25 points)
    if spf_result == "FAIL":
        score += 8
    elif spf_result == "SOFTFAIL":
        score += 4

    if dkim_result == "FAIL":
        score += 8
    elif dkim_result == "NONE":
        score += 3

    if dmarc_result == "FAIL":
        score += 9
    elif dmarc_result == "NONE":
        score += 5

    # Reply-To mismatch (0-15 points)
    if has_reply_to_mismatch:
        score += 15

    # Typosquatting (0-10 points)
    if is_typosquat:
        score += 10

    # Domain age (0-8 points)
    if domain_age_days is not None:
        if domain_age_days < 7:
            score += 8
        elif domain_age_days < 30:
            score += 5
        elif domain_age_days < 90:
            score += 2

    # Threat feed hits (0-7 points)
    if threat_feeds > 0:
        score += min(threat_feeds * 2, 7)

    score = min(100, max(0, int(round(score))))

    if score >= 80:
        risk_level = "High Risk"
    elif score >= 50:
        risk_level = "Medium Risk"
    else:
        risk_level = "Low Risk"

    # Confidence calculations
    model_confidence = _calc_model_confidence(score, identity_score)
    evidence_confidence = _calc_evidence_confidence(
        spf_result, dkim_result, dmarc_result, has_reply_to_mismatch
    )

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "model_confidence": model_confidence,
        "evidence_confidence": evidence_confidence,
    }


def _calc_model_confidence(risk_score: int, identity_score: int) -> int:
    """Higher risk + lower identity consistency = higher model confidence."""
    base = 70
    if risk_score >= 80:
        base += 15
    elif risk_score >= 50:
        base += 8
    if identity_score < 50:
        base += 10
    elif identity_score < 70:
        base += 5
    return min(99, base)


def _calc_evidence_confidence(
    spf: str, dkim: str, dmarc: str, has_mismatch: bool
) -> int:
    """Evidence confidence based on deterministic observations."""
    base = 75
    if spf in ("PASS", "FAIL"):
        base += 5
    if dkim in ("PASS", "FAIL"):
        base += 5
    if dmarc in ("PASS", "FAIL"):
        base += 3
    if has_mismatch:
        base += 4
    return min(99, base)


def classify_threat_type(
    spf: str, dkim: str, dmarc: str,
    has_reply_to_mismatch: bool,
    is_typosquat: bool,
    body_content: str = "",
) -> str:
    """Classify the threat type based on indicators."""
    if has_reply_to_mismatch and is_typosquat:
        return "BEC"
    if is_typosquat:
        return "Credential Phishing"
    if dmarc == "FAIL" and has_reply_to_mismatch:
        return "Spoofing"
    if "invoice" in body_content.lower() or "payment" in body_content.lower():
        return "BEC"
    return "Spam"
