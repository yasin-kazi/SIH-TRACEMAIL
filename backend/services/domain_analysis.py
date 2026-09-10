"""Domain and IP analysis services using DNS lookups."""
from __future__ import annotations
import socket
from typing import Any
import dns.resolver
import dns.rdatatype


def resolve_domain(domain: str) -> dict[str, Any]:
    """Resolve a domain to IP addresses via DNS A records."""
    if not domain:
        return {"ips": [], "error": "No domain provided"}

    try:
        answers = dns.resolver.resolve(domain, "A")
        ips = [str(rdata) for rdata in answers]
        return {"ips": ips, "error": None}
    except dns.resolver.NXDOMAIN:
        return {"ips": [], "error": f"Domain {domain} does not exist"}
    except dns.resolver.NoAnswer:
        return {"ips": [], "error": f"No A records for {domain}"}
    except Exception as e:
        return {"ips": [], "error": str(e)}


def reverse_dns(ip: str) -> dict[str, Any]:
    """Perform reverse DNS lookup on an IP address."""
    if not ip:
        return {"hostname": "", "error": "No IP provided"}

    try:
        hostname = socket.gethostbyaddr(ip)
        return {"hostname": hostname[0], "error": None}
    except socket.herror:
        return {"hostname": "", "error": f"No reverse DNS for {ip}"}
    except Exception as e:
        return {"hostname": "", "error": str(e)}


def get_mx_records(domain: str) -> list[dict[str, str]]:
    """Get MX records for a domain."""
    if not domain:
        return []
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return [{"priority": str(rdata.preference), "exchange": str(rdata.exchange).rstrip(".")}
                for rdata in answers]
    except Exception:
        return []


def get_ns_records(domain: str) -> list[str]:
    """Get nameserver records for a domain."""
    if not domain:
        return []
    try:
        answers = dns.resolver.resolve(domain, "NS")
        return [str(rdata).rstrip(".") for rdata in answers]
    except Exception:
        return []


def get_txt_records(domain: str) -> list[str]:
    """Get TXT records for a domain."""
    if not domain:
        return []
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        return ["".join(rdata.strings) if isinstance(rdata.strings, (list, tuple)) else str(rdata.strings)
                for rdata in answers]
    except Exception:
        return []


def get_asn_for_ip(ip: str) -> dict[str, Any]:
    """Get ASN information for an IP using DNS-based ASN lookup."""
    if not ip:
        return {"asn": "", "provider": "", "error": "No IP provided"}

    try:
        query = f"{ip}.origin.asn.cymru.com"
        answers = dns.resolver.resolve(query, "TXT")
        for rdata in answers:
            txt = "".join(rdata.strings) if isinstance(rdata.strings, (list, tuple)) else str(rdata.strings)
            parts = [p.strip() for p in txt.split("|")]
            if len(parts) >= 5:
                return {
                    "asn": f"AS{parts[0]}",
                    "provider": parts[4] if len(parts) > 4 else "",
                    "country": parts[1] if len(parts) > 1 else "",
                    "error": None,
                }
        return {"asn": "", "provider": "", "error": "No ASN data found"}
    except Exception as e:
        return {"asn": "", "provider": "", "error": str(e)}


def get_ip_geolocation(ip: str) -> dict[str, Any]:
    """Get geolocation data for an IP (uses free ip-api.com)."""
    if not ip:
        return {"lat": 0.0, "lon": 0.0, "location": "", "country": "", "error": "No IP provided"}

    try:
        import httpx
        resp = httpx.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,as", timeout=5.0)
        data = resp.json()
        if data.get("status") == "success":
            location_parts = [p for p in [data.get("city"), data.get("regionName"), data.get("country")] if p]
            return {
                "lat": data.get("lat", 0.0),
                "lon": data.get("lon", 0.0),
                "location": ", ".join(location_parts),
                "country": data.get("country", ""),
                "isp": data.get("isp", ""),
                "org": data.get("org", ""),
                "asn": data.get("as", ""),
                "error": None,
            }
        return {"lat": 0.0, "lon": 0.0, "location": "", "country": "", "error": "Geolocation lookup failed"}
    except Exception as e:
        return {"lat": 0.0, "lon": 0.0, "location": "", "country": "", "error": str(e)}


def analyze_domain_full(domain: str) -> dict[str, Any]:
    """Run comprehensive domain analysis."""
    dns_data = resolve_domain(domain)
    mx = get_mx_records(domain)
    ns = get_ns_records(domain)
    txt = get_txt_records(domain)

    ip_info = {}
    if dns_data["ips"]:
        ip_info = get_ip_geolocation(dns_data["ips"][0])
        asn_info = get_asn_for_ip(dns_data["ips"][0])
    else:
        asn_info = {"asn": "", "provider": ""}

    return {
        "domain": domain,
        "dns": dns_data,
        "mx_records": mx,
        "ns_records": ns,
        "txt_records": txt,
        "geolocation": ip_info,
        "asn": asn_info,
    }


def analyze_ip_full(ip: str) -> dict[str, Any]:
    """Run comprehensive IP analysis."""
    rdns = reverse_dns(ip)
    geo = get_ip_geolocation(ip)
    asn = get_asn_for_ip(ip)

    return {
        "ip": ip,
        "reverse_dns": rdns,
        "geolocation": geo,
        "asn": asn,
    }
