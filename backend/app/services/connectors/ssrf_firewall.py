import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, List, Optional
from app.core.errors import SsrfBlockedError

BLOCKED_HOSTNAMES = {
    "localhost", "0.0.0.0", "metadata.google.internal", "instance-data"
}

BLOCKED_SUFFIXES = (
    ".localhost", ".local", ".internal", ".lan", ".corp", ".home.arpa"
)


def validate_url_security(url: str, allowed_domains: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Production SSRF firewall.
    Verifies URL scheme, validates hostname, resolves DNS to detect DNS-rebinding attacks,
    and blocks loopback, private subnets (RFC 1918), link-local, cloud metadata, and multicast.
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or invalid"

    try:
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() not in ["http", "https"]:
            return False, f"Forbidden URL scheme '{parsed.scheme}'. Only http and https permitted."

        host = parsed.netloc.lower().split(":")[0].strip()
        if not host:
            return False, "URL host is missing"

        # Check explicitly blocked hostnames
        if host in BLOCKED_HOSTNAMES or host.endswith(BLOCKED_SUFFIXES):
            return False, f"Host '{host}' is forbidden under SSRF egress policy (internal/local host)"

        # Check if host itself is an IP address
        try:
            ip = ipaddress.ip_address(host)
            if _is_blocked_ip(ip):
                return False, f"Direct access to IP {host} is blocked (private/loopback/cloud-metadata)"
        except ValueError:
            # Host is a domain name; perform DNS resolution to protect against rebinding
            try:
                addr_info = socket.getaddrinfo(host, None)
                for item in addr_info:
                    resolved_ip_str = item[4][0]
                    resolved_ip = ipaddress.ip_address(resolved_ip_str)
                    if _is_blocked_ip(resolved_ip):
                        return False, f"Host '{host}' resolved to restricted IP {resolved_ip_str} (SSRF blocked)"
            except socket.gaierror:
                # DNS failure will be handled gracefully during fetch
                pass

        # Validate against domain allowlist if configured
        if allowed_domains and "*" not in allowed_domains:
            matched = False
            for allowed in allowed_domains:
                clean_allowed = allowed.lower().lstrip(".")
                if host == clean_allowed or host.endswith(f".{clean_allowed}"):
                    matched = True
                    break
            if not matched:
                return False, f"Host '{host}' is not in the connector's permitted domain whitelist"

        return True, ""
    except Exception as e:
        return False, f"URL security validation failed: {e}"


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    """Checks if an IPv4 or IPv6 address is private, loopback, link-local, or cloud metadata."""
    # Specific cloud metadata check (169.254.169.254)
    if str(ip) in ["169.254.169.254", "100.100.100.200"]:
        return True

    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_url_safe(url: str, allowed_domains: Optional[List[str]] = None) -> None:
    is_safe, reason = validate_url_security(url, allowed_domains)
    if not is_safe:
        raise SsrfBlockedError(message=f"SSRF Protection: {reason}")
