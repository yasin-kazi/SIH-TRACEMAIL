"""Parse .eml files and extract headers, body, and metadata."""
from __future__ import annotations
import email
import email.policy
import email.utils
import hashlib
import re
from email import message_from_bytes, message_from_string
from typing import Any


def parse_eml(raw_bytes: bytes) -> dict[str, Any]:
    """Parse a raw .eml byte string and return structured data."""
    msg = message_from_bytes(raw_bytes, policy=email.policy.default)

    from_header = msg.get("From", "")
    reply_to = msg.get("Reply-To", "")
    return_path = msg.get("Return-Path", "")
    to_header = msg.get("To", "")
    subject = msg.get("Subject", "")
    date_header = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")

    from_name, from_email_addr = _parse_address(from_header)
    reply_to_name, reply_to_email = _parse_address(reply_to)
    return_path_name, return_path_email = _parse_address(return_path)

    from_domain = _extract_domain(from_email_addr)
    reply_to_domain = _extract_domain(reply_to_email)
    return_path_domain = _extract_domain(return_path_email)

    received_lines = _get_all_headers(msg, "Received")
    auth_results = msg.get("Authentication-Results", "")
    x_mailer = msg.get("X-Mailer", "")

    spf_result = _extract_auth_result(auth_results, "spf")
    dkim_result = _extract_auth_result(auth_results, "dkim")
    dmarc_result = _extract_auth_result(auth_results, "dmarc")

    source_ip = _extract_source_ip(received_lines)

    body = _get_body(msg)

    sha256 = hashlib.sha256(raw_bytes).hexdigest()

    all_headers = []
    for key in [
        "From", "To", "Reply-To", "Subject", "Date", "Message-ID",
        "Return-Path", "Received", "Authentication-Results",
        "MIME-Version", "Content-Type", "X-Mailer", "ARC-Seal",
        "DKIM-Signature",
    ]:
        vals = msg.get_all(key, [])
        for v in vals:
            all_headers.append({"key": f"{key}:", "value": v})

    received_hops = _parse_received_hops(received_lines)
    mime_parts = _collect_mime_parts(msg)
    attachments = _collect_attachments(mime_parts)

    return {
        "from_name": from_name,
        "from_email": from_email_addr,
        "from_domain": from_domain,
        "reply_to": reply_to_email,
        "reply_to_domain": reply_to_domain,
        "return_path": return_path_email,
        "return_path_domain": return_path_domain,
        "to_email": _extract_email_addr(to_header),
        "subject": subject,
        "date": date_header,
        "message_id": message_id,
        "spf_result": spf_result,
        "dkim_result": dkim_result,
        "dmarc_result": dmarc_result,
        "source_ip": source_ip,
        "x_mailer": x_mailer,
        "auth_results": auth_results,
        "received_lines": received_lines,
        "received_hops": received_hops,
        "mime_parts": mime_parts,
        "attachments": attachments,
        "body": body,
        "sha256": sha256,
        "headers": all_headers,
        "all_raw_headers": _get_raw_header_block(raw_bytes),
    }


