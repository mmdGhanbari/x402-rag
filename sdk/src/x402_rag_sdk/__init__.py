"""X402 RAG SDK - Client library for the X402 RAG server."""

from .client import X402RagClient
from .config import ClientConfig
from .exceptions import (
    X402RagConnectionError,
    X402RagError,
    X402RagHTTPError,
    X402RagTimeoutError,
)
from .schemas import (
    DocumentChunk,
    DocumentChunkMetadata,
    DocumentToIndex,
    FetchChunksByRangeRequest,
    FetchChunksByRangeResult,
    IndexDocsRequest,
    IndexedDocument,
    IndexResult,
    IndexWebPagesRequest,
    SearchRequest,
    SearchResult,
    WebPageToIndex,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "X402RagClient",
    "ClientConfig",
    # Schemas
    "DocumentChunk",
    "DocumentChunkMetadata",
    "DocumentToIndex",
    "FetchChunksByRangeRequest",
    "FetchChunksByRangeResult",
    "IndexDocsRequest",
    "IndexedDocument",
    "IndexResult",
    "IndexWebPagesRequest",
    "SearchRequest",
    "SearchResult",
    "WebPageToIndex",
    # Exceptions
    "X402RagError",
    "X402RagHTTPError",
    "X402RagConnectionError",
    "X402RagTimeoutError",
]
