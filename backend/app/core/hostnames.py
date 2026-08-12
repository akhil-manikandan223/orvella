def extract_subdomain_label(host: str | None, *, base_domain: str) -> str | None:
    """Extract the single tenant subdomain label from a request Host header.

    Returns None for: missing/empty host, the bare base domain itself, hosts
    unrelated to base_domain, or ambiguous multi-label subdomains (e.g.
    "foo.bar.orvella.com") - these are treated as unsupported rather than
    guessed at.
    """
    if not host:
        return None

    hostname = host.split(':', 1)[0].strip().lower()
    normalized_base = base_domain.strip().lower()

    if hostname == normalized_base:
        return None

    suffix = f'.{normalized_base}'
    if not hostname.endswith(suffix):
        return None

    prefix = hostname[: -len(suffix)]
    if not prefix or '.' in prefix:
        return None

    return prefix
