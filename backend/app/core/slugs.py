import re

SLUG_REGEX = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

MAX_TAXONOMY_SLUG_LENGTH = 150

MIN_TENANT_SLUG_LENGTH = 2
MAX_TENANT_SLUG_LENGTH = 63  # DNS label limit

# Reserved so tenant subdomains can never collide with platform-level routes.
RESERVED_TENANT_SLUGS = frozenset(
    {
        'www',
        'api',
        'app',
        'admin',
        'platform',
        'mail',
        'static',
        'assets',
        'cdn',
        'ftp',
        'smtp',
        'ns1',
        'ns2',
        'root',
        'localhost',
    }
)


class InvalidSlugError(Exception):
    pass


def validate_slug_format(slug: str, *, max_length: int) -> None:
    if not slug or len(slug) > max_length or not SLUG_REGEX.match(slug):
        raise InvalidSlugError(
            f'Slug must be lowercase alphanumeric segments separated by single hyphens '
            f'(max {max_length} characters).'
        )


def validate_tenant_slug(slug: str) -> None:
    validate_slug_format(slug, max_length=MAX_TENANT_SLUG_LENGTH)
    if len(slug) < MIN_TENANT_SLUG_LENGTH:
        raise InvalidSlugError(f'Slug must be at least {MIN_TENANT_SLUG_LENGTH} characters.')
    if slug in RESERVED_TENANT_SLUGS:
        raise InvalidSlugError(f'"{slug}" is a reserved subdomain and cannot be used.')
