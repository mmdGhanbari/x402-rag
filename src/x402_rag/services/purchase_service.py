"""Service for managing chunk purchase tracking."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from x402_rag.core import RuntimeContext
from x402_rag.db.schemas import ChunkPurchase
from x402_rag.services.utils import stable_chunk_uuid

logger = logging.getLogger(__name__)


class PurchaseService:
    """Service for tracking chunk purchases."""

    def __init__(self, runtime_context: RuntimeContext):
        self.runtime_context = runtime_context
        self.async_engine = runtime_context.async_engine

    async def get_paid_chunk_ids(self, user_address: str, chunk_ids: list[str]) -> set[str]:
        if not chunk_ids:
            return set()

        async with AsyncSession(self.async_engine) as session:
            stmt = select(ChunkPurchase.chunk_id).where(
                ChunkPurchase.user_address == user_address,
                ChunkPurchase.chunk_id.in_(chunk_ids),
            )
            result = await session.execute(stmt)
            return {row[0] for row in result.fetchall()}

    async def record_purchases(self, user_address: str, chunk_ids: list[str]) -> None:
        if not chunk_ids:
            return

        if not self.runtime_context.settings.x402.enabled:
            return

        async with AsyncSession(self.async_engine) as session:
            # Use insert with on_conflict_do_nothing to avoid duplicate key errors
            for chunk_id in chunk_ids:
                purchase = ChunkPurchase(
                    user_address=user_address,
                    chunk_id=chunk_id,
                )
                session.add(purchase)

            await session.commit()
            logger.debug(f"Recorded {len(chunk_ids)} chunk purchases for user {user_address}")

    async def filter_unpaid_chunks(
        self,
        user_address: str,
        chunks: list,
    ) -> tuple[list, list]:
        if not chunks:
            return [], []

        # Extract chunk IDs from metadata
        chunk_ids = [stable_chunk_uuid(chunk.metadata.doc_id, chunk.metadata.chunk_id) for chunk in chunks]

        # Get paid chunk IDs
        paid_ids = await self.get_paid_chunk_ids(user_address, chunk_ids)

        # Split chunks into paid and unpaid
        unpaid_chunks = []
        paid_chunks = []

        for chunk, chunk_id in zip(chunks, chunk_ids, strict=True):
            if chunk_id in paid_ids:
                paid_chunks.append(chunk)
            else:
                unpaid_chunks.append(chunk)

        return unpaid_chunks, paid_chunks
