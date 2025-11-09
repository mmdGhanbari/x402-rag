# x402-rag

Pay-as-you-go **Retrieval-Augmented Generation** with **x402 crypto payments** (USDC on Solana).
Index your data, expose it via a clean API, and let agents/apps **search & fetch chunks**. When access is paid, x402 handles the payment handshake automatically—your users just get results.

- 🔎 **Semantic search** across documents & web pages
- 📄 **Precise chunk retrieval** (by range)
- 💳 **Frictionless payments**: on `402 Payment Required`, the client signs an x402 payment and retries
- 💡 **Fair pricing**: users **pay only for the chunks they read**, not the whole document

---

## Repo layout

```
x402-rag/
├─ docker-compose.yml          # pgvector (database)
├─ .env / .env.default         # server configuration
├─ src/x402_rag/               # FastAPI service
├─ x402-rag-sdk/               # Python SDK (async)
└─ x402-rag-langchain/         # LangChain tools (search + get chunks)
```

---

## Run the server (local)

1. **Create `.env`** (override only what you need):

```bash
cp .env.default .env
```

Set these in `.env`:

```dotenv
# Embeddings (pick one provider)
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...

# x402 payments (Solana)
X402__ENABLED=True
X402__NETWORK=solana-devnet            # or: solana
X402__PAY_TO_ADDRESS=YOUR_MERCHANT_WALLET_PUBKEY
# Optional overrides if needed:
# X402__FACILITATOR_URL=...
# X402__USDC_ADDRESS=... (default USDC mint provided)
# X402__FEE_PAYER=...
```

2. **Start the database (pgvector):**

```bash
docker compose up -d
```

3. **Install & run the API:**

```bash
poetry install
poetry run python -m x402_rag.server.run
```

Server runs at `http://0.0.0.0:8000`.

---

## How pricing works (brief)

When you index a document or web page, you set a **total USD price** (e.g., `$0.01`).
During indexing, the text is split into chunks; each chunk’s price is proportional to its **character share** of the document:

```
chunk_price = total_price_in_USDC_base_units × (chunk_chars / total_chars)
```

At query time, the server sums the prices of the chunks it returns. If that sum > 0, it responds `402` with payment requirements. The client signs and retries. **Consumers pay only for the chunks they actually receive.**

---

## API overview

- `POST /docs/index` — index local files (priced per document)
- `POST /docs/index/web` — index web pages (priced per page)
- `POST /docs/search` — semantic search (pays per returned chunk)
- `POST /docs/chunks` — fetch chunk ranges (pays per chunk)

---

## Use from Python (SDK)

### Consumers (query & read)

```python
import asyncio
from x402_rag_sdk import X402RagClient, ClientConfig

async def main():
    config = ClientConfig(
        base_url="http://localhost:8000",
        # Required if your server enforces payments:
        x402_secret_key_hex="YOUR_32_BYTE_PRIVATE_KEY_HEX",
        x402_rpc_by_network={
            "solana": "https://api.mainnet-beta.solana.com",
            "solana-devnet": "https://api.devnet.solana.com",
        },
        x402_asset_decimals=6,  # USDC
    )

    async with X402RagClient(config) as client:
        # Semantic search (auto-pays on 402)
        result = await client.search("vector databases", k=3)
        print(result.total, "chunks")

        # Fetch chunks by range
        chunks = await client.get_chunk_range(doc_id="doc_123", start_chunk=0, end_chunk=2)
        print(chunks.doc_id, chunks.total)

asyncio.run(main())
```

### Resource owners (index your data)

```python
import asyncio
from x402_rag_sdk import ClientConfig, X402RagClient

async def main():
    config = ClientConfig(base_url="http://localhost:8000", timeout=30)

    async with X402RagClient(config) as client:
        # Documents on disk (absolute paths), with total USD price per doc
        docs = [
            {"path": "/abs/path/to/report.pdf", "price_usd": 0.01},
            {"path": "/abs/path/to/notes.txt",  "price_usd": 0.005},
        ]
        await client.index_docs(docs)

        # Public web pages, priced per page
        pages = [
            {"url": "https://example.com/guide", "price_usd": 0.01},
            {"url": "https://example.com/post",  "price_usd": 0.01},
        ]
        await client.index_web_pages(pages)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Use from LangChain (tools)

`x402-rag-langchain` provides two async tools: `x402_rag_search` and `x402_rag_get_chunks`.

```python
import asyncio
from x402_rag_langchain import X402RagClient, ClientConfig, make_x402_rag_tools

async def main():
    config = ClientConfig(
        base_url="http://localhost:8000",
        x402_secret_key_hex="YOUR_32_BYTE_PRIVATE_KEY_HEX",
        x402_rpc_by_network={"solana": "https://api.mainnet-beta.solana.com"},
        x402_asset_decimals=6,
    )

    client = X402RagClient(config)
    search_tool, get_chunks_tool = make_x402_rag_tools(client)

    res = await search_tool.ainvoke({"query": "RAG evals", "k": 5})
    print(res)

    res2 = await get_chunks_tool.ainvoke({"doc_id": "doc_123", "start_chunk": 0, "end_chunk": 2})
    print(res2)

    await client.close()

asyncio.run(main())
```

Both tools return LLM-friendly JSON (`ok/total/chunks/...`). If the server charges, payments are handled automatically via the client.

---

## Why x402-RAG?

- **Monetize access** at the **chunk** or **document** level
- **Zero UX friction**—payments are programmatic (no pop-ups)
- **Composable**: standard FastAPI + a tiny SDK + agent tools
- **Trust-minimized settlement** on Solana with server-side verification

---

## Minimal checklist

- ✅ Set `OPENAI_API_KEY` (or another embedding provider’s key)
- ✅ Set `X402__PAY_TO_ADDRESS` and choose `X402__NETWORK`
- ▶️ `docker compose up -d` (pgvector), then `poetry run python -m x402_rag.server.run`
- 🚀 Integrate via the SDK or LangChain tools

---

## License

MIT
