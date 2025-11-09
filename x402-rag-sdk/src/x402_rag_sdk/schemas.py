"""Schemas for X402 RAG client requests and responses."""

from pydantic import BaseModel, Field


class DocumentChunkMetadata(BaseModel):
    """Metadata for a single chunk."""

    source: str
    doc_type: str
    doc_id: str
    chunk_id: int
    price: int = Field(description="Price for this chunk in USDC base units")


class DocumentChunk(BaseModel):
    """A single chunk of a document."""

    text: str
    metadata: DocumentChunkMetadata


class DocumentToIndex(BaseModel):
    """A document to be indexed with its price."""

    path: str = Field(description="File path to the document")
    price_usd: float = Field(ge=0, description="Price for this document in USD")


class WebPageToIndex(BaseModel):
    """A web page to be indexed with its price."""

    url: str = Field(description="URL of the web page")
    price_usd: float = Field(ge=0, description="Price for this web page in USD")


class IndexDocsRequest(BaseModel):
    """Request to index documents from file paths."""

    documents: list[DocumentToIndex] = Field(description="Documents to index with their prices")


class IndexWebPagesRequest(BaseModel):
    """Request to index web pages from URLs."""

    pages: list[WebPageToIndex] = Field(description="Web pages to index with their prices")


class SearchRequest(BaseModel):
    """Request to search for documents."""

    query: str = Field(description="Search query text")
    k: int = Field(default=5, ge=1, description="Number of results to return")
    filters: dict[str, str] | None = Field(default=None, description="Optional metadata filters")


class FetchChunksByRangeRequest(BaseModel):
    """Request to fetch a range of chunks for a specific document."""

    doc_id: str
    start_chunk: int = Field(ge=0, description="Starting chunk index (inclusive)")
    end_chunk: int | None = Field(default=None, ge=0, description="Ending chunk index (inclusive, optional)")


class SearchResult(BaseModel):
    """Result from a similarity search."""

    chunks: list[DocumentChunk]
    total: int = Field(description="Total number of chunks returned")


class IndexedDocument(BaseModel):
    """An indexed document."""

    doc_id: str
    source: str
    chunks_count: int


class IndexResult(BaseModel):
    """Result from indexing operation."""

    indexed_documents: list[IndexedDocument] = Field(description="Indexed documents")


class FetchChunksByRangeResult(BaseModel):
    """Result from fetching chunks by range."""

    chunks: list[DocumentChunk]
    doc_id: str
    total: int = Field(description="Total number of chunks returned")
