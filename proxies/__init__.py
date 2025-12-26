def proxy_to_url(host: str, port: int, protocol: str = "http") -> str:
    """Convert proxy components to URL string."""
    return f"{protocol}://{host}:{port}"
