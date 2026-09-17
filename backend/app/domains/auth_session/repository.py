import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth_session.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        token_hash: str,
        subject_type: str,
        subject_id: uuid.UUID,
        tenant_id: uuid.UUID | None,
        expires_at: datetime,
    ) -> RefreshToken:
        row = RefreshToken(
            token_hash=token_hash,
            subject_type=subject_type,
            subject_id=subject_id,
            tenant_id=tenant_id,
            expires_at=expires_at,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def revoke(self, row: RefreshToken, *, replaced_by_id: uuid.UUID | None = None) -> None:
        row.revoked_at = datetime.now(UTC)
        row.replaced_by_id = replaced_by_id
        await self._session.commit()

    async def revoke_all_for_subject(self, *, subject_type: str, subject_id: uuid.UUID) -> None:
        """Defensive mass-revocation - used when a rotated-out token gets
        replayed (see rotate_refresh_token), since that's a signal the whole
        chain may be compromised, not just the one reused token.
        """
        await self._session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.subject_type == subject_type,
                RefreshToken.subject_id == subject_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=func.now())
        )
        await self._session.commit()
