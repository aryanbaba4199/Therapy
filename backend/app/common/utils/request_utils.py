"""Request and HTTP utility functions."""

from fastapi import Request


def get_client_ip(request: Request, trusted_proxies: list[str] | None = None) -> str:
    """Extract client IP address safely, only trusting forwarding headers if behind a trusted proxy."""
    client_host = request.client.host if request.client else "127.0.0.1"

    if trusted_proxies and client_host in trusted_proxies:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

    return client_host
