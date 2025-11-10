# x402-rag-langchain

Plug-and-play **LangChain tools** for searching and retrieving content from any **X402-RAG compatible server**—with seamless, automatic crypto payments (x402 on Solana). Connect your agent to premium knowledge sources and let pay-as-you-go just work.

---

## Why this matters

- 🔎 **Semantic search** across paid or free corpora exposed by an X402-RAG server
- 📄 **Precise chunk retrieval** for downstream reasoning
- 💳 **Frictionless payments**: on `402 Payment Required`, the client signs an x402 payment (USDC on Solana by default) and retries—no extra payment code
- ⚡ **Agent-ready & async**: drop the tools into your LangChain stack

---

## Install

```bash
poetry add x402-rag-langchain
# or
pip install x402-rag-langchain
```

---

## Quickstart

```python
import asyncio
from x402_rag_langchain import make_x402_rag_tools, X402RagClient, ClientConfig

async def main():
    # Point at any X402-RAG compatible server
    client = X402RagClient(ClientConfig(
        base_url="http://localhost:8000",
        # If the server charges via x402, provide your Solana payer:
        x402_keypair_hex="YOUR_64_BYTE_KEYPAIR_HEX",
    ))

    search_tool, get_chunks_tool = make_x402_rag_tools(client)

    # 1) Search
    search_res = await search_tool.ainvoke({"query": "vector databases", "k": 3})
    print(search_res)

    # 2) Fetch chunks
    chunks_res = await get_chunks_tool.ainvoke(
        {"doc_id": "doc_123", "start_chunk": 0, "end_chunk": 2}
    )
    print(chunks_res)

asyncio.run(main())
```

**How payments feel:** if the server replies `402`, the client signs an x402 payment and retries automatically. Your code just gets results.

---

## Included tools

- **`x402_rag_search`**
  _Inputs_: `query: str`, `k: int = 5`, `filters?: dict[str, str]`
  _Returns_: `{"ok": True, "total": int, "chunks": [{text, metadata}, ...]}`

- **`x402_rag_get_chunks`**
  _Inputs_: `doc_id: str`, `start_chunk: int`, `end_chunk?: int`
  _Returns_: `{"ok": True, "doc_id": str, "total": int, "chunks": [...]}`

Both tools are **async**. Use `ainvoke` or an async-capable agent.

---

## Requirements

- Python `>=3.10,<4.0`
- Works with any server implementing the X402-RAG API and x402 payment flow (Solana)

---

## License

MIT
