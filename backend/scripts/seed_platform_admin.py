"""Idempotently bootstrap the first platform/super-admin from environment variables.

Run manually (not on every container start):
    python -m scripts.seed_platform_admin
"""

import asyncio
import logging
import os
import sys

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.domains.platform_admin.repository import PlatformAdminRepository

logger = logging.getLogger(__name__)


async def seed_platform_admin() -> None:
    email = os.environ.get('PLATFORM_ADMIN_EMAIL')
    password = os.environ.get('PLATFORM_ADMIN_PASSWORD')
    if not email or not password:
        logger.error(
            'PLATFORM_ADMIN_EMAIL and PLATFORM_ADMIN_PASSWORD must both be set to seed the '
            'platform admin.'
        )
        sys.exit(1)

    normalized_email = email.strip().lower()

    async with AsyncSessionLocal() as session:
        repository = PlatformAdminRepository(session)
        existing = await repository.get_by_email(normalized_email)
        if existing is not None:
            logger.info('Platform admin %s already exists; skipping.', normalized_email)
            return

        await repository.create(email=normalized_email, hashed_password=hash_password(password))
        logger.info('Seeded platform admin %s.', normalized_email)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_platform_admin())


if __name__ == '__main__':
    main()
