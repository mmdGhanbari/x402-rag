# X402 RAG SDK

Python SDK for X402 RAG API - a client library for interacting with the X402 RAG server.

## Installation

```bash
pip install x402-rag-sdk
```

or

```bash
poetry add x402-rag-sdk
```

## Usage

### Basic Setup

```python
from x402_rag_sdk import X402RagClient, ClientConfig

# Create a client configuration
config = ClientConfig(
    base_url="http://localhost:8000",
    x402_keypair_hex="YOUR_64_BYTE_KEYPAIR_HEX",  # Solana keypair for auth + payments
)

# Initialize the client
client = X402RagClient(config)
```

**Authentication**: All requests are authenticated using your Solana keypair. The SDK automatically signs each request with an Ed25519 signature, proving wallet ownership without exposing your private key.

### Using as Context Manager

```python
async with X402RagClient(config) as client:
    # Your operations here
    results = await client.search("machine learning")
```

### X402 Payment Integration

The SDK supports automatic handling of 402 Payment Required responses using Solana USDC payments. When configured, the client will automatically sign and retry requests that require payment.

```python
from x402_rag_sdk import X402RagClient, ClientConfig

# Configure the client with x402 payment settings
config = ClientConfig(
    base_url="http://localhost:8000",
    x402_keypair_hex="YOUR_64_BYTE_KEYPAIR_HEX",
)

client = X402RagClient(config)

# Now any request that returns 402 will be automatically handled
# The client will build and sign a payment transaction, then retry
result = await client.search("machine learning", k=5)
```

**How it works:**

1. When the server returns 402 Payment Required, the client parses the payment requirements
2. It builds a Solana transaction with the required USDC transfer
3. Signs the transaction with your private key
4. Retries the request with the signed transaction in the `X-PAYMENT` header
5. The server validates and submits the payment, then returns the requested data

**Security Note:** Keep your `x402_keypair_hex` secure and never commit it to version control.

### Index Documents

```python
# Index local documents
result = await client.index_docs([
    {"path": "/path/to/document1.pdf", "price_usd": 0.01},
    {"path": "/path/to/document2.txt", "price_usd": 0.005},
])

print(f"Indexed {len(result.indexed_documents)} documents")
for doc in result.indexed_documents:
    print(f"  - {doc.source}: {doc.chunks_count} chunks")
```

### Index Web Pages

```python
# Index web pages
result = await client.index_web_pages([
    {"url": "https://example.com/page1", "price_usd": 0.01},
    {"url": "https://example.com/page2", "price_usd": 0.01},
])

print(f"Indexed {len(result.indexed_documents)} web pages")
```

### Search Documents

```python
# Search for relevant documents
result = await client.search(
    query="What is machine learning?",
    k=5,  # number of results
    filters={"doc_type": "pdf"}  # optional metadata filters
)

print(f"Found {result.total} chunks")
for chunk in result.chunks:
    print(f"\n{chunk.text}")
    print(f"Source: {chunk.metadata.source}")
    print(f"Price: {chunk.metadata.price} USDC base units")
```

### Fetch Chunk Range

```python
# Fetch a specific range of chunks from a document
result = await client.get_chunk_range(
    doc_id="doc_12345",
    start_chunk=0,
    end_chunk=10,  # optional, fetches from start_chunk to end if not provided
)

print(f"Retrieved {result.total} chunks from document {result.doc_id}")
for chunk in result.chunks:
    print(f"Chunk {chunk.metadata.chunk_id}: {chunk.text[:100]}...")
```

### Complete Example

```python
import asyncio
from x402_rag_sdk import X402RagClient, ClientConfig

async def main():
    config = ClientConfig(
        base_url="http://localhost:8000",
        x402_keypair_hex="YOUR_64_BYTE_KEYPAIR_HEX",
    )
    async with X402RagClient(config) as client:
        # Index some documents
        index_result = await client.index_docs([
            {"path": "/path/to/research.pdf", "price_usd": 0.02},
        ])
        print(f"Indexed {len(index_result.indexed_documents)} documents")

        # Search the indexed documents
        search_result = await client.search(
            query="neural networks",
            k=3,
        )

        for chunk in search_result.chunks:
            print(f"\nFound in {chunk.metadata.source}:")
            print(chunk.text[:200])

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling

```python
from x402_rag_sdk import (
    X402RagClient,
    ClientConfig,
    X402RagHTTPError,
    X402RagConnectionError,
    X402RagTimeoutError,
)

async with X402RagClient(config) as client:
    try:
        result = await client.search("query")
    except X402RagHTTPError as e:
        print(f"HTTP Error {e.status_code}: {e.detail}")
    except X402RagConnectionError as e:
        print(f"Connection error: {e}")
    except X402RagTimeoutError as e:
        print(f"Request timed out: {e}")
```

## API Reference

### ClientConfig

- `base_url` (str): Base URL of the X402 RAG server
- `x402_keypair_hex` (str): 64-byte ed25519 keypair in hex format (for authentication and payments)
- `timeout` (int): Request timeout in seconds (default: 30)
- `x402_rpc_by_network` (dict, optional): RPC endpoints by network for x402 payments
- `x402_asset_decimals` (int, optional): Asset decimals for x402 payments (default: 6 for USDC)

### X402RagClient

#### Methods

- `index_docs(documents)`: Index local documents
- `index_web_pages(pages)`: Index web pages from URLs
- `search(query, k, filters)`: Search for similar documents
- `get_chunk_range(doc_id, start_chunk, end_chunk)`: Fetch a range of chunks

### Exceptions

- `X402RagError`: Base exception
- `X402RagHTTPError`: HTTP error with status code and detail
- `X402RagConnectionError`: Connection error
- `X402RagTimeoutError`: Request timeout

## Development

Install dependencies:

```bash
poetry install
```

Run linter:

```bash
poetry run ruff check .
```

Format code:

```bash
poetry run ruff format .
```

## License

TBD
