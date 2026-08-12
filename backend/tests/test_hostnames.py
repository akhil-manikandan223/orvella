import pytest

from app.core.hostnames import extract_subdomain_label

BASE_DOMAIN = 'orvella.com'


@pytest.mark.parametrize(
    ('host', 'expected'),
    [
        ('saihospital.orvella.com', 'saihospital'),
        ('saihospital.orvella.com:8000', 'saihospital'),
        ('SaiHospital.Orvella.Com', 'saihospital'),
        ('orvella.com', None),
        ('localhost', None),
        ('localhost:8000', None),
        ('example.com', None),
        ('foo.bar.orvella.com', None),
        (None, None),
        ('', None),
    ],
)
def test_extract_subdomain_label(host: str | None, expected: str | None) -> None:
    assert extract_subdomain_label(host, base_domain=BASE_DOMAIN) == expected
