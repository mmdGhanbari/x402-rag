import logging

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.v2.async_vectorstore import AsyncPGVectorStore
from langchain_postgres.v2.engine import PGEngine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from x402_rag.db.schemas import Base

from .settings import Settings

logger = logging.getLogger(__name__)


class RuntimeContext:
    settings: Settings
    doc_store: AsyncPGVectorStore
    async_engine: AsyncEngine

    def __init__(self, settings: Settings, doc_store: AsyncPGVectorStore, async_engine: AsyncEngine):
        self.settings = settings
        self.doc_store = doc_store
        self.async_engine = async_engine

    @classmethod
    async def create(cls, settings: Settings) -> "RuntimeContext":
        async_engine = create_async_engine(settings.pg_conn)
        engine = PGEngine.from_engine(async_engine)
        embedding_service = create_embedding_service(settings)

        # Initialize chunk_purchases table
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        try:
            await engine.ainit_vectorstore_table(
                table_name="document_chunks",
                vector_size=settings.embedding_dimension,
                id_column="id",
                metadata_json_column="metadata",
            )
        except Exception:
            logger.info("Vector store tables already initialized")

        doc_store = await AsyncPGVectorStore.create(
            engine=engine,
            embedding_service=embedding_service,
            table_name="document_chunks",
            id_column="id",
            metadata_json_column="metadata",
        )

        return cls(settings, doc_store, async_engine)


class FakeEmbeddings(Embeddings):
    def __init__(self):
        self.dimension = 768

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self.dimension for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.0] * self.dimension


def create_embedding_service(settings: Settings) -> Embeddings:
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddings(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
        )
    elif settings.embedding_provider == "gemini":
        return GoogleGenerativeAIEmbeddings(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
        )
    elif settings.embedding_provider == "hf":  # huggingface
        return HuggingFaceEmbeddings(model_name=settings.hf_model)
    else:
        return FakeEmbeddings()
