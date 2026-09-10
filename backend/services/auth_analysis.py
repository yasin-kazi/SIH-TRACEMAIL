"""SPF / DKIM / DMARC analysis using DNS lookups."""
from __future__ import annotations
import re
from typing import Any
import dns.resolver


def analyze_spf(domain: str) -> dict[str, Any]:
    """Look up SPF record and evaluate."""
    if not domain:
        return {"result": "NONE", "record": "", "explanation": "No domain provided"}

    try:
        answers = dns.resolver.resolve(domain, "TXT")
        for rdata in answers:
            txt = "".join(rdata.strings) if isinstance(rdata.strings, (list, tuple)) else str(rdata.strings)
            if txt.startswith("v=spf1"):
                has_include = "include:" in txt
                has_ip4 = "ip4:" in txt
                has_redirect = "redirect=" in txt
                return {
                    "result": "PASS",
                    "record": txt,
                    "explanation": f"SPF record found for {domain}",
                    "mechanisms": {
                        "include": has_include,
                        "ip4": has_ip4,
                        "redirect": has_redirect,
                    },
                }
        return {"result": "NONE", "record": "", "explanation": f"No SPF record found for {domain}"}
    except dns.resolver.NXDOMAIN:
        return {"result": "NONE", "record": "", "explanation": f"Domain {domain} does not exist"}
    except dns.resolver.NoAnswer:
        return {"result": "NONE", "record": "", "explanation": f"No TXT records for {domain}"}
    except Exception as e:
        return {"result": "NONE", "record": "", "explanation": f"DNS lookup failed: {str(e)}"}


def analyze_dkim(domain: str, selector: str = "default") -> dict[str, Any]:
    """Look up DKIM record for a given selector."""
    if not domain:
        return {"result": "NONE", "record": "", "explanation": "No domain provided"}

    query = f"{selector}._domainkey.{domain}"
    try:
        answers = dns.resolver.resolve(query, "TXT")
        for rdata in answers:
            txt = "".join(rdata.strings) if isinstance(rdata.strings, (list, tuple)) else str(rdata.strings)
            if "v=DKIM1" in txt or "k=rsa" in txt:
                return {
                    "result": "PASS",
                    "record": txt,
                    "explanation": f"DKIM record found for {selector}._domainkey.{domain}",
                    "selector": selector,
                }
        return {"result": "NONE", "record": "", "explanation": f"No DKIM record for selector {selector}"}
    except dns.resolver.NXDOMAIN:
        return {"result": "NONE", "record": "", "explanation": f"DKIM record not found: {query}"}
    except dns.resolver.NoAnswer:
        return {"result": "NONE", "record": "", "explanation": f"No DKIM TXT record for {query}"}
    except Exception as e:
        return {"result": "NONE", "record": "", "explanation": f"DNS lookup failed: {str(e)}"}


def analyze_dmarc(domain: str) -> dict[str, Any]:
    """Look up DMARC record and parse policy."""
    if not domain:
        return {"result": "NONE", "record": "", "explanation": "No domain provided"}

    query = f"_dmarc.{domain}"
    try:
        answers = dns.resolver.resolve(query, "TXT")
        for rdata in answers:
            txt = "".join(rdata.strings) if isinstance(rdata.strings, (list, tuple)) else str(rdata.strings)
            if txt.startswith("v=DMARC1"):
                policy_match = re.search(r'p=(\w+)', txt)
                sp_match = re.search(r'sp=(\w+)', txt)
                pct_match = re.search(r'pct=(\d+)', txt)
                rua_match = re.search(r'rua=([^;\s]+)', txt)
                return {
                    "result": "PASS",
                    "record": txt,
                    "explanation": f"DMARC record found for {domain}",
                    "policy": policy_match.group(1) if policy_match else "none",
                    "sub_policy": sp_match.group(1) if sp_match else "none",
                    "pct": int(pct_match.group(1)) if pct_match else 100,
                    "rua": rua_match.group(1) if rua_match else "",
                }
        return {"result": "NONE", "record": "", "explanation": f"No DMARC record for {domain}"}
    except dns.resolver.NXDOMAIN:
        return {"result": "NONE", "record": "", "explanation": f"DMARC record not found: {query}"}
    except dns.resolver.NoAnswer:
        return {"result": "NONE", "record": "", "explanation": f"No DMARC TXT record for {query}"}
    except Exception as e:
        return {"result": "NONE", "record": "", "explanation": f"DNS lookup failed: {str(e)}"}


def check_alignment(domain_a: str, domain_b: str, strict: bool = False) -> bool:
    """Check if two domains align (DMARC alignment)."""
    if strict:
        return domain_a.lower() == domain_b.lower()
    a_parts = domain_a.lower().split(".")
    b_parts = domain_b.lower().split(".")
    return a_parts[-2:] == b_parts[-2:] if len(a_parts) >= 2 and len(b_parts) >= 2 else domain_a.lower() == domain_b.lower()


def full_auth_analysis(
    from_domain: str,
    sender_ip: str,
    auth_results_header: str = "",
    dkim_domain: str = "",
) -> dict[str, Any]:
    """Run full SPF/DKIM/DMARC analysis."""
    spf = analyze_spf(from_domain)
    dkim = analyze_dkim(dkim_domain or from_domain)
    dmarc = analyze_dmarc(from_domain)

    spf_aligned = check_alignment(from_domain, from_domain)
    dkim_aligned = check_alignment(from_domain, dkim_domain) if dkim_domain else False
    dmarc_aligned = spf_aligned or dkim_aligned

    return {
        "spf": spf,
        "dkim": dkim,
        "dmarc": dmarc,
        "alignment": {
            "spf_aligned": spf_aligned,
            "dkim_aligned": dkim_aligned,
            "dmarc_aligned": dmarc_aligned,
        },
    }
