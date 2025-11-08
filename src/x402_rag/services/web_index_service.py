import asyncio
import logging

from x402_rag.core import RuntimeContext

from .base import BaseIndexService
from .loaders import load_url_auto
from .schemas import IndexedDocument, IndexResult, WebPageToIndex
from .utils import (
    build_text_splitter,
)

logger = logging.getLogger(__name__)


class WebIndexService(BaseIndexService):
    def __init__(self, runtime_context: RuntimeContext):
        super().__init__(
            doc_store=runtime_context.doc_store,
            text_splitter=build_text_splitter(runtime_context.settings),
            settings=runtime_context.settings,
        )

    async def index_web_pages(self, pages_to_index: list[WebPageToIndex]) -> IndexResult:
        """
        Index web pages from URLs.
        """
        urls = [page.url for page in pages_to_index]
        batches = await asyncio.gather(*[load_url_auto(u, self.settings) for u in urls])
        logger.debug(f"Loaded {len(batches)}/{len(urls)} web pages")

        indexed_documents: list[IndexedDocument] = []
        for page_to_index, docs in zip(pages_to_index, batches, strict=True):
            url = page_to_index.url
            page_price_usd = page_to_index.price_usd

            if not docs:
                logger.warning(f"No documents found for URL {url}")
                continue

            full_text = "\n\n".join(
                [(d.page_content or "").strip() for d in docs if (d.page_content or "").strip()]
            )
            if not full_text:
                logger.warning(f"No text found for URL {url}")
                continue

            doc = await self.index_document(
                source=url,
                content=full_text,
                price_usd=page_price_usd,
                doc_type="web",
            )
            indexed_documents.append(doc)

            logger.debug(f"Indexed {doc.chunks_count} chunks for URL {url} with price ${page_price_usd}")

        return IndexResult(
            indexed_documents=indexed_documents,
        )
