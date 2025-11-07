import logging

from fastapi import APIRouter, HTTPException

from x402_rag.services import DocIndexService, RetrievalService, WebIndexService
from x402_rag.services.schemas import (
    FetchChunksByRangeRequest,
    FetchChunksByRangeResult,
    IndexDocsRequest,
    IndexResult,
    IndexWebPagesRequest,
    SearchRequest,
    SearchResult,
)

from ..dependencies import ContainerDep

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["docs"],
)


@router.post("/docs/index")
async def index_docs(
    params: IndexDocsRequest,
    container: ContainerDep,
) -> IndexResult:
    """Index documents from file paths."""
    try:
        doc_index_service = await container.resolve(DocIndexService)
        return await doc_index_service.index_docs(params.paths)
    except Exception as e:
        logger.exception(f"Failed to index documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to index documents!") from None


@router.post("/docs/index/web")
async def index_web_pages(
    params: IndexWebPagesRequest,
    container: ContainerDep,
) -> IndexResult:
    """Index web pages from URLs."""
    try:
        web_index_service = await container.resolve(WebIndexService)
        return await web_index_service.index_web_pages(params.urls)
    except Exception as e:
        logger.exception(f"Failed to index web pages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to index web pages!") from None


@router.post("/docs/search")
async def search_docs(
    params: SearchRequest,
    container: ContainerDep,
) -> SearchResult:
    """Search for documents similar to the query text."""
    try:
        retrieval_service = await container.resolve(RetrievalService)
        return await retrieval_service.search(
            query=params.query,
            k=params.k,
            filters=params.filters,
        )
    except Exception as e:
        logger.exception(f"Failed to search documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search documents!") from None


@router.post("/docs/chunks")
async def get_chunk_range(
    params: FetchChunksByRangeRequest,
    container: ContainerDep,
) -> FetchChunksByRangeResult:
    """Fetch a range of chunks for a specific document."""
    try:
        retrieval_service = await container.resolve(RetrievalService)
        return await retrieval_service.get_chunk_range(
            doc_id=params.doc_id,
            start_chunk=params.start_chunk,
            end_chunk=params.end_chunk,
        )
    except Exception as e:
        logger.exception(f"Failed to fetch chunks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chunks!") from None
