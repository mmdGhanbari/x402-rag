import asyncio
import logging

from x402_rag.core import RuntimeContext

from .base import BaseIndexService
from .loaders import parse_pdf_to_markdown
from .schemas import DocumentToIndex, IndexedDocument, IndexResult
from .utils import (
    build_text_splitter,
)

logger = logging.getLogger(__name__)


class DocIndexService(BaseIndexService):
    def __init__(self, runtime_context: RuntimeContext):
        super().__init__(
            doc_store=runtime_context.doc_store,
            text_splitter=build_text_splitter(runtime_context.settings),
            settings=runtime_context.settings,
        )

    async def index_docs(self, documents_to_index: list[DocumentToIndex]) -> IndexResult:
        """
        Index documents from file paths.
        """
        paths = [doc.path for doc in documents_to_index]
        md_list = await asyncio.gather(*[parse_pdf_to_markdown(p) for p in paths])

        logger.debug(f"Parsed {len(md_list)}/{len(paths)} documents")

        indexed_documents: list[IndexedDocument] = []
        for doc_to_index, markdown_text in zip(documents_to_index, md_list, strict=True):
            path = doc_to_index.path
            price_usd = doc_to_index.price_usd

            doc = await self.index_document(
                source=path,
                content=markdown_text,
                price_usd=price_usd,
                doc_type="pdf",
            )
            indexed_documents.append(doc)

            logger.debug(f"Indexed {doc.chunks_count} chunks for document {path} with price ${price_usd}")

        return IndexResult(
            indexed_documents=indexed_documents,
        )
