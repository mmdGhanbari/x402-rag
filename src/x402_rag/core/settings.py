from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

EMBEDDING_DIMS = {
    # OpenAI
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    # Gemini
    "gemini-embedding-001": 768,
}

SupportedNetworks = Literal["solana-devnet", "solana"]


class X402Settings(BaseModel):
    enabled: bool = Field(default=True, description="Enable x402 payment requirement")
    pay_to_address: str = Field(default=..., description="Wallet address to receive payments")
    network: SupportedNetworks = Field(
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

    # Database
    pg_conn: str = Field(
        default="postgresql+asyncpg://x402_rag:x402_rag@localhost:5432/x402_rag", alias="PGVECTOR_CONNECTION"
    )

    # Embeddings
    embedding_provider: Literal["openai", "gemini", "hf", "fake"] = Field(
        default="openai",
        alias="EMBEDDING_PROVIDER",
        description="Possible values: openai, gemini, hf, fake",
    )
    openai_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBED_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    gemini_model: str = Field(default="gemini-embedding-001", alias="GEMINI_EMBED_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    hf_model: str = Field(default="sentence-transformers/all-mpnet-base-v2", alias="HF_EMBEDDING_MODEL")

    # Chunking
    chunk_size: int = Field(default=2000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=0, alias="CHUNK_OVERLAP")

    # Retrieval
    max_retrieved_chunks: int = Field(default=100, alias="MAX_RETRIEVED_CHUNKS")

    # X402 Payment
    x402: X402Settings

    # Web fallback
    use_playwright_fallback: bool = Field(default=True, alias="USE_PLAYWRIGHT_FALLBACK")
    min_text_len: int = Field(default=800, alias="MIN_TEXT_LEN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def embedding_dimension(self) -> int:
        model = (
            self.openai_model
            if self.embedding_provider == "openai"
            else self.gemini_model
            if self.embedding_provider == "gemini"
            else self.hf_model
        )
        return EMBEDDING_DIMS.get(model, 768)
