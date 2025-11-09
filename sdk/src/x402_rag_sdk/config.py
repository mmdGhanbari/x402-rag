"""Configuration for the X402 RAG client."""


class ClientConfig:
    """Configuration for the X402 RAG client.

    Args:
        base_url: The base URL of the X402 RAG server (e.g., "http://localhost:8000")
        timeout: Request timeout in seconds (default: 30)
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
