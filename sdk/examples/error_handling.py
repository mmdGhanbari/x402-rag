"""Example demonstrating error handling with X402 RAG SDK."""

import asyncio
import os

from x402_rag_sdk import (
    ClientConfig,
    X402RagClient,
    X402RagConnectionError,
    X402RagHTTPError,
    X402RagTimeoutError,
)


async def main():
    """Demonstrate error handling with the X402 RAG SDK."""
    config = ClientConfig(
        base_url="http://localhost:8000",
        timeout=5,  # Short timeout for demonstration
        x402_keypair_hex=os.environ.get("X402_KEYPAIR_HEX"),
    )

    async with X402RagClient(config) as client:
        # Example 1: Handle all errors generically
        print("=== Generic Error Handling ===")
        try:
            result = await client.search("test query")
            print(f"Success! Found {result.total} results")
        except Exception as e:
            print(f"An error occurred: {e}")

        # Example 2: Handle specific error types
        print("\n=== Specific Error Handling ===")
        try:
            result = await client.search("test query", k=10)
            print(f"Success! Found {result.total} results")
        except X402RagHTTPError as e:
            # HTTP errors (4xx, 5xx)
            print(f"HTTP Error {e.status_code}: {e.detail}")
            if e.status_code == 404:
                print("  -> Resource not found")
            elif e.status_code == 500:
                print("  -> Server error")
        except X402RagTimeoutError as e:
            # Timeout errors
            print(f"Request timed out: {e}")
            print("  -> Consider increasing timeout or checking network")
        except X402RagConnectionError as e:
            # Connection errors
            print(f"Connection error: {e}")
            print("  -> Check if server is running and accessible")

        # Example 3: Retry logic
        print("\n=== Retry Logic ===")
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                result = await client.search("test query")
                print(f"Success on attempt {attempt + 1}! Found {result.total} results")
                break
            except X402RagTimeoutError:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} timed out, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"Failed after {max_retries} attempts")
            except X402RagHTTPError as e:
                print(f"HTTP error, not retrying: {e}")
                break
            except X402RagConnectionError:
                if attempt < max_retries - 1:
                    print(f"Connection error on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"Connection failed after {max_retries} attempts")

        # Example 4: Handling errors during indexing
        print("\n=== Indexing with Error Handling ===")
        documents_to_index = [
            {"path": "/path/to/doc1.pdf", "price_usd": 0.01},
            {"path": "/path/to/doc2.txt", "price_usd": 0.005},
        ]

        try:
            result = await client.index_docs(documents_to_index)
            print(f"Successfully indexed {len(result.indexed_documents)} documents")
            for doc in result.indexed_documents:
                print(f"  - {doc.source}: {doc.chunks_count} chunks")
        except X402RagHTTPError as e:
            if e.status_code == 400:
                print(f"Invalid request: {e.detail}")
                print("  -> Check document paths and parameters")
            elif e.status_code == 500:
                print(f"Server error during indexing: {e.detail}")
                print("  -> Some documents may be corrupted or unsupported")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
