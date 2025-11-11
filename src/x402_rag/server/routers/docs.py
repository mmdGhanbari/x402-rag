import logging

from fastapi import APIRouter, HTTPException, Request, Response

from x402_rag.services import DocIndexService, PurchaseService, RetrievalService, WebIndexService
from x402_rag.services.schemas import (
    FetchChunksByRangeRequest,
    FetchChunksByRangeResult,
    IndexDocsRequest,
    IndexResult,
    IndexWebPagesRequest,
    SearchRequest,
    SearchResult,
)
from x402_rag.services.utils import stable_chunk_uuid

from ..dependencies import ContainerDep, UserAddressDep
from ..x402 import X402PaymentHandler, X402PaymentRequired

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["docs"],
)


@router.post("/docs/index")
async def index_docs(
    params: IndexDocsRequest,
    container: ContainerDep,
    user_address: UserAddressDep,
) -> IndexResult:
    """Index documents from file paths."""
    try:
        logger.debug(f"User {user_address} indexing documents")
        doc_index_service = await container.resolve(DocIndexService)
        return await doc_index_service.index_docs(params.documents)
    except Exception as e:
        logger.exception(f"Failed to index documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to index documents!") from None


@router.post("/docs/index/web")
async def index_web_pages(
    params: IndexWebPagesRequest,
    container: ContainerDep,
    user_address: UserAddressDep,
) -> IndexResult:
    """Index web pages from URLs."""
    try:
        logger.debug(f"User {user_address} indexing web pages")
        web_index_service = await container.resolve(WebIndexService)
        return await web_index_service.index_web_pages(params.pages)
    except Exception as e:
        logger.exception(f"Failed to index web pages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to index web pages!") from None


@router.post("/docs/search")
async def search_docs(
    params: SearchRequest,
    request: Request,
    response: Response,
    container: ContainerDep,
    user_address: UserAddressDep,
) -> SearchResult:
    """Search for documents similar to the query text.

    Requires payment based on number of chunks retrieved.
    """
    try:
        retrieval_service = await container.resolve(RetrievalService)
        payment_handler = await container.resolve(X402PaymentHandler)
        purchase_service = await container.resolve(PurchaseService)

        result = await retrieval_service.search(
            query=params.query,
            k=params.k,
            filters=params.filters,
        )

        if not result.chunks:
            return result

        # Filter out chunks that user has already paid for
        unpaid_chunks, paid_chunks = await purchase_service.filter_unpaid_chunks(
            user_address=user_address,
            chunks=result.chunks,
        )

        total_price = sum([chunk.metadata.price for chunk in unpaid_chunks])
        if total_price == 0:
            logger.info(
                f"All {len(unpaid_chunks)} chunks for document {params.doc_id} are already paid, skipping payment"
            )
            return result

        logger.debug(
            f"User {user_address} searched and retrieved {result.total} chunks "
            f"({len(unpaid_chunks)} unpaid, {len(paid_chunks)} already paid) "
            f"with total unpaid price: {total_price} USDC base units"
        )

        description = f"Searching documents for query: {params.query[:50]}..."
        payment_ctx = await payment_handler.verify_payment(
            request=request,
            total_price=total_price,
            description=description,
        )

        await payment_handler.settle_payment(payment_ctx, response)

        # Record the purchase for unpaid chunks
        unpaid_chunk_ids = [
            stable_chunk_uuid(chunk.metadata.doc_id, chunk.metadata.chunk_id) for chunk in unpaid_chunks
        ]
        await purchase_service.record_purchases(user_address, unpaid_chunk_ids)

        return result

    except X402PaymentRequired as e:
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
    user_address: UserAddressDep,
) -> FetchChunksByRangeResult:
    """Fetch a range of chunks for a specific document.

    Requires payment based on number of chunks retrieved.
    """
    try:
        retrieval_service = await container.resolve(RetrievalService)
        payment_handler = await container.resolve(X402PaymentHandler)
        purchase_service = await container.resolve(PurchaseService)

        result = await retrieval_service.get_chunk_range(
            doc_id=params.doc_id,
            start_chunk=params.start_chunk,
            end_chunk=params.end_chunk,
        )

        if not result.chunks:
            return result

        # Filter out chunks that user has already paid for
        unpaid_chunks, paid_chunks = await purchase_service.filter_unpaid_chunks(
            user_address=user_address,
            chunks=result.chunks,
        )

        total_price = sum([chunk.metadata.price for chunk in unpaid_chunks])
        if total_price == 0:
            logger.info(
                f"All {len(unpaid_chunks)} chunks for document {params.doc_id} are already paid, skipping payment"
            )
            return result

        end_chunk = params.end_chunk or params.start_chunk
        logger.debug(
            f"User {user_address} fetched {result.total} chunks for document {params.doc_id} "
            f"({len(unpaid_chunks)} unpaid, {len(paid_chunks)} already paid) "
            f"with total unpaid price: {total_price} USDC base units"
        )

        description = f"Fetching chunks for document {params.doc_id} from chunk {params.start_chunk} to {end_chunk}"
        payment_ctx = await payment_handler.verify_payment(
            request=request,
            total_price=total_price,
            description=description,
        )

        await payment_handler.settle_payment(payment_ctx, response)

        # Record the purchase for unpaid chunks
        unpaid_chunk_ids = [
            stable_chunk_uuid(chunk.metadata.doc_id, chunk.metadata.chunk_id) for chunk in unpaid_chunks
        ]
        await purchase_service.record_purchases(user_address, unpaid_chunk_ids)

        return result

    except X402PaymentRequired as e:
        return e.response
    except Exception as e:
        logger.exception(f"Failed to fetch chunks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chunks!") from None
