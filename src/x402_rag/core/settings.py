from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

OPENAI_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

GEMINI_DIMS = {
    "models/embedding-001": 768,
    "models/text-embedding-004": 768,
}


class X402Settings(BaseModel):
    enabled: bool = Field(default=True, description="Enable x402 payment requirement")
    pay_to_address: str = Field(default=..., description="Wallet address to receive payments")
    network: Literal["solana-devnet", "solana"] = Field(
        default="solana-devnet",
        description="Solana network for payments, possible values: solana-devnet, solana",
    )
    usdc_address: str = Field(
        default="4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
        description="USDC asset address to use for payments",
    )
    usdc_decimals: int = Field(default=6, description="USDC asset decimals")
    fee_payer: str = Field(
        default="2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",
        description="Wallet address to pay fees",
    )
    facilitator_url: str = Field(
        default="https://facilitator.payai.network",
        description="URL of the x402 facilitator service",
    )


class Settings(BaseSettings):
    # Server
    server_host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    server_port: int = Field(default=8000, alias="SERVER_PORT")

    # Default log level for the whole application
    log_level: str = Field(default="warning", alias="LOG_LEVEL")
    # Log level for our own packages (x402_rag)
    app_log_level: str = Field(default="info", alias="APP_LOG_LEVEL")

    # DB / store
    pg_conn: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres", alias="PGVECTOR_CONNECTION"
    )

    # Embeddings
    embedding_provider: Literal["openai", "gemini", "hf"] = Field(
        default="openai",
        alias="EMBEDDING_PROVIDER",
        description="Possible values: openai, gemini, hf",
    )
    openai_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBED_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    gemini_model: str = Field(default="models/text-embedding-004", alias="GEMINI_EMBED_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    hf_model: str = Field(default="sentence-transformers/all-mpnet-base-v2", alias="HF_EMBEDDING_MODEL")

    # Chunking
    chunk_size: int = Field(default=1200, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")

    # Retrieval
    max_retrieved_chunks: int = Field(default=100, alias="MAX_RETRIEVED_CHUNKS")

    # X402 Payment
    x402: X402Settings = Field(default=X402Settings())

    # Web fallback
    use_playwright_fallback: bool = Field(default=True, alias="USE_PLAYWRIGHT_FALLBACK")
    min_text_len: int = Field(default=800, alias="MIN_TEXT_LEN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        extra="ignore",
    )

    @property
    def embedding_dimension(self) -> int:
        if self.embedding_provider == "openai":
            return OPENAI_DIMS.get(self.openai_model, 1536)
        elif self.embedding_provider == "gemini":
            return GEMINI_DIMS.get(self.gemini_model, 768)
        else:  # hf or huggingface
            return 768
