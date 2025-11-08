from typing import Any

from x402_rag.core import RuntimeContext

from .schemas import FetchChunksByRangeResult, SearchResult
from .utils import stable_chunk_uuid


class RetrievalService:
    """Service for retrieving documents and chunks."""

    def __init__(self, runtime_context: RuntimeContext):
        self.runtime_context = runtime_context
        self.settings = runtime_context.settings
        self.doc_store = runtime_context.doc_store

    async def search(
        self,
        query: str,
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> SearchResult:
        """
        Search for documents similar to the query text.

        Args:
            query: The text to search for
            k: Number of results to return
            filters: Optional metadata filters (e.g., {"doc_id": "...", "source": "..."})

        Returns:
            QueryResult with matching chunks
        """
        # Clamp k to max_retrieved_chunks
        k = min(k, self.settings.max_retrieved_chunks)

        docs = await self.doc_store.asimilarity_search(
            query=query,
            k=k,
            filter=filters,
        )

        return SearchResult.from_langchain_documents(docs)

    async def get_chunk_range(
        self,
        doc_id: str,
        start_chunk: int,
        end_chunk: int | None = None,
    ) -> FetchChunksByRangeResult:
        """
        Fetch a range of chunks for a specific document.

        Args:
            doc_id: The document ID
            start_chunk: Starting chunk index (inclusive)
            end_chunk: Ending chunk index (inclusive, optional)

        Returns:
            ChunkRangeResult with the requested chunks
        """
        # If no end_chunk specified, fetch just the start chunk
        if end_chunk is None:
            end_chunk = start_chunk

        # Clamp the range to max_retrieved_chunks
        requested_count = end_chunk - start_chunk + 1
        if requested_count > self.settings.max_retrieved_chunks:
            end_chunk = start_chunk + self.settings.max_retrieved_chunks - 1

        # Generate stable UUIDs for the chunk range
        chunk_ids = [stable_chunk_uuid(doc_id, i) for i in range(start_chunk, end_chunk + 1)]

        # Fetch chunks by their IDs
        docs = await self.doc_store.aget_by_ids(ids=chunk_ids)

        return FetchChunksByRangeResult.from_langchain_documents(doc_id, docs)
