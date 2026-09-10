"""Observable indicator extraction (IOCs).

Extracts only values actually observed in the email (headers, transit hops,
body). IOCs are never labelled malicious, suspicious, or attributed merely
because they were extracted.
"""
from __future__ import annotations

import re
import urllib.parse
from typing import Any

IP_RE = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
URL_RE = re.compile(r'(?:https?://|www\.)[^\s<>"\')\]]+', re.IGNORECASE)
EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')


def extract_iocs(parsed: dict[str, Any]) -> list[dict[str, str]]:
    """Return a deduplicated list of observable indicators.

    Each item is ``{"ioc_type", "value", "source"}``. ``ioc_type`` is one of
    ip / domain / url / email / message_id / hash.
    """
    found: dict[tuple[str, str], str] = {}

    def add(ioc_type: str, value: str, source: str) -> None:
        value = (value or "").strip().strip("<>")
        if not value:
            return
        key = (ioc_type, value.lower() if ioc_type != "url" else value)
        found[key] = source

    # Header-derived addresses and domains.
    for header_name, email_addr in (
        ("From header", parsed.get("from_email") or ""),
        ("To header", parsed.get("to_email") or ""),
        ("Reply-To header", parsed.get("reply_to") or ""),
        ("Return-Path header", parsed.get("return_path") or ""),
    ):
        if email_addr:
            add("email", email_addr, header_name)
    for header_name, domain in (
        ("From header", parsed.get("from_domain") or ""),
        ("Reply-To header", parsed.get("reply_to_domain") or ""),
        ("Return-Path header", parsed.get("return_path_domain") or ""),
    ):
        if domain:
            add("domain", domain, header_name)

    if parsed.get("message_id"):
        add("message_id", parsed["message_id"], "Message-ID header")

    # Transit hop source IPs.
    for hop in parsed.get("received_hops") or []:
        src_ip = hop.get("source_ip") or ""
        if src_ip:
            add("ip", src_ip, "Received header")

    body = parsed.get("body") or ""
    for match in URL_RE.finditer(body):
        url = match.group(0).rstrip(".,;:") if not match.group(0).startswith("www.") else "http://" + match.group(0).rstrip(".,;:")
        add("url", url, "body")
        host = urllib.parse.urlparse(url if "://" in url else "http://" + url).hostname
        if host:
            add("domain", host, "URL in body")
    for match in IP_RE.finditer(body):
        add("ip", match.group(0), "body")
    for match in EMAIL_RE.finditer(body):
        add("email", match.group(0), "body")

    return [{"ioc_type": t, "value": v, "source": s} for (t, v), s in found.items()]