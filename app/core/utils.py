"""
Request extraction utilities for Flask views.
"""
from flask import request

def get_user_ip() -> str:
    """
    Extract the client's real IP address from request headers or remote address.
    Handles proxy headers (e.g. from Nginx, Cloudflare) safely.
    """
    if not request:
        return ""
    # Check X-Forwarded-For first
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # X-Forwarded-For can be a comma-separated list of IPs.
        # The first IP (leftmost) is the client IP.
        ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if ips:
            return ips[0]
            
    # Check X-Real-IP
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
        
    return request.remote_addr or ""


def get_user_agent() -> str:
    """
    Extract the User-Agent header from the current Flask request context.
    """
    if not request:
        return ""
    return request.headers.get("User-Agent", "")
