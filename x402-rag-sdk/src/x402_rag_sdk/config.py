"""Configuration for the X402 RAG client."""


class ClientConfig:
    """Configuration for the X402 RAG client.

    Args:
        base_url: The base URL of the X402 RAG server (e.g., "http://localhost:8000")
        timeout: Request timeout in seconds (default: 30)
        x402_keypair_hex: 64-byte keypair hex string for x402 payments (required if payments are enabled)
        x402_rpc_by_network: RPC endpoints by network for x402 payments (optional)
        x402_asset_decimals: Asset decimals for x402 payments (default: 6 for USDC)
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        x402_keypair_hex: str | None = None,
        x402_rpc_by_network: dict[str, str] | None = None,
        x402_asset_decimals: int | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.x402_keypair_hex = x402_keypair_hex
        self.x402_rpc_by_network = x402_rpc_by_network
        self.x402_asset_decimals = x402_asset_decimals