def _parse_address(raw: str) -> tuple[str, str]:
    """Return (name, email) from a header value like '"Name" <email>'."""
    if not raw:
        return ("", "")
    match = re.match(r'"?([^"<]*)"?\s*<([^>]+)>', raw.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    if "@" in raw:
        return ("", raw.strip().strip('"'))
    return (raw.strip(), "")


def _extract_email_addr(raw: str) -> str:
    match = re.search(r'<([^>]+)>', raw)
    if match:
        return match.group(1)
    if "@" in raw:
        return raw.strip().strip('"')
    return raw


def _extract_domain(addr: str) -> str:
    if "@" in addr:
        return addr.split("@")[-1].strip().lower()
    return ""


def _get_all_headers(msg: email.message.Message, key: str) -> list[str]:
    return msg.get_all(key, []) or []


def _get_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                parts.append(part.get_content())
            elif ct == "text/html" and not parts:
                parts.append(part.get_content())
        return "\n".join(parts)
    return msg.get_content() if msg.get_content() else ""


def _extract_auth_result(auth_header: str, mechanism: str) -> str:
    """Extract SPF/DKIM/DMARC result from Authentication-Results header."""
    if not auth_header:
        return "NONE"
    pattern = rf'{mechanism}=(\w+)'
    match = re.search(pattern, auth_header, re.IGNORECASE)
    if match:
        result = match.group(1).upper()
        if result in ("PASS", "PASS"):
            return "PASS"
        if result in ("FAIL",):
            return "FAIL"
        if result in ("SOFTFAIL", "SOFT_FAIL"):
            return "SOFTFAIL"
        if result in ("NONE",):
            return "NONE"
        return result
    return "NONE"


def _extract_source_ip(received_lines: list[str]) -> str:
    """Try to extract the originating IP from Received headers."""
    for line in received_lines:
        match = re.search(r'\[(\d+\.\d+\.\d+\.\d+)\]', line)
        if match:
            return match.group(1)
        match = re.search(r'from\s+\S+\s+\((?:[^)]*\s)?(\d+\.\d+\.\d+\.\d+)\)', line)
        if match:
            return match.group(1)
    return ""


def extract_received_hops_from_text(eml_text: str) -> list[dict[str, str]]:
    """Extract observed transit hops from the Received headers of stored EML text.

    Every returned hop is derived from the Received headers actually present in the
    EML. No hostnames, IPs, or organizations are invented; if the EML contains no
    Received headers, an empty list is returned rather than fabricating a path.
    """
    if not eml_text:
        return []
    try:
        msg = message_from_string(eml_text, policy=email.policy.default)
    except Exception:
        return []
    return _parse_received_hops(_get_all_headers(msg, "Received"))


def _parse_received_hops(received_lines: list[str]) -> list[dict[str, str]]:
    """Parse Received headers into transit hops.

    Every field is derived from the actual header text. ``ip`` keeps its legacy
    meaning (bracketed source IP, falling back to the ``by`` host). Additional
    fields (from_host, by_host, source_ip, protocol, timestamp, raw_header) are
    preserved so forensic records can persist them without fabrication.
    """
    hops = []
    for i, line in enumerate(reversed(received_lines)):
        details = _parse_received_hop(line, i, len(received_lines))
        hops.append(details)
    return hops


def _parse_received_hop(line: str, reversed_index: int, total: int) -> dict[str, str]:
    """Extract structured, evidence-derived fields from a single Received header."""
    ip_match = re.search(r'\[(\d+\.\d+\.\d+\.\d+)\]', line)
    ip = ip_match.group(1) if ip_match else ""

    from_match = re.search(r'from\s+(\S+)', line)
    from_host = from_match.group(1) if from_match else "unknown"

    by_match = re.search(r'by\s+(\S+)', line)
    by_host = by_match.group(1) if by_match else "unknown"

    protocol_match = re.search(r'\swith\s+([A-Za-z0-9]+)', line)
    protocol = protocol_match.group(1).upper() if protocol_match else ""

    timestamp = ""
    semicolon = line.find(";")
    if semicolon != -1:
        after = line[semicolon + 1:].strip()
        if after:
            try:
                parsed_dt = email.utils.parsedate_to_datetime(after)
                if parsed_dt:
                    timestamp = parsed_dt.isoformat()
            except (TypeError, ValueError, OverflowError):
                timestamp = ""

    hop_type = "source" if reversed_index == 0 else (
        "destination" if reversed_index == total - 1 else "relay"
    )
    label = "SOURCE" if hop_type == "source" else (
        "INBOX" if hop_type == "destination" else f"H{reversed_index + 1}"
    )
    return {
        "label": label,
        "ip": ip or by_host,
        "description": f"{from_host} → {by_host}",
        "hop_type": hop_type,
        "sequence": reversed_index + 1,
        "raw_header": line,
        "from_host": from_host,
        "by_host": by_host,
        "source_ip": ip,
        "protocol": protocol,
        "timestamp": timestamp,
    }


def _collect_mime_parts(msg: email.message.Message) -> list[dict[str, Any]]:
    """Collect normalized MIME part metadata without executing or decoding content.

    Payload bytes are transfer-decoded only to measure size and (for attachments)
    compute a SHA-256. Nothing is opened, rendered, or run.
    """
    parts: list[dict[str, Any]] = []
    seq = {"n": 0}

    def walk(node: email.message.Message, parent_index: int | None, depth: int) -> None:
        seq["n"] += 1
        index = seq["n"]
        disposition = (node.get_content_disposition() or "").strip()
        filename = (node.get_filename() or "").strip()
        content_type = node.get_content_type()
        payload = None
        try:
            payload = node.get_payload(decode=True)
        except Exception:
            payload = None
        size = len(payload) if payload else 0

        part = {
            "part_index": index,
            "parent_index": parent_index,
            "depth": depth,
            "content_type": content_type,
            "disposition": disposition,
            "filename": filename,
            "content_id": (node.get("Content-ID") or "").strip().strip("<>"),
            "size": size,
            "transfer_encoding": (node.get("Content-Transfer-Encoding") or "").strip(),
            "is_attachment": bool(filename) or disposition.lower() == "attachment",
            "sha256": "",
        }
        if part["is_attachment"] and payload:
            part["sha256"] = hashlib.sha256(payload).hexdigest()
        parts.append(part)

        if node.is_multipart():
            for sub in node.iter_parts():
                walk(sub, index, depth + 1)

    walk(msg, None, 0)
    return parts


def _collect_attachments(mime_parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract the attachment subset of collected MIME parts."""
    return [
        {
            "filename": p["filename"] or f"part-{p['part_index']}",
            "mime_type": p["content_type"],
            "disposition": p["disposition"],
            "content_id": p["content_id"],
            "size": p["size"],
            "sha256": p["sha256"],
        }
        for p in mime_parts if p["is_attachment"]
    ]


def _get_raw_header_block(raw_bytes: bytes) -> str:
    """Extract the raw header block from the eml bytes."""
    try:
        text = raw_bytes.decode("utf-8", errors="replace")
        if "\r\n\r\n" in text:
            return text.split("\r\n\r\n", 1)[0]
        if "\n\n" in text:
            return text.split("\n\n", 1)[0]
        return text[:4000]
    except Exception:
        return ""
