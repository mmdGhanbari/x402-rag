from __future__ import annotations

from pydantic import BaseModel, Field


class X402RagSearchArgs(BaseModel):
    """Arguments for the X402Rag search tool."""

    query: str = Field(..., description="Search query text")
    k: int = Field(5, ge=1, description="Number of results to return (default: 5)")
    filters: dict[str, str] | None = Field(default=None, description="Optional metadata filters to apply")


class X402RagGetChunksArgs(BaseModel):
    """Arguments for fetching a chunk range from a document."""

    doc_id: str = Field(..., description="Document ID to fetch from")
    start_chunk: int = Field(..., ge=0, description="Starting chunk index (inclusive)")
    end_chunk: int | None = Field(default=None, ge=0, description="Ending chunk index (inclusive, optional)")
