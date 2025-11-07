import asyncio

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from x402_rag.core.context import RuntimeContext

from .loaders import load_url_auto
from .schemas import DocumentChunkMetadata, IndexResult
from .utils import (
    build_doc_id_from_source,
    stable_chunk_uuid,
)


class WebIndexService:
    def __init__(self, runtime_context: RuntimeContext):
        self.runtime_context = runtime_context
        self.settings = runtime_context.settings
        self.doc_store = runtime_context.doc_store
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    async def index_web_pages(self, urls: list[str]) -> IndexResult:
        """
        Index web pages from URLs.
        """

        batches = await asyncio.gather(*[load_url_auto(u, self.settings) for u in urls])

        total_chunks = 0
        doc_ids = []
        sources = []

        for url, docs in zip(urls, batches, strict=True):
            if not docs:
                continue

            full_text = "\n\n".join(
                [(d.page_content or "").strip() for d in docs if (d.page_content or "").strip()]
            )
            if not full_text:
                continue

            doc_id = build_doc_id_from_source(url)

            chunks = self.text_splitter.split_text(full_text)
            if not chunks:
                continue

            documents = []
            chunk_ids = []

            for i, text in enumerate(chunks):
                chunk_id = stable_chunk_uuid(doc_id, i)
                metadata: DocumentChunkMetadata = {
                    "source": url,
                    "doc_type": "web",
                    "doc_id": doc_id,
                    "chunk_id": i,
                }
                documents.append(Document(page_content=text, metadata=metadata))
                chunk_ids.append(chunk_id)

            await self.doc_store.aadd_documents(documents=documents, ids=chunk_ids)

            total_chunks += len(documents)
            doc_ids.append(doc_id)
            sources.append(url)

        return IndexResult(
            indexed_count=total_chunks,
            doc_ids=doc_ids,
            sources=sources,
        )
