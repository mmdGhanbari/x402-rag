from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.v2.async_vectorstore import AsyncPGVectorStore
from langchain_postgres.v2.engine import PGEngine

from .settings import Settings


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
    else:  # hf or huggingface
        return HuggingFaceEmbeddings(model_name=settings.hf_model)


class RuntimeContext:
    settings: Settings
    doc_store: AsyncPGVectorStore

    def __init__(self, settings: Settings, doc_store: AsyncPGVectorStore):
        self.settings = settings
        self.doc_store = doc_store

    @classmethod
    async def create(cls, settings: Settings) -> "RuntimeContext":
        engine = PGEngine.from_connection_string(settings.pg_conn)
        embedding_service = create_embedding_service(settings)

        # Initialize table if it doesn't exist
        await engine.ainit_vectorstore_table(
            table_name="document_chunks",
            vector_size=settings.embedding_dimension,
            id_column="id",
            metadata_json_column="metadata",
        )

        doc_store = await AsyncPGVectorStore.create(
            engine=engine,
            embedding_service=embedding_service,
            table_name="document_chunks",
            id_column="id",
            metadata_json_column="metadata",
        )

        return cls(settings, doc_store)
