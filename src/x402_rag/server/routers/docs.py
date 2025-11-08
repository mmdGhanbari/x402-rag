import logging

from fastapi import APIRouter, HTTPException, Request, Response

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
from ..x402 import X402PaymentHandler, X402PaymentRequired

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
    request: Request,
    response: Response,
    container: ContainerDep,
) -> SearchResult:
    """Search for documents similar to the query text.

    Requires payment based on number of chunks retrieved.
    """
    try:
        retrieval_service = await container.resolve(RetrievalService)
        payment_handler = await container.resolve(X402PaymentHandler)

        # First, retrieve the chunks
        result = await retrieval_service.search(
            query=params.query,
            k=params.k,
            filters=params.filters,
        )

        # Verify payment based on actual chunk count
        logger.debug(f"Searched and retrieved {result.total} chunks")

        description = f"Searching documents for query: {params.query[:50]}..."
        payment_ctx = await payment_handler.verify_payment(
            request=request,
            chunk_count=result.total,
            description=description,
        )

        # Settle payment after successful retrieval
        await payment_handler.settle_payment(payment_ctx, response)

        return result

    except X402PaymentRequired as e:
        # Return the 402 response with payment requirements
        return e.response
    except Exception as e:
        logger.exception(f"Failed to search documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search documents!") from None


@router.post("/docs/chunks")
async def get_chunk_range(
    params: FetchChunksByRangeRequest,
    request: Request,
    response: Response,
    container: ContainerDep,
) -> FetchChunksByRangeResult:
    """Fetch a range of chunks for a specific document.

    Requires payment based on number of chunks retrieved.
    """
    try:
        retrieval_service = await container.resolve(RetrievalService)
        payment_handler = await container.resolve(X402PaymentHandler)

        # First, retrieve the chunks
        result = await retrieval_service.get_chunk_range(
            doc_id=params.doc_id,
            start_chunk=params.start_chunk,
            end_chunk=params.end_chunk,
        )

        # Verify payment based on actual chunk count
        end_chunk = params.end_chunk or params.start_chunk
        logger.debug(f"Fetched {result.total} chunks for document {params.doc_id}")

        description = (
            f"Fetching chunks for document {params.doc_id} from chunk {params.start_chunk} to {end_chunk}"
        )
        payment_ctx = await payment_handler.verify_payment(
            request=request,
            chunk_count=result.total,
            description=description,
        )

        # Settle payment after successful retrieval
        await payment_handler.settle_payment(payment_ctx, response)

        return result

    except X402PaymentRequired as e:
        # Return the 402 response with payment requirements
        return e.response
    except Exception as e:
        logger.exception(f"Failed to fetch chunks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chunks!") from None
