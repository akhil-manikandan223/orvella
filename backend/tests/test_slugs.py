import pytest

from app.core.slugs import (
    MAX_TENANT_SLUG_LENGTH,
    RESERVED_TENANT_SLUGS,
    InvalidSlugError,
    validate_slug_format,
    validate_tenant_slug,
)


@pytest.mark.parametrize('slug', ['a', 'school', 'high-school', 'sai-hospital-2'])
def test_valid_slug_formats_accepted(slug: str) -> None:
    validate_slug_format(slug, max_length=150)


@pytest.mark.parametrize(
    'slug',
    ['High-School', 'high_school', '-highschool', 'highschool-', 'high--school', ''],
)
def test_invalid_slug_formats_rejected(slug: str) -> None:
    with pytest.raises(InvalidSlugError):
        validate_slug_format(slug, max_length=150)


@pytest.mark.parametrize('slug', sorted(RESERVED_TENANT_SLUGS))
def test_reserved_tenant_slugs_rejected(slug: str) -> None:
    with pytest.raises(InvalidSlugError):
        validate_tenant_slug(slug)


def test_tenant_slug_too_short_rejected() -> None:
    with pytest.raises(InvalidSlugError):
        validate_tenant_slug('a')


def test_tenant_slug_too_long_rejected() -> None:
    with pytest.raises(InvalidSlugError):
        validate_tenant_slug('a' * (MAX_TENANT_SLUG_LENGTH + 1))


def test_valid_tenant_slug_accepted() -> None:
    validate_tenant_slug('saihospital')
