import asyncio

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from x402_rag.core.context import RuntimeContext

from .loaders import parse_pdf_to_markdown
from .schemas import DocumentChunkMetadata, IndexResult
from .utils import (
    build_doc_id_from_source,
    stable_chunk_uuid,
)


class DocIndexService:
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

    async def index_docs(self, paths: list[str]) -> IndexResult:
        """
        Index documents from file paths.
        """

        md_list = await asyncio.gather(*[parse_pdf_to_markdown(p) for p in paths])

        total_chunks = 0
        doc_ids = []
        sources = []

        for path, markdown_text in zip(paths, md_list, strict=True):
            doc_id = build_doc_id_from_source(path)

            chunks = self.text_splitter.split_text(markdown_text or "")
            if not chunks:
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

        return IndexResult(
            indexed_count=total_chunks,
            doc_ids=doc_ids,
            sources=sources,
        )
