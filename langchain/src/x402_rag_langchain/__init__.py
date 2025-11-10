"""LangChain tools for the X402 RAG SDK.

These tools expect you to inject a pre-configured `X402RagClient` instance.
The client itself should be constructed with `ClientConfig`, which may include:
- x402_secret_key_hex
- x402_rpc_by_network
- x402_asset_decimals

Example:
    from x402_rag_langchain import make_x402_rag_tools, X402RagClient, ClientConfig

    client = X402RagClient(ClientConfig(
        base_url="http://localhost:8000",
        x402_secret_key_hex="...32-byte-hex...",
    ))

    tools = make_x402_rag_tools(client)
"""

from x402_rag_sdk import ClientConfig, X402RagClient

from .tools import (
    X402RagGetChunksArgs,
    X402RagGetChunksTool,
    X402RagSearchArgs,
    X402RagSearchTool,
    make_x402_rag_tools,
)

__all__ = [
    # Re-exports
    "X402RagClient",
    "ClientConfig",
    # Tools & args
    "X402RagSearchArgs",
    "X402RagGetChunksArgs",
    "X402RagSearchTool",
    "X402RagGetChunksTool",
    "make_x402_rag_tools",
]
