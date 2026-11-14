"""Web profiler for detecting WAF/CDN, security headers, and cookie flags."""

from dataclasses import dataclass
from typing import Any

from core.models import Finding


@dataclass
class ProfilerResult:
    """Result of web profiling."""
    findings: list[Finding]


# WAF/CDN detection patterns
WAF_CDN_HEADERS = {
    "cloudflare": [
        "cf-ray",
        "cf-cache-status",
        "cf-request-id",
        "__cfduid",
    ],
    "akamai": [
        "akamai-origin-hop",
        "akamai-x-cache",
        "akamai-x-get-cache-key",
    ],
    "sucuri": [
        "x-sucuri-id",
        "x-sucuri-cdn-cache",
        "x-sucuri-custom-block",
    ],
    "imperva": [
        "x-cdn",
        "x-iinfo",
        "x-request-id",
    ],
    "fastly": [
        "x-served-by",
        "x-cache",
        "x-cache-hits",
    ],
}

# Security headers to check
SECURITY_HEADERS = {
    "Strict-Transport-Security": "HSTS header missing - site may not enforce HTTPS",
    "Content-Security-Policy": "CSP header missing - site may be vulnerable to XSS",
    "X-Frame-Options": "X-Frame-Options header missing - site may be vulnerable to clickjacking",
    "X-Content-Type-Options": "X-Content-Type-Options missing - MIME sniffing possible",
    "Referrer-Policy": "Referrer-Policy missing - may leak referrer information",
    "Permissions-Policy": "Permissions-Policy missing - browser features not restricted",
}

# Cookie flags to check
COOKIE_FLAGS = {
    "Secure": "Cookie without Secure flag - can be transmitted over HTTP",
    "HttpOnly": "Cookie without HttpOnly flag - accessible to JavaScript",
    "SameSite": "Cookie without SameSite flag - vulnerable to CSRF",
}


def profile_web(url: str, response: Any) -> list[Finding]:
    """Profile a web response for security characteristics.

    Args:
        url: The URL that was requested
        response: The requests.Response object

    Returns:
        List of Finding objects representing security findings
    """
    findings: list[Finding] = []

    # Check for WAF/CDN headers
    headers_lower = {k.lower(): v for k, v in response.headers.items()}

    for cdn_name, header_names in WAF_CDN_HEADERS.items():
        for header in header_names:
            if header.lower() in headers_lower:
                findings.append(Finding(
                    type="waf_cdn",
                    severity="info",
                    url=url,
                    evidence=f"{cdn_name.title()} detected via {header} header",
                ))
                break  # Only add one finding per CDN

    # Check for missing security headers
    for header, evidence in SECURITY_HEADERS.items():
        if header.lower() not in headers_lower:
            findings.append(Finding(
                type="security_header",
                severity="low",
                url=url,
                evidence=evidence,
                detail={"header": header},
            ))

    # Check cookies for missing flags
    cookies = response.cookies
    for cookie in cookies:
        cookie_name = cookie.name
        for flag, evidence in COOKIE_FLAGS.items():
            # Check if flag is present
            flag_present = False
            if flag == "Secure":
                flag_present = cookie.secure
            elif flag == "HttpOnly":
                flag_present = cookie.has_nonstandard_attr("HttpOnly") or cookie.has_nonstandard_attr("httponly")
            elif flag == "SameSite":
                # SameSite can be Strict, Lax, or None
                samesite = getattr(cookie, "same_site", None)
                flag_present = samesite is not None and samesite.lower() != "none"

            if not flag_present:
                findings.append(Finding(
                    type="cookie_security",
                    severity="low",
                    url=url,
                    evidence=f"Cookie '{cookie_name}' {evidence.lower()}",
                    detail={"cookie": cookie_name, "flag": flag},
                ))

    return findings


def check_rate_limit(url: str, responses: list) -> list[Finding]:
    """Check for rate limiting based on responses.

    Args:
        url: The URL that was requested
        responses: List of (response_or_exception, was_timeout) tuples

    Returns:
        List of Finding objects
    """
    findings: list[Finding] = []

    # Check if last response was 429 or timeout
    if responses:
        last_response, was_timeout = responses[-1]
        if was_timeout:
            findings.append(Finding(
                type="rate_limit",
                severity="medium",
                url=url,
                evidence="Request timed out - possible rate limiting",
            ))
        elif hasattr(last_response, "status_code"):
            if last_response.status_code == 429:
                findings.append(Finding(
                    type="rate_limit",
                    severity="medium",
                    url=url,
                    evidence="Received 429 Too Many Requests - rate limiting detected",
                ))

    return findings