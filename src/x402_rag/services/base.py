import logging

from langchain_core.documents import Document
from langchain_postgres.v2.async_vectorstore import AsyncPGVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from x402_rag.core import Settings

from .schemas import DocumentChunkMetadata, IndexedDocument
from .utils import build_doc_id, stable_chunk_uuid

logger = logging.getLogger(__name__)


class BaseIndexService:
    def __init__(
        self,
        doc_store: AsyncPGVectorStore,
        text_splitter: RecursiveCharacterTextSplitter,
        settings: Settings,
    ):
        self.doc_store = doc_store
        self.text_splitter = text_splitter
        self.settings = settings

    async def index_document(self, source: str, content: str, price_usd: float, doc_type: str):
        doc_id = build_doc_id(source)

        chunks = self.text_splitter.split_text(content or "")
        if not chunks:
            logger.warning(f"No chunks found for document {source}")
            return

        total_chars = sum(len(chunk) for chunk in chunks)

        usdc_decimals = self.settings.x402.usdc_decimals
        # Convert USD price to USDC base units
        price_base_units = int(price_usd * (10**usdc_decimals))

        chunks: list[Document] = []
        chunk_ids: list[str] = []

        for i, text in enumerate(chunks):
            chunk_id = stable_chunk_uuid(doc_id, i)

            # Calculate chunk price based on character proportion
            chunk_chars = len(text)
            chunk_price = int((chunk_chars / total_chars) * price_base_units) if total_chars > 0 else 0

            metadata: DocumentChunkMetadata = {
                "source": source,
                "doc_type": doc_type,
                "doc_id": doc_id,
                "chunk_id": i,
                "price": chunk_price,
            }
            chunks.append(Document(page_content=text, metadata=metadata))
            chunk_ids.append(chunk_id)

        await self.doc_store.aadd_documents(documents=chunks, ids=chunk_ids)

        return IndexedDocument(
            doc_id=doc_id,
            source=source,
            chunks_count=len(chunks),
        )
