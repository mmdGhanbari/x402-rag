import asyncio
import logging

from langchain_core.documents import Document

from x402_rag.core import RuntimeContext

from .loaders import parse_pdf_to_markdown
from .schemas import DocumentChunkMetadata, IndexResult
from .utils import (
    build_doc_id_from_source,
    build_text_splitter,
    stable_chunk_uuid,
)

logger = logging.getLogger(__name__)


class DocIndexService:
    def __init__(self, runtime_context: RuntimeContext):
        self.runtime_context = runtime_context
        self.settings = runtime_context.settings
        self.doc_store = runtime_context.doc_store
        self.text_splitter = build_text_splitter(self.settings)

    async def index_docs(self, paths: list[str]) -> IndexResult:
        """
        Index documents from file paths.
        """
        md_list = await asyncio.gather(*[parse_pdf_to_markdown(p) for p in paths])

        logger.debug(f"Parsed {len(md_list)}/{len(paths)} documents")

        total_chunks = 0
        doc_ids = []
        sources = []

        for path, markdown_text in zip(paths, md_list, strict=True):
            doc_id = build_doc_id_from_source(path)

            chunks = self.text_splitter.split_text(markdown_text or "")
            if not chunks:
                logger.warning(f"No chunks found for document {path}")
                continue

            documents = []
            chunk_ids = []

            for i, text in enumerate(chunks):
                chunk_id = stable_chunk_uuid(doc_id, i)
                metadata: DocumentChunkMetadata = {
                    "source": path,
                    "doc_type": "pdf",
                    "doc_id": doc_id,
                    "chunk_id": i,
                }
                documents.append(Document(page_content=text, metadata=metadata))
                chunk_ids.append(chunk_id)

            await self.doc_store.aadd_documents(documents=documents, ids=chunk_ids)

            total_chunks += len(documents)
            doc_ids.append(doc_id)
            sources.append(path)

            logger.debug(f"Indexed {len(documents)} chunks for document {path}")

        return IndexResult(
            indexed_count=total_chunks,
            doc_ids=doc_ids,
            sources=sources,
        )
