"""Basic usage example for X402 RAG SDK."""

import asyncio

from x402_rag_sdk import ClientConfig, X402RagClient


async def main():
    """Demonstrate basic usage of the X402 RAG SDK."""
    # Create client configuration
    config = ClientConfig(
        base_url="http://localhost:8000",
        timeout=30,
    )

    # Use the client as a context manager
    async with X402RagClient(config) as client:
        print("=== Indexing Documents ===")
        # Index some documents
        index_result = await client.index_docs(
            [
                {"path": "/path/to/document1.pdf", "price_usd": 0.01},
                {"path": "/path/to/document2.txt", "price_usd": 0.005},
            ]
        )

        print(f"Indexed {len(index_result.indexed_documents)} documents:")
        for doc in index_result.indexed_documents:
            print(f"  - {doc.source}: {doc.chunks_count} chunks (ID: {doc.doc_id})")

        print("\n=== Indexing Web Pages ===")
        # Index web pages
        web_result = await client.index_web_pages(
            [
                {"url": "https://example.com/page1", "price_usd": 0.01},
                {"url": "https://example.com/page2", "price_usd": 0.01},
            ]
        )

        print(f"Indexed {len(web_result.indexed_documents)} web pages:")
        for doc in web_result.indexed_documents:
            print(f"  - {doc.source}: {doc.chunks_count} chunks (ID: {doc.doc_id})")

        print("\n=== Searching Documents ===")
        # Search for documents
        search_result = await client.search(
            query="machine learning",
            k=5,
            filters=None,  # Optional: {"doc_type": "pdf"}
        )

        print(f"Found {search_result.total} chunks:")
        for i, chunk in enumerate(search_result.chunks, 1):
            print(f"\n--- Result {i} ---")
            print(f"Source: {chunk.metadata.source}")
            print(f"Doc ID: {chunk.metadata.doc_id}")
            print(f"Chunk ID: {chunk.metadata.chunk_id}")
            print(f"Price: {chunk.metadata.price} USDC base units")
            print(f"Text preview: {chunk.text[:200]}...")

        # Get a specific document ID from the first result
        if search_result.chunks:
            doc_id = search_result.chunks[0].metadata.doc_id

            print(f"\n=== Fetching Chunk Range for {doc_id} ===")
            # Fetch a range of chunks
            chunk_result = await client.get_chunk_range(
                doc_id=doc_id,
                start_chunk=0,
                end_chunk=5,
            )

            print(f"Retrieved {chunk_result.total} chunks:")
            for chunk in chunk_result.chunks:
                print(f"\n  Chunk {chunk.metadata.chunk_id}:")
                print(f"  {chunk.text[:150]}...")


if __name__ == "__main__":
    asyncio.run(main())
