"""Identity contradiction analysis engine."""
from __future__ import annotations
import json
import re
from typing import Any


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance."""
    if not a or not b:
        return max(len(a), len(b))
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def _extract_domain(addr: str) -> str:
    if "@" in addr:
        return addr.split("@")[-1].strip().lower()
    return ""


def analyze_identity(
    display_name: str,
    from_email: str,
    from_domain: str,
    reply_to: str,
    return_path: str,
    dkim_domain: str,
    source_ip: str,
    source_asn: str,
    source_location: str,
    source_provider: str,
    known_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze identity consistency and find contradictions."""
    known = known_domains or []
    reply_to_domain = _extract_domain(reply_to)
    return_path_domain = _extract_domain(return_path)

    contradictions = []
    chain = []

    # Step 1: Display name
    chain.append({
        "step": 1,
        "label": "Display",
        "value": display_name,
        "status": _check_display_name(display_name, known),
        "status_type": _status_type_display(display_name, known),
        "subtitle": "RFC 5322 Friendly Name",
        "meta": _display_meta(display_name, known),
        "meta_type": _meta_type_display(display_name, known),
    })

    # Step 2: From domain
    distance = min((_levenshtein(from_domain, kd) for kd in known if kd), default=999)
    is_typosquat = 0 < distance <= 3
    chain.append({
        "step": 2,
        "label": "From Domain",
        "value": from_email,
        "status": "Typosquat" if is_typosquat else "Verified",
        "status_type": "error" if is_typosquat else "success",
        "subtitle": "Header Sender Address",
        "meta": f"Distance = {distance}" if is_typosquat else "Authenticated",
        "meta_type": "error" if is_typosquat else "success",
    })

    if is_typosquat:
        contradictions.append({
            "id": "c_typosquat",
            "title": "Lookalike Typosquatting Domain",
            "description": f"Domain {from_domain} has Levenshtein distance {distance} from known domain(s). This indicates potential typosquatting.",
            "severity": "High",
            "risk_level": "Medium",
            "tags": [f"Levenshtein Distance: {distance}", "Domain Spoofing"],
        })

    # Step 3: Reply-To mismatch
    if reply_to and reply_to_domain and reply_to_domain != from_domain:
        chain.append({
            "step": 3,
            "label": "Reply-To",
            "value": reply_to,
            "status": "Contradiction",
            "status_type": "error",
            "subtitle": "Exfiltration Mailbox",
            "meta": "Rogue Destination",
            "meta_type": "error",
        })
        contradictions.append({
            "id": "c_replyto",
            "title": "From vs. Reply-To Alignment",
            "description": f"Reply-To domain ({reply_to_domain}) differs from From domain ({from_domain}). Replies will be diverted to an external address.",
            "severity": "Critical",
            "risk_level": "High Risk",
            "tags": ["RFC 5322 Section 3.6.2 Violation", "Active Exfiltration Funnel"],
        })
    else:
        chain.append({
            "step": 3,
            "label": "Reply-To",
            "value": reply_to or "Not set",
            "status": "Aligned" if reply_to else "Missing",
            "status_type": "success" if reply_to else "warning",
            "subtitle": "Reply Destination",
            "meta": "Aligned" if reply_to else "N/A",
            "meta_type": "success" if reply_to else "neutral",
        })

    # Step 4: Envelope
    chain.append({
        "step": 4,
        "label": "Envelope",
        "value": return_path or "Not set",
        "status": "Relay",
        "status_type": "neutral",
        "subtitle": "RFC 5321 Envelope From",
        "meta": "External ESP" if return_path_domain and return_path_domain != from_domain else "Self-hosted",
        "meta_type": "neutral",
    })

    if return_path_domain and return_path_domain != from_domain and return_path:
        contradictions.append({
            "id": "c_return_path",
            "title": "Return-Path (Envelope) Alignment",
            "description": f"Return-Path domain ({return_path_domain}) differs from From domain ({from_domain}). This indicates use of third-party ESP.",
            "severity": "Informational",
            "risk_level": "Informational",
            "tags": ["ESP Tenant Isolation: Unverified", "Shared IP Range"],
        })

    # Step 5: Cryptography
    dkim_aligned = _extract_domain(dkim_domain) == from_domain if dkim_domain else False
    chain.append({
        "step": 5,
        "label": "Cryptography",
        "value": f"d={dkim_domain}" if dkim_domain else "None",
        "status": "DKIM Pass" if dkim_domain else "No DKIM",
        "status_type": "success" if dkim_domain else "neutral",
        "subtitle": "Third-Party Signature" if not dkim_aligned else "Aligned",
        "meta": "Unaligned" if dkim_domain and not dkim_aligned else "Aligned",
        "meta_type": "success" if dkim_domain else "neutral",
    })

    if dkim_domain and not dkim_aligned:
        contradictions.append({
            "id": "c_dkim",
            "title": "DKIM Cryptographic Integrity",
            "description": f"DKIM signature validates for {dkim_domain} but is unaligned with From domain ({from_domain}).",
            "severity": "Low",
            "risk_level": "Low Threat",
            "tags": ["Selector: s1024", "Unaligned Signature"],
        })

    # Step 6: Hop Zero
    chain.append({
        "step": 6,
        "label": "Hop Zero",
        "value": source_ip or "Unknown",
        "status": source_provider or "Unknown",
        "status_type": "neutral",
        "subtitle": f"{source_location} ({source_asn})" if source_asn else "Unknown",
        "meta": "Hosting Node",
        "meta_type": "neutral",
    })

    # Calculate identity score
    num_contradictions = len(contradictions)
    score = max(0, 100 - (num_contradictions * 18) - (5 if is_typosquat else 0))

    return {
        "score": score,
        "contradictions": contradictions,
        "chain": chain,
        "from_domain": from_domain,
        "reply_to_domain": reply_to_domain,
        "return_path_domain": return_path_domain,
    }


def _check_display_name(name: str, known_domains: list[str]) -> str:
    for kd in known_domains:
        base = kd.split(".")[0].lower()
        if base in name.lower():
            return "Impersonated"
    return "Verified"


def _status_type_display(name: str, known_domains: list[str]) -> str:
    return "warning" if _check_display_name(name, known_domains) == "Impersonated" else "success"


def _display_meta(name: str, known_domains: list[str]) -> str:
    for kd in known_domains:
        base = kd.split(".")[0].lower()
        if base in name.lower():
            return "Internal Brand Match"
    return "External"


def _meta_type_display(name: str, known_domains: list[str]) -> str:
    return "warning" if _check_display_name(name, known_domains) == "Impersonated" else "neutral"
