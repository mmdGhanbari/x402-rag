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
        x402_keypair_hex="YOUR_64_BYTE_KEYPAIR_HEX",
    ))

    # Create tools with default names: 'search' and 'get_chunks'
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

- **`search`** (default name)
  _Inputs_: `query: str`, `k: int = 5`, `filters?: dict[str, str]`
  _Returns_: `{"ok": True, "total": int, "chunks": [{text, metadata}, ...]}`

- **`get_chunks`** (default name)
  _Inputs_: `doc_id: str`, `start_chunk: int`, `end_chunk?: int`
  _Returns_: `{"ok": True, "doc_id": str, "total": int, "chunks": [...]}`

Both tools are **async**. Use `ainvoke` or an async-capable agent.

---

## Customization

Customize tool names and descriptions to help agents distinguish between multiple tool sets or add domain-specific context:

```python
# Add prefix and context description
tools = make_x402_rag_tools(
    client=client,
    prefix="company_docs",
    context_description="Search through internal company documentation and policies.",
)
# Creates tools: 'company_docs_search' and 'company_docs_get_chunks'
# Each description starts with the context to guide the agent

# Full customization
tools = make_x402_rag_tools(
    client=client,
    prefix="kb",
    search_description="Find relevant articles from the knowledge base. Use for general queries.",
    get_chunks_description="Retrieve specific sections from knowledge base documents by ID.",
)
# Creates: 'kb_search' and 'kb_get_chunks' with fully custom descriptions
```

**Parameters:**

- `prefix`: Optional prefix for tool names (e.g., `"docs"` → `docs_search`, `docs_get_chunks`)
- `context_description`: Context prepended to default descriptions to help agents distinguish tool sets
- `search_description`: Override the entire search tool description
- `get_chunks_description`: Override the entire get_chunks tool description

**Use case:** When agents have access to multiple knowledge sources (e.g., company docs, technical specs, public wiki), prefix and context help them choose the right tool.

---

## Requirements

- Python `>=3.10,<4.0`
- Works with any server implementing the X402-RAG API and x402 payment flow (Solana)

---

## License

MIT
