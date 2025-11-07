from langchain_core.documents import Document as LCDocument
from pydantic import BaseModel, Field


class DocumentChunkMetadata(BaseModel):
    """Metadata for a single chunk."""

    source: str
    doc_type: str
    doc_id: str
    chunk_id: int


class DocumentChunk(BaseModel):
    """A single chunk of a document."""

    text: str
    metadata: DocumentChunkMetadata

    @staticmethod
    def from_langchain_document(doc: LCDocument) -> "DocumentChunk":
        return DocumentChunk(
            text=doc.page_content,
            metadata=DocumentChunkMetadata.model_validate(doc.metadata),
        )


class IndexDocsRequest(BaseModel):
    """Request to index documents from file paths."""

    paths: list[str] = Field(description="List of file paths to index")


class IndexWebPagesRequest(BaseModel):
    """Request to index web pages from URLs."""

    urls: list[str] = Field(description="List of URLs to index")


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

    @staticmethod
    def from_langchain_documents(docs: list[LCDocument]) -> "SearchResult":
        chunks = [DocumentChunk.from_langchain_document(doc) for doc in docs]
        return SearchResult(chunks=chunks, total=len(chunks))


class IndexResult(BaseModel):
    """Result from indexing operation."""

    indexed_count: int = Field(description="Number of chunks indexed")
    doc_ids: list[str] = Field(description="Document IDs that were indexed")
    sources: list[str] = Field(description="Sources that were indexed")


class FetchChunksByRangeResult(BaseModel):
    """Result from fetching chunks by range."""

    chunks: list[DocumentChunk]
    doc_id: str
    total: int = Field(description="Total number of chunks returned")

    @staticmethod
    def from_langchain_documents(doc_id: str, docs: list[LCDocument]) -> "FetchChunksByRangeResult":
        chunks = [DocumentChunk.from_langchain_document(doc) for doc in docs]
        return FetchChunksByRangeResult(doc_id=doc_id, chunks=chunks, total=len(chunks))
