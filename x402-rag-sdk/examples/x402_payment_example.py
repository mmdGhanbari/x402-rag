"""Example of using X402RagClient with automatic payment handling.

This example demonstrates how to configure the client to automatically
handle 402 Payment Required responses using Solana USDC payments.
"""

import asyncio
import os

from x402_rag_sdk import ClientConfig, X402RagClient


async def main():
    """Example usage with x402 payment configuration."""

    # Configure the client with x402 payment settings
    config = ClientConfig(
        base_url="http://localhost:8000",
        timeout=30,
        # X402 Solana payment configuration
        x402_keypair_hex=os.environ.get("X402_KEYPAIR_HEX"),
    )

    # Create client - it will automatically handle 402 responses
    async with X402RagClient(config) as client:
        # Make requests normally - payment is handled automatically
        # If the server returns 402, the client will:
        # 1. Parse the payment requirements
        # 2. Build a signed Solana transaction
        # 3. Retry the request with the X-PAYMENT header

        # Search for documents
        result = await client.search("machine learning", k=5)
        print(f"Found {len(result.chunks)} chunks")
        for chunk in result.chunks:
            print(f"- {chunk.metadata.doc_id}: {chunk.text[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
