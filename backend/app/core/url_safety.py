"""
URL validation and SSRF protection.

SRS 2.8 / 2.11 requires rejecting javascript:, file:, localhost, private IP
ranges, and cloud metadata endpoints, while only allowing valid HTTP/HTTPS
URLs to be crawled.
"""
import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
}

# AWS/GCP/Azure metadata endpoint
CLOUD_METADATA_IP = "169.254.169.254"


class URLSafetyError(ValueError):
    """Raised when a URL fails validation or SSRF checks."""


def _is_private_or_reserved(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # can't parse -> treat as unsafe
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or str(ip) == CLOUD_METADATA_IP
    )


def validate_and_normalize_url(raw_url: str, resolve_dns: bool = True) -> str:
    """
    Validate a URL for crawling. Raises URLSafetyError on any violation.
    Returns a normalized URL (scheme+host lowercased, fragment stripped).
    """
    if not raw_url or not raw_url.strip():
        raise URLSafetyError("URL must not be empty")

    parsed = urlparse(raw_url.strip())

    if parsed.scheme.lower() not in ("http", "https"):
        raise URLSafetyError(f"Unsupported scheme: {parsed.scheme!r}. Only http/https allowed")

    if not parsed.hostname:
        raise URLSafetyError("URL must include a hostname")

    hostname = parsed.hostname.lower()

    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise URLSafetyError(f"Blocked hostname: {hostname}")

    # If hostname is already a literal IP, check it directly.
    try:
        ipaddress.ip_address(hostname)
        is_literal_ip = True
    except ValueError:
        is_literal_ip = False  # not a literal IP, fine

    if is_literal_ip and _is_private_or_reserved(hostname):
        raise URLSafetyError(f"Blocked private/reserved IP: {hostname}")

    if resolve_dns:
        try:
            resolved_ips = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
        except socket.gaierror:
            raise URLSafetyError(f"Could not resolve hostname: {hostname}")
        for ip in resolved_ips:
            if _is_private_or_reserved(ip):
                raise URLSafetyError(f"Hostname resolves to blocked IP range: {hostname} -> {ip}")

    # Normalize: lowercase scheme/host, strip fragment, drop default ports.
    netloc = hostname
    if parsed.port and not (
        (parsed.scheme == "http" and parsed.port == 80)
        or (parsed.scheme == "https" and parsed.port == 443)
    ):
        netloc = f"{hostname}:{parsed.port}"

    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme.lower()}://{netloc}{path}{query}"
